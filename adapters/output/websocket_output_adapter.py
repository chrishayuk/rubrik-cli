# adapters/output/websocket_output_adapter.py
import json
import websockets
from adapters.output.output_adapter import OutputAdapter

class WebSocketOutput(OutputAdapter):
    def __init__(self, uri="ws://localhost:8000/ws"):
        # set properties
        self.uri = uri
        self.websocket = None
        self.websockets = websockets

    async def start(self):
        # connect to websocket
        self.websocket = await self.websockets.connect(self.uri)

    async def write_message(self, data: dict):
        # send message
        await self.websocket.send(json.dumps(data))

    async def stop(self):
        # close connection
        if self.websocket:
            # close websocket
            await self.websocket.close()