import asyncio
from rich.console import Console

console = Console()

class HumanHandler:
    async def get_response(self, question: str, conversation: list) -> str:
        loop = asyncio.get_running_loop()
        answer = await loop.run_in_executor(None, console.input, "[bold cyan]Your answer:[/bold cyan] ")
        return answer

