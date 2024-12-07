# chat_handler.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.live import Live  # Import Live for dynamic updates

from agent_handlers.human_handler import HumanHandler
from agent_handlers.llm_handler import LLMHandler
from agent_handlers.persona_handler import PersonaHandler
from transport.conversation_io import ConversationIO, ConversationEndedError

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
                 conversation_io: ConversationIO,
                 mode: str = "human", 
                 provider: str = "ollama", 
                 model: str = "llama3.3", 
                 persona: str = None,
                 stream: bool = False):
        self.conversation_io = conversation_io
        self.mode = mode
        self.provider = provider
        self.model = model
        self.stream = stream
        self.conversation = []

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
        self.conversation.append({"role": role.lower(), "content": content})

    async def run(self):
        console.print("[bold yellow]Starting our conversation...[/bold yellow]\n")
        await self.conversation_io.start_conversation()

        # Receive the initial question
        initial_prompt = await self.conversation_io.listen()
        role = initial_prompt.get("role", "Unknown")
        question = initial_prompt.get("message", "")

        # Display the question
        self.display_message(role, question)
        self.add_message(role, question)

        # check if streaming is enabled
        if self.stream and hasattr(self.responder_handler, "get_response_stream"):
            # Use a Live context to dynamically update the panel
            answer = ""
            style_name = role_styles.get("Responder", "unknown")

            # Create an empty panel to start
            text_content = Text("", style=style_name)
            panel = Panel(text_content, title="Responder", subtitle="", border_style=style_name, expand=True)

            # Use Live for dynamic updates
            with Live(panel, console=console, refresh_per_second=4, transient=True) as live:
                for token in self.responder_handler.get_response_stream(question, self.conversation):
                    answer += token
                    # Update the panel content with the accumulated answer
                    text_content = Text(answer, style=style_name)
                    updated_panel = Panel(text_content, title="Responder", subtitle="", border_style=style_name, expand=True)
                    live.update(updated_panel)

            # After streaming is done, print a final panel outside of Live
            self.add_message("Responder", answer)
            self.display_message("Responder", answer)
        else:
            # Non-streaming response
            answer = self.responder_handler.get_response(question, self.conversation)
            self.add_message("Responder", answer)
            self.display_message("Responder", answer)

        # Send the answer back to the server
        response_msg = {
            "role": "Responder",
            "message": answer
        }
        await self.conversation_io.respond(response_msg)

        # Listen for follow-up
        try:
            follow_up = await self.conversation_io.listen()
        except ConversationEndedError:
            console.print("[bold red]The conversation ended unexpectedly. No further messages received.[/bold red]")
            await self.conversation_io.end_conversation()
            console.print("[bold yellow]The conversation has concluded. Thank you.[/bold yellow]\n")
            return

        v_role = follow_up.get("role", "Unknown")
        v_msg = follow_up.get("message", "")
        self.display_message(v_role, v_msg)
        self.add_message(v_role, v_msg)

        # End conversation
        await self.conversation_io.end_conversation()
        console.print("[bold yellow]The conversation has concluded. Thank you.[/bold yellow]\n")
