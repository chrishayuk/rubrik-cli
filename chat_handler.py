import json
import websockets
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# Import handlers
from human_handler import HumanHandler
from llm_handler import LLMHandler

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
    def __init__(self, mode: str = "human", provider: str = "openai", model: str = "gpt-4o-mini"):
        self.mode = mode
        self.provider = provider
        self.model = model
        self.conversation = []

        # Instantiate the appropriate handler based on mode
        if self.mode == "human":
            self.responder_handler = HumanHandler()
        else:
            self.responder_handler = LLMHandler(provider=self.provider, model=self.model)

    def display_message(self, role: str, message: str):
        """Display a message in a styled panel."""
        style_name = role_styles.get(role, "unknown")
        text_content = Text(message, style=style_name)
        panel = Panel(
            text_content,
            title=role,
            subtitle="via WebSocket",
            border_style=style_name,
            expand=True
        )
        console.print(panel)

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation.append({"role": role.lower(), "content": content})

    async def run(self):
        uri = "ws://localhost:8000/ws"
        console.print("[bold yellow]Connecting to the server...[/bold yellow]\n")
        async with websockets.connect(uri) as websocket:
            # 1. Receive the question (Questioner)
            question_msg = await websocket.recv()
            data = json.loads(question_msg)
            role = data.get("role", "Unknown")
            q_msg = data.get("message", "")

            # Display and store the question
            self.display_message(role, q_msg)
            self.add_message(role, q_msg)

            # 2. Get the response using the appropriate handler
            answer = self.responder_handler.get_response(q_msg, self.conversation)

            # Add responder message and send back to server
            self.add_message("Responder", answer)
            responder_msg = {
                "role": "Responder",
                "message": answer
            }
            await websocket.send(json.dumps(responder_msg))
            self.display_message("Responder", answer)

            # 3. Wait for verification message
            verifier_data = await websocket.recv()
            verifier_data = json.loads(verifier_data)
            v_role = verifier_data.get("role", "Unknown")
            v_msg = verifier_data.get("message", "")
            self.display_message(v_role, v_msg)
            self.add_message(v_role, v_msg)
