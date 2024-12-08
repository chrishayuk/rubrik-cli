# chat_handler.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.live import Live
import asyncio

# agent handlers
from adapters.output.server_output_adapter import ServerOutputAdapter
from agent_handlers.human_handler import HumanHandler
from agent_handlers.llm_handler import LLMHandler
from agent_handlers.persona_handler import PersonaHandler

custom_theme = Theme({
    "questioner": "bold magenta",
    "responder": "bold cyan",
    "verifier": "bold green",
    "unknown": "bold yellow"
})

console = Console(theme=custom_theme)
role_styles = {
    "Questioner": "questioner",
    "Responder": "responder",
    "Verifier": "verifier"
}

class ChatHandler:
    def __init__(self, 
                 input_adapter,
                 output_adapter,
                 mode: str = "human", 
                 provider: str = "ollama", 
                 model: str = "llama3.3", 
                 persona: str = None,
                 stream: bool = False):
        self.input_adapter = input_adapter
        self.output_adapter = output_adapter
        self.mode = mode
        self.provider = provider
        self.model = model
        self.stream = stream
        self.conversation = []

        # Choose responder handler
        if self.mode == "human":
            self.responder_handler = HumanHandler()
        elif self.mode == "llm":
            self.responder_handler = LLMHandler(provider=self.provider, model=self.model)
        elif self.mode == "persona":
            if not persona:
                raise ValueError("persona is required when mode is 'persona'")
            self.responder_handler = PersonaHandler(persona_name=persona, provider=self.provider, model=self.model)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def display_message(self, role: str, message: str):
        style_name = role_styles.get(role, "unknown")
        text_content = Text(message, style=style_name)
        panel = Panel(
            text_content,
            title=role,
            subtitle="",
            border_style=style_name,
            expand=True
        )
        console.print(panel)

    def add_message(self, role: str, content: str):
        # Add message to the conversation
        self.conversation.append({"role": role.lower(), "content": content})

    async def run(self):
        console.print("[bold yellow]Starting our conversation...[/bold yellow]\n")

        # Start input/output if needed
        if hasattr(self.input_adapter, "start"):
            await self.input_adapter.start()
        if hasattr(self.output_adapter, "start"):
            await self.output_adapter.start()

        # Always handle user input
        user_input_task = asyncio.create_task(self.handle_user_input())
        tasks = [user_input_task]

        # Only handle server messages if output_adapter supports read_message
        if hasattr(self.output_adapter, "read_message"):
            server_response_task = asyncio.create_task(self.handle_server_messages())
            tasks.append(server_response_task)

        await asyncio.gather(*tasks)

        await self._cleanup()
        console.print("[bold yellow]The conversation has concluded. Thank you.[/bold yellow]\n")



    async def handle_user_input(self):
        while True:
            try:
                user_msg = await self.input_adapter.read_message()
            except EOFError:
                break

            # user_msg is something like {"role": "Questioner", "message": "hi"}
            u_role = user_msg.get("role", "Unknown")
            u_content = user_msg.get("message", "")
            self.display_message(u_role, u_content)
            self.add_message(u_role, u_content)

            # Send user message to server
            await self.output_adapter.write_message(user_msg)

            # After sending user message, we can also optionally get a response locally from responder handler:
            answer = await self._get_response(u_content)
            self.add_message("Responder", answer)
            self.display_message("Responder", answer)

            # Send the responder's message out to the server (or other clients)
            response_msg = {"role": "Responder", "message": answer}
            await self.output_adapter.write_message(response_msg)

    async def handle_server_messages(self):
        # Continuously read server messages from the output_adapter (WebSocketDuplexAdapter)
        # and display them. This handles any messages from the server that are not the local user's
        # or the local responder's. If server echoes messages, they'll appear here.

        while True:
            try:
                server_msg = await self.output_adapter.read_message()  # from server
            except EOFError:
                break

            s_role = server_msg.get("role", "unknown")
            s_content = server_msg.get("message", "")
            self.display_message(s_role, s_content)
            self.add_message(s_role, s_content)

    async def _get_response(self, question: str) -> str:
        if self.stream and hasattr(self.responder_handler, "get_response_stream"):
            answer = ""
            style_name = role_styles.get("Responder", "unknown")

            text_content = Text("", style=style_name)
            panel = Panel(text_content, title="Responder", subtitle="", border_style=style_name, expand=True)

            with Live(panel, console=console, refresh_per_second=4, transient=True) as live:
                for token in self.responder_handler.get_response_stream(question, self.conversation):
                    answer += token
                    text_content = Text(answer, style=style_name)
                    updated_panel = Panel(text_content, title="Responder", subtitle="", border_style=style_name, expand=True)
                    live.update(updated_panel)
            return answer
        else:
            return self.responder_handler.get_response(question, self.conversation)

    async def _cleanup(self):
        # Stop input and output adapters if they have stop methods
        if hasattr(self.input_adapter, "stop"):
            await self.input_adapter.stop()
        if hasattr(self.output_adapter, "stop"):
            await self.output_adapter.stop()
