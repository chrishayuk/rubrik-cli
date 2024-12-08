# adapters/output/human_output_adapter.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from adapters.output.output_adapter import OutputAdapter


# Define a custom theme for the Rich Console
custom_theme = Theme({
    "questioner": "bold magenta",
    "responder": "bold cyan",
    "verifier": "bold green",
    "unknown": "bold yellow"
})

# Define styles for different roles
role_styles = {
    "Questioner": "questioner",
    "Responder": "responder",
    "Verifier": "verifier"
}

# Create a Rich Console with the custom theme
console = Console(theme=custom_theme)

class HumanOutput(OutputAdapter):
    async def write_message(self, data: dict):
        # Extract role and message from data
        role = data.get("role", "Unknown")
        message = data.get("message", "")
        style_name = role_styles.get(role, "unknown")
        text_content = Text(message, style=style_name)

        # Create a Rich Panel with the styled content
        panel = Panel(
            text_content,
            title=role,
            subtitle="",
            border_style=style_name,
            expand=True
        )

        # Print the panel to the console
        console.print(panel)