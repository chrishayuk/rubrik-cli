# chat_handler/ui_renderer.py
from typing import Optional
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from ui_utils import role_to_display_name, print_prompt, display_message, console

class UIRenderer:
    def __init__(self):
        self.is_streaming = False
        self.streaming_answer = ""
        self.live_instance: Optional[Live] = None
        self.display_role: Optional[str] = None
        self.style_name: Optional[str] = None

    def start_streaming(self, server: bool, local_name: str, remote_name: str, role: str, initial_text: str):
        """Start displaying streamed content."""
        self.is_streaming = True
        self.streaming_answer = initial_text
        self.display_role, self.style_name = role_to_display_name(server, local_name, remote_name, role)

        text_content = Text(self.streaming_answer, style=self.style_name)
        panel = Panel(text_content, title=self.display_role, border_style=self.style_name, expand=True)
        self.live_instance = Live(panel, console=console, refresh_per_second=10)
        self.live_instance.__enter__()

    def update_streaming(self, new_text: str):
        """Update the ongoing streaming display."""
        if not self.is_streaming or not self.live_instance:
            return
        self.streaming_answer += new_text
        text_content = Text(self.streaming_answer, style=self.style_name)
        updated_panel = Panel(text_content, title=self.display_role, border_style=self.style_name, expand=True)
        self.live_instance.update(updated_panel)
        self.live_instance.refresh()

    def end_streaming(self):
        """End the streaming display."""
        if self.is_streaming and self.live_instance:
            self.live_instance.__exit__(None, None, None)
            self.live_instance = None
        self.is_streaming = False
        self.streaming_answer = ""
        self.display_role = None
        self.style_name = None
        console.print()

    def display_complete_message(self, server: bool, local_name: str, remote_name: str, role: str, content: str):
        """Display a complete (non-streaming) message."""
        if content:
            display_message(server, local_name, remote_name, role, content)
        console.print()

    async def after_message(self, server_mode: bool):
        """Perform any UI actions after a complete message is displayed, e.g., show prompt."""
        await print_prompt(server_mode=server_mode)
