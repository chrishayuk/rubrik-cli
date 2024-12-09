# ui_utils.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
import asyncio

# set the theme
custom_theme = Theme({
    "you": "bold magenta",
    "assistant": "bold cyan",
    "verifier": "bold green",
    "unknown": "bold yellow",
    "system": "bold blue"
})

# setup the console
console = Console(theme=custom_theme)


def print_panel(title: str, content: str, style: str = "unknown"):
    text_content = Text(content, style=style)
    panel = Panel(text_content, title=title, border_style=style, expand=True)
    console.print(panel)

def role_to_display_name(server: bool, local_name: str, remote_name: str, role: str) -> (str, str):
    r = role.lower()

    if server:
        if r == "questioner":
            display_role = remote_name
        elif r == "responder":
            display_role = local_name
        else:
            display_role = role.capitalize()
    else:
        if r == "questioner":
            display_role = local_name
        elif r == "responder":
            display_role = remote_name
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

def display_message(server: bool, local_name: str, remote_name: str, role: str, message: str):
    display_role, style_name = role_to_display_name(server, local_name, remote_name, role)
    print_panel(display_role, message, style=style_name)

def print_environment_info(server: bool, mode: str, persona: str, provider: str, model: str, input_adapter_name: str, output_adapter_name: str, local_name: str, remote_name: str):
    mode_type = "Server Mode" if server else "Client Mode"
    content_lines = [
        f"{mode_type}",
        f"Mode: {mode.upper()}",
    ]

    if persona:
        content_lines.append(f"Persona: {persona}")

    if mode != "human":
        content_lines.append(f"Provider: {provider} | Model: {model}")

    content_lines.append("")
    content_lines.append(f"Input Adapter: {input_adapter_name}")
    content_lines.append(f"Output Adapter: {output_adapter_name}")
    content_lines.append("")

    content_lines.append(f"Local Role: {local_name}")
    content_lines.append(f"Remote Role: {remote_name}")

    content_lines.append("")
    content_lines.append("Type 'exit' to quit.")

    info_str = "\n".join(content_lines)
    print_panel("Environment Info", info_str, "system")

async def print_prompt(server_mode=False):
    await asyncio.sleep(0.05)
    console.print(">:", end=" ", style="system")
