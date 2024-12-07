# chat_handler.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

from human_handler import HumanHandler
from llm_handler import LLMHandler
from persona_handler import PersonaHandler
from transport.conversation_io import ConversationIO  # Add this import

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
                 persona: str = None):
        self.conversation_io = conversation_io
        self.mode = mode
        self.provider = provider
        self.model = model
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

        # Wait for the first message from the other side
        initial_prompt = await self.conversation_io.listen()
        role = initial_prompt.get("role", "Unknown")
        question = initial_prompt.get("message", "")

        # Display the opening message and remember it
        self.display_message(role, question)
        self.add_message(role, question)

        # Use our chosen style (human, llm, or persona) to craft a response
        answer = self.responder_handler.get_response(question, self.conversation)

        # Add our reply and send it back to continue the exchange
        self.add_message("Responder", answer)
        response_msg = {
            "role": "Responder",
            "message": answer
        }
        await self.conversation_io.respond(response_msg)
        self.display_message("Responder", answer)

        # Wait to see how the other side reacts or evaluates our answer
        follow_up = await self.conversation_io.listen()
        v_role = follow_up.get("role", "Unknown")
        v_msg = follow_up.get("message", "")
        self.display_message(v_role, v_msg)
        self.add_message(v_role, v_msg)

        # Gently bring this conversation to a close
        await self.conversation_io.end_conversation()
        console.print("[bold yellow]The conversation has concluded. Thank you.[/bold yellow]\n")
