# my_ui_renderer.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

custom_theme = Theme({
    "questioner": "bold magenta",
    "responder": "bold cyan",
    "verifier": "bold green",
    "unknown": "bold yellow"
})

role_styles = {
    "Questioner": "questioner",
    "Responder": "responder",
    "Verifier": "verifier"
}

console = Console(theme=custom_theme)

def RichRenderer(data: dict):
    role = data.get("role", "Unknown")
    message = data.get("message", "")
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
