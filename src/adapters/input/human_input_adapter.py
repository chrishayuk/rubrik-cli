# adapters/input/human_input_adapter.py
import asyncio
import logging
from adapters.input.input_adapter import InputAdapter

logger = logging.getLogger(__name__)

class HumanInput(InputAdapter):
    def __init__(self, prompt: str = "> "):
        super().__init__()
        self.prompt = prompt
        self._stopped = False

    async def start(self):
        # No special setup needed, but available if future initialization is required
        pass

    async def read_message(self):
        if self._stopped:
            raise EOFError("HumanInput adapter has been stopped.")

        loop = asyncio.get_running_loop()
        try:
            # Display the prompt and read user input from stdin in a thread executor
            user_input = await loop.run_in_executor(None, lambda: input(self.prompt))
            logger.debug(f"User input received: {user_input}")
        except EOFError:
            # End of input (Ctrl+D), treat as no more input
            logger.debug("EOF reached from user input.")
            raise EOFError("No more user input available.")
        except KeyboardInterrupt:
            # If user sends Ctrl+C, also treat as EOF or no more input
            logger.debug("KeyboardInterrupt received, treating as EOF.")
            raise EOFError("Interrupted by user.")

        # Return a dictionary that the handler expects
        return {"role": "Questioner", "message": user_input}

    async def stop(self):
        logger.debug("Stopping HumanInput adapter, no more input will be read.")
        self._stopped = True
