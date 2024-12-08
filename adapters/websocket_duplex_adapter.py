import json
import websockets

class WebSocketDuplexAdapter:
    def __init__(self, uri="ws://localhost:8000/ws"):
        self.uri = uri
        self.websocket = None

    async def start(self):
        self.websocket = await websockets.connect(self.uri)

    async def read_message(self) -> dict:
        msg = await self.websocket.recv()
        return json.loads(msg)

    async def write_message(self, data: dict):
        await self.websocket.send(json.dumps(data))

    async def stop(self):
        if self.websocket:
            await self.websocket.close()

    async def get_user_input_and_send(self):
        # Continuously prompt user for input and send it
        while True:
            user_input = input("User: ")
            if user_input.strip().lower() == "quit":
                break
            await self.write_message({"role": "Questioner", "message": user_input})

