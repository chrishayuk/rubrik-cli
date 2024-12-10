# adapters/input/server_input_adapter.py
import asyncio
import json

class ServerInputAdapter:
    def __init__(self, message_queue: asyncio.Queue):
        self.message_queue = message_queue

    async def start(self):
        # do nothing
        pass

    async def read_message(self):
        # Get a message from the queue (expected to be a JSON string)
        msg = await self.message_queue.get()

        # Parse the JSON string into a dictionary
        data = json.loads(msg)

        # data should now look like {"role": "Questioner", "message": "hi"}
        return data
    
    async def stop(self):
        # do nothing
        pass
