# chat_handler.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.live import Live
import asyncio

# agent handlers
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
            await self.print_prompt(server_mode=True)

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

            # If not streaming, we print the final answer now:
            if not (self.stream and hasattr(self.responder_handler, "get_response_stream")):
                self.display_message("responder", answer)

            response_msg = {"role": "Responder", "message": answer}
            await self.output_adapter.write_message(response_msg)

    async def handle_user_input(self):
        while True:
            await self.print_prompt(server_mode=False)
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
        while True:
            try:
                server_msg = await self.output_adapter.read_message()
            except EOFError:
                break

            s_role = server_msg.get("role", "unknown")
            s_content = server_msg.get("message", "")
            self.display_message(s_role, s_content)
            self.add_message(s_role, s_content)
            await self.print_prompt(server_mode=False)

    async def _get_response(self, question: str) -> str:
        if self.stream and hasattr(self.responder_handler, "get_response_stream"):
            # Streaming mode
            answer = ""
            style_name = "assistant"
            display_role = self.local_name

            # Create initial text and panel
            text_content = Text("", style=style_name)
            panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)

            # Use Live to continuously update the panel as tokens arrive
            # Set a relatively high refresh rate and no transient so it stays visible
            with Live(panel, console=console, refresh_per_second=10) as live:
                for token in self.responder_handler.get_response_stream(question, self.conversation):
                    answer += token
                    # Update the text content with the appended token
                    text_content = Text(answer, style=style_name)
                    updated_panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
                    # Update the live display
                    live.update(updated_panel)
                    live.refresh()  # Force immediate refresh to show the new token

            # After streaming completes, 'answer' holds the full response,
            # and the final panel is already displayed with the full answer.
            return answer
        else:
            # Non-streaming mode
            if asyncio.iscoroutinefunction(self.responder_handler.get_response):
                return await self.responder_handler.get_response(question, self.conversation)
            else:
                return self.responder_handler.get_response(question, self.conversation)




    async def _cleanup(self):
        if hasattr(self.input_adapter, "stop"):
            await self.input_adapter.stop()
        if hasattr(self.output_adapter, "stop"):
            await self.output_adapter.stop()

    async def print_prompt(self, server_mode=False):
        await asyncio.sleep(0.05)
        console.print("\n>:", end=" ", style="system")
