from rich.console import Console

# setup the console
console = Console()

class HumanHandler:
    def get_response(self, question: str, conversation: list) -> str:
        """
        Prompt the human user for an answer.
        `question` and `conversation` are provided for context if needed.
        """
        return console.input("[bold cyan]Your answer:[/bold cyan] ")
