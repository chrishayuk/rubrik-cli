import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.live import Live
from websockets.exceptions import ConnectionClosedError

from response_handlers.human_handler import HumanHandler
from response_handlers.llm_handler import LLMHandler
from response_handlers.persona_handler import PersonaHandler
from adapters.output.server_output_adapter import ServerOutputAdapter
from response_handlers.forwarder_handler import ForwarderHandler

import logging

log = logging.getLogger(__name__)

custom_theme = Theme({
    "you": "bold magenta",
    "assistant": "bold cyan",
    "verifier": "bold green",
    "unknown": "bold yellow",
    "system": "bold blue"
})

console = Console(theme=custom_theme)

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

        if self.server:
            self.local_name = f"Assistant ({local_mode_desc}, Server)"
            self.remote_name = "Questioner (Client)"
        else:
            self.local_name = f"You ({local_mode_desc}, Client)"
            self.remote_name = "Assistant (Server)"

    def print_panel(self, title: str, content: str, style: str = "unknown"):
        text_content = Text(content, style=style)
        panel = Panel(text_content, title=title, border_style=style, expand=True)
        console.print(panel)

    def add_message(self, role: str, content: str):
        self.conversation.append({"role": role.lower(), "content": content})

    def role_to_display_name(self, role: str) -> (str, str):
        r = role.lower()

        if self.server:
            if r == "questioner":
                display_role = self.remote_name
            elif r == "responder":
                display_role = self.local_name
            else:
                display_role = role.capitalize()
        else:
            if r == "questioner":
                display_role = self.local_name
            elif r == "responder":
                display_role = self.remote_name
            else:
                display_role = role.capitalize()

        lower_disp = display_role.lower()
        if "assistant" in lower_disp:
            style_name = "assistant"
        elif "you" in lower_disp or "human" in lower_disp:
            style_name = "you"
        else:
            style_name = "unknown"

        return display_role, style_name

    def display_message(self, role: str, message: str):
        display_role, style_name = self.role_to_display_name(role)
        self.print_panel(display_role, message, style=style_name)

    def print_environment_info(self):
        mode_type = "Server Mode" if self.server else "Client Mode"
        content_lines = [
            f"{mode_type}",
            f"Mode: {self.mode.upper()}",
        ]

        if self.persona:
            content_lines.append(f"Persona: {self.persona}")

        if self.mode != "human":
            content_lines.append(f"Provider: {self.provider} | Model: {self.model}")

        content_lines.append("")
        content_lines.append(f"Input Adapter: {self.input_adapter.__class__.__name__}")
        content_lines.append(f"Output Adapter: {self.output_adapter.__class__.__name__}")
        content_lines.append("")

        content_lines.append(f"Local Role: {self.local_name}")
        content_lines.append(f"Remote Role: {self.remote_name}")

        content_lines.append("")
        content_lines.append("Type 'exit' to quit.")

        info_str = "\n".join(content_lines)
        self.print_panel("Environment Info", info_str, "system")

    async def run(self):
        self.print_environment_info()

        if hasattr(self.input_adapter, "start"):
            await self.input_adapter.start()
        if hasattr(self.output_adapter, "start"):
            await self.output_adapter.start()

        # If human client mode, print initial prompt once at startup
        if self.mode == "human" and not self.server:
            console.print()
            await self.print_prompt(server_mode=False)

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
            self.print_panel("Chat", "The conversation has concluded. Thank you.", "system")

    async def handle_server_input(self):
        while True:
            try:
                user_msg = await self.input_adapter.read_message()
            except (EOFError, ConnectionClosedError) as e:
                log.debug(f"Server input ended: {e}")
                break

            u_role = user_msg.get("role", "Unknown")
            u_content = user_msg.get("message", "")
            if u_content.strip().lower() == "exit":
                break

            self.display_message(u_role, u_content)
            self.add_message(u_role, u_content)

            answer = await self._safe_get_response(u_content)
            self.add_message("responder", answer)

            try:
                if self.stream and hasattr(self.responder_handler, "get_response_stream"):
                    # Streaming: only send partial=False with no message at end
                    await self._safe_write_message({"role": "Responder", "partial": False})
                else:
                    # Non-streaming: send full answer once
                    await self._safe_write_message({"role": "Responder", "message": answer})
                    self.display_message("responder", answer)
            except (ConnectionClosedError, EOFError) as e:
                log.debug(f"Failed to send responder message: {e}")
                break

    async def handle_user_input(self):
        # Doesn't print prompt here, prompt is printed initially at startup and after server messages
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

            self.display_message(u_role, u_content)
            self.add_message(u_role, u_content)
            # Send message to output adapter
            try:
                await self._safe_write_message(user_msg)
            except (ConnectionClosedError, EOFError) as e:
                log.debug(f"Failed to relay user message: {e}")
                break

    async def handle_server_messages(self):
        streaming_answer = ""
        is_streaming = False
        live_instance = None
        display_role = None
        style_name = None

        while True:
            try:
                server_msg = await self.output_adapter.read_message()
            except (EOFError, ConnectionClosedError) as e:
                log.debug(f"Server messages ended: {e}")
                break

            s_role = server_msg.get("role", "unknown")
            s_content = server_msg.get("message", "")
            partial = server_msg.get("partial", False)

            if partial:
                if not is_streaming:
                    # Start streaming
                    is_streaming = True
                    streaming_answer = s_content
                    display_role, style_name = self.role_to_display_name(s_role)
                    text_content = Text(streaming_answer, style=style_name)
                    panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
                    live_instance = Live(panel, console=console, refresh_per_second=10)
                    live_instance.__enter__()
                else:
                    # Continue streaming
                    streaming_answer += s_content
                    text_content = Text(streaming_answer, style=style_name)
                    updated_panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
                    live_instance.update(updated_panel)
                    live_instance.refresh()
            else:
                # partial=False means streaming ended or normal message
                if is_streaming:
                    # End streaming
                    live_instance.__exit__(None, None, None)
                    live_instance = None
                    is_streaming = False
                    streaming_answer = ""
                    display_role = None
                    style_name = None

                    console.print()
                    await self.print_prompt(server_mode=False)
                else:
                    # Non-streaming message
                    if s_content:
                        self.display_message(s_role, s_content)
                    console.print()
                    await self.print_prompt(server_mode=False)

    async def _get_response(self, question: str) -> str:
        # Original _get_response logic
        if self.stream and hasattr(self.responder_handler, "get_response_stream"):
            answer = ""
            style_name = "assistant"
            display_role = self.local_name

            text_content = Text("", style=style_name)
            panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)

            with Live(panel, console=console, refresh_per_second=10) as live:
                async for token in self._async_token_generator(question):
                    answer += token
                    text_content = Text(answer, style=style_name)
                    updated_panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
                    live.update(updated_panel)
                    live.refresh()

                    # Send token as partial
                    try:
                        await self._safe_write_message({
                            "role": "Responder",
                            "message": token,
                            "partial": True
                        })
                    except (ConnectionClosedError, EOFError) as e:
                        log.debug(f"Failed streaming token: {e}")
                        break

            return answer
        else:
            # Non-streaming mode
            if asyncio.iscoroutinefunction(self.responder_handler.get_response):
                return await self.responder_handler.get_response(question, self.conversation)
            else:
                return self.responder_handler.get_response(question, self.conversation)

    async def _async_token_generator(self, question):
        # If your get_response_stream is async, iterate async, else sync
        # This is pseudo-code depending on how get_response_stream is implemented
        stream_gen = self.responder_handler.get_response_stream(question, self.conversation)
        if hasattr(stream_gen, '__aiter__'):
            async for token in stream_gen:
                yield token
        else:
            for token in stream_gen:
                yield token
                await asyncio.sleep(0)  # Allow event loop to run

    async def _safe_get_response(self, question: str) -> str:
        # Wrap _get_response in a try/except to handle abrupt closures
        try:
            return await self._get_response(question)
        except (ConnectionClosedError, EOFError) as e:
            log.debug(f"Failed to get response: {e}")
            return ""

    async def _safe_write_message(self, data: dict):
        # Attempts to write a message safely
        try:
            await self.output_adapter.write_message(data)
        except (ConnectionClosedError, EOFError) as e:
            log.debug(f"Failed to write message: {e}")
            raise

    async def _cleanup(self):
        # Attempt clean shutdown
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

    async def print_prompt(self, server_mode=False):
        # Print prompt without newline
        await asyncio.sleep(0.05)
        console.print(">:", end=" ", style="system")
