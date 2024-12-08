import asyncio

class ServerInputAdapter:
    def __init__(self, message_queue: asyncio.Queue):
        # set up the message queue
        self.message_queue = message_queue

    async def start(self):
        # do nothing
        pass

    async def read_message(self):
        # get a message from the queue
        msg = await self.message_queue.get()

        # return the message
        return {"role": "questioner", "message": msg}
    
    async def stop(self):
        # do nothing
        pass
