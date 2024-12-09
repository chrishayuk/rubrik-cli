import asyncio
import logging
from websockets.exceptions import ConnectionClosedError

from response_handlers.human_handler import HumanHandler
from response_handlers.llm_handler import LLMHandler
from response_handlers.persona_handler import PersonaHandler
from response_handlers.forwarder_handler import ForwarderHandler

from adapters.output.server_output_adapter import ServerOutputAdapter

from ui_utils import display_message, print_environment_info, print_prompt, console
from response_utils import get_response, safe_get_response

log = logging.getLogger(__name__)

class ChatHandler:
    def __init__(self, 
                 input_adapter,
                 output_adapter,
                 mode: str = "human", 
                 provider: str = "ollama", 
                 model: str = "llama3.3", 
                 persona: str = None,
                 stream: bool = False,
                 server: bool = False):
        self.input_adapter = input_adapter
        self.output_adapter = output_adapter
        self.mode = mode
        self.provider = provider
        self.model = model
        self.persona = persona
        self.stream = stream
        self.server = server
        self.conversation = []

        # Initialize the appropriate responder handler
        if self.mode == "human":
            self.responder_handler = HumanHandler()
            local_mode_desc = "Human"
        elif self.mode == "llm":
            self.responder_handler = LLMHandler(provider=self.provider, model=self.model)
            local_mode_desc = f"LLM ({self.provider}/{self.model})"
        elif self.mode == "persona":
            if not persona:
                raise ValueError("persona is required when mode=persona")
            self.responder_handler = PersonaHandler(persona_name=self.persona, provider=self.provider, model=self.model)
            local_mode_desc = f"Persona ({self.persona}, {self.provider}/{self.model})"
        elif self.mode == "forwarder":
            self.responder_handler = ForwarderHandler()
            local_mode_desc = "forwarder"
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        # Determine local and remote roles
        if self.server:
            self.local_name = f"Assistant ({local_mode_desc}, Server)"
            self.remote_name = "Questioner (Client)"
        else:
            self.local_name = f"You ({local_mode_desc}, Client)"
            self.remote_name = "Assistant (Server)"

    def add_message(self, role: str, content: str):
        self.conversation.append({"role": role.lower(), "content": content})

    async def run(self):
        # Print environment info at start
        print_environment_info(
            server=self.server,
            mode=self.mode,
            persona=self.persona,
            provider=self.provider,
            model=self.model,
            input_adapter_name=self.input_adapter.__class__.__name__,
            output_adapter_name=self.output_adapter.__class__.__name__,
            local_name=self.local_name,
            remote_name=self.remote_name
        )

        # Start adapters if they have start methods
        if hasattr(self.input_adapter, "start"):
            await self.input_adapter.start()
        if hasattr(self.output_adapter, "start"):
            await self.output_adapter.start()

        # If human client and not server, print initial prompt
        if self.mode == "human" and not self.server:
            console.print()
            await print_prompt(server_mode=False)

        try:
            if self.server:
                await self.handle_server_input()
            else:
                user_input_task = asyncio.create_task(self.handle_user_input())
                tasks = [user_input_task]

                if hasattr(self.output_adapter, "read_message"):
                    server_response_task = asyncio.create_task(self.handle_server_messages())
                    tasks.append(server_response_task)

                await asyncio.gather(*tasks)
        except (ConnectionClosedError, EOFError) as e:
            log.debug(f"Connection ended abruptly: {e}")
        finally:
            await self._cleanup()
            from ui_utils import print_panel
            print_panel("Chat", "The conversation has concluded. Thank you.", "system")

    async def handle_server_input(self):
        user_prompt_buffer = []
        prompt_in_progress = False

        while True:
            try:
                user_msg = await self.input_adapter.read_message()
            except (EOFError, ConnectionClosedError) as e:
                log.debug(f"Server input ended: {e}")
                break

            u_role = user_msg.get("role", "Unknown")
            chunk = user_msg.get("message", "")
            partial = user_msg.get("partial", False)

            if chunk.strip().lower() == "exit":
                break

            if partial:
                # Accumulate partial chunks
                if not prompt_in_progress:
                    prompt_in_progress = True
                    user_prompt_buffer.clear()

                user_prompt_buffer.append(chunk)
                current_input = "".join(user_prompt_buffer)
                display_message(self.server, self.local_name, self.remote_name, u_role, current_input)
            else:
                # Final chunk received
                if prompt_in_progress:
                    user_prompt_buffer.append(chunk)
                    full_prompt = "".join(user_prompt_buffer)
                    user_prompt_buffer.clear()
                    prompt_in_progress = False
                else:
                    full_prompt = chunk

                display_message(self.server, self.local_name, self.remote_name, u_role, full_prompt)
                self.add_message(u_role, full_prompt)

                # Call LLM once with full prompt
                answer = await safe_get_response(
                    lambda q: get_response(self.responder_handler, self.output_adapter, q, self.conversation, self.stream, self.local_name, console),
                    full_prompt
                )
                self.add_message("responder", answer)

                # Send final response
                try:
                    if self.stream and hasattr(self.responder_handler, "get_response_stream"):
                        await self.output_adapter.write_message({"role": "Responder", "partial": False})
                    else:
                        await self.output_adapter.write_message({"role": "Responder", "message": answer})
                        display_message(self.server, self.local_name, self.remote_name, "responder", answer)
                except (ConnectionClosedError, EOFError) as e:
                    log.debug(f"Failed to send responder message: {e}")
                    break

    async def handle_user_input(self):
        # For client mode, handle user input similarly
        while True:
            try:
                user_msg = await self.input_adapter.read_message()
            except (EOFError, ConnectionClosedError) as e:
                log.debug(f"User input ended: {e}")
                break

            u_role = user_msg.get("role", "Unknown")
            u_content = user_msg.get("message", "")
            if u_content.strip().lower() == "exit":
                break

            display_message(self.server, self.local_name, self.remote_name, u_role, u_content)
            self.add_message(u_role, u_content)
            try:
                await self.output_adapter.write_message(user_msg)
            except (ConnectionClosedError, EOFError) as e:
                log.debug(f"Failed to relay user message: {e}")
                break

    async def handle_server_messages(self):
        streaming_answer = ""
        is_streaming = False
        live_instance = None
        display_role = None
        style_name = None

        from ui_utils import role_to_display_name, print_prompt
        from rich.panel import Panel
        from rich.text import Text
        from rich.live import Live

        while True:
            try:
                server_msg = await self.output_adapter.read_message()
            except EOFError:
                # No more messages
                break
            except ConnectionClosedError as e:
                log.debug(f"Connection closed while reading server messages: {e}")
                break

            s_role = server_msg.get("role", "unknown")
            s_content = server_msg.get("message", "")
            partial = server_msg.get("partial", False)

            if partial:
                # Streaming tokens from server
                if not is_streaming:
                    is_streaming = True
                    streaming_answer = s_content
                    display_role, style_name = role_to_display_name(self.server, self.local_name, self.remote_name, s_role)

                    text_content = Text(streaming_answer, style=style_name)
                    panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
                    live_instance = Live(panel, console=console, refresh_per_second=10)
                    live_instance.__enter__()
                else:
                    # Append subsequent tokens
                    streaming_answer += s_content
                    text_content = Text(streaming_answer, style=style_name)
                    updated_panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
                    live_instance.update(updated_panel)
                    live_instance.refresh()
            else:
                # partial=False: streaming ended or normal message
                if is_streaming:
                    live_instance.__exit__(None, None, None)
                    live_instance = None
                    is_streaming = False
                    streaming_answer = ""
                    display_role = None
                    style_name = None

                    console.print()
                    await print_prompt(server_mode=False)
                else:
                    if s_content:
                        display_message(self.server, self.local_name, self.remote_name, s_role, s_content)
                    console.print()
                    await print_prompt(server_mode=False)

    async def _cleanup(self):
        try:
            if hasattr(self.input_adapter, "stop"):
                await self.input_adapter.stop()
        except Exception as e:
            log.debug(f"Error stopping input_adapter: {e}")

        try:
            if hasattr(self.output_adapter, "stop"):
                await self.output_adapter.stop()
        except Exception as e:
            log.debug(f"Error stopping output_adapter: {e}")
