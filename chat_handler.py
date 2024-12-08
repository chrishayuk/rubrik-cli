# chat_handler.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.live import Live
import asyncio

from agent_handlers.human_handler import HumanHandler
from agent_handlers.llm_handler import LLMHandler
from agent_handlers.persona_handler import PersonaHandler
from adapters.output.server_output_adapter import ServerOutputAdapter

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
        panel = Panel(
            text_content,
            title=title,
            border_style=style,
            expand=True
        )
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

        if self.server:
            await self.handle_server_input()
        else:
            user_input_task = asyncio.create_task(self.handle_user_input())
            tasks = [user_input_task]

            if hasattr(self.output_adapter, "read_message"):
                server_response_task = asyncio.create_task(self.handle_server_messages())
                tasks.append(server_response_task)

            await asyncio.gather(*tasks)

        await self._cleanup()
        self.print_panel("Chat", "The conversation has concluded. Thank you.", "system")

    async def handle_server_input(self):
        while True:
            try:
                user_msg = await self.input_adapter.read_message()
            except EOFError:
                break

            u_role = user_msg.get("role", "Unknown")
            u_content = user_msg.get("message", "")
            if u_content.strip().lower() == "exit":
                break

            self.display_message(u_role, u_content)
            self.add_message(u_role, u_content)

            answer = await self._get_response(u_content)
            self.add_message("responder", answer)

            if self.stream and hasattr(self.responder_handler, "get_response_stream"):
                # Streaming: only send partial=False with no message at end
                await self.output_adapter.write_message({
                    "role": "Responder",
                    "partial": False
                })
            else:
                # Non-streaming: send full answer once
                await self.output_adapter.write_message({
                    "role": "Responder",
                    "message": answer
                })
                self.display_message("responder", answer)


    async def handle_user_input(self):
        # Doesn't print prompt here, prompt is printed initially at startup and after server messages
        while True:
            try:
                user_msg = await self.input_adapter.read_message()
            except EOFError:
                break

            u_role = user_msg.get("role", "Unknown")
            u_content = user_msg.get("message", "")
            if u_content.strip().lower() == "exit":
                break

            self.display_message(u_role, u_content)
            self.add_message(u_role, u_content)
            await self.output_adapter.write_message(user_msg)

    async def handle_server_messages(self):
        streaming_answer = ""
        is_streaming = False
        live_instance = None
        display_role = None
        style_name = None

        while True:
            try:
                server_msg = await self.output_adapter.read_message()
            except EOFError:
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

                    # Start live with no transient so final panel stays
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
                    # End streaming. No final message in s_content, just end it
                    live_instance.__exit__(None, None, None)
                    live_instance = None
                    is_streaming = False
                    streaming_answer = ""
                    display_role = None
                    style_name = None

                    # Print newline and prompt after streaming ends
                    console.print()
                    await self.print_prompt(server_mode=False)
                else:
                    # Non-streaming message, just print once
                    if s_content:
                        self.display_message(s_role, s_content)
                    console.print()
                    await self.print_prompt(server_mode=False)

    async def _get_response(self, question: str) -> str:
        if self.stream and hasattr(self.responder_handler, "get_response_stream"):
            # Streaming mode: send only partial tokens
            answer = ""
            style_name = "assistant"
            display_role = self.local_name

            text_content = Text("", style=style_name)
            panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)

            with Live(panel, console=console, refresh_per_second=10) as live:
                for token in self.responder_handler.get_response_stream(question, self.conversation):
                    answer += token
                    text_content = Text(answer, style=style_name)
                    updated_panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
                    live.update(updated_panel)
                    live.refresh()

                    # Send token as partial
                    await self.output_adapter.write_message({
                        "role": "Responder",
                        "message": token,
                        "partial": True
                    })

            # Return full answer, but we do NOT send it here. handle_server_input() handles final partial=False.
            return answer
        else:
            # Non-streaming mode
            if asyncio.iscoroutinefunction(self.responder_handler.get_response):
                answer = await self.responder_handler.get_response(question, self.conversation)
            else:
                answer = self.responder_handler.get_response(question, self.conversation)
            return answer

    async def _cleanup(self):
        if hasattr(self.input_adapter, "stop"):
            await self.input_adapter.stop()
        if hasattr(self.output_adapter, "stop"):
            await self.output_adapter.stop()

    async def print_prompt(self, server_mode=False):
        # Print prompt without newline
        await asyncio.sleep(0.05)
        console.print(">:", end=" ", style="system")
