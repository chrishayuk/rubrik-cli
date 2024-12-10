# adapters/input/human_input_adapter.py
import asyncio
from adapters.input.input_adapter import InputAdapter

class HumanInput(InputAdapter):    
    async def read_message(self):
        loop = asyncio.get_running_loop()
        user_input = await loop.run_in_executor(None, input, "")
        return {"role": "Questioner", "message": user_input}

        