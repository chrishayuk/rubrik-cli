# adapters/input/websocket_input_adapter.py
import json
import websockets
from adapters.input.input_adapter import InputAdapter


class WebSocketInput(InputAdapter):
    def __init__(self, uri="ws://localhost:8000/ws"):
        # set properties
        self.uri = uri
        self.websocket = None
        self.websockets = websockets

    async def start(self):
        # connect to websocket
        self.websocket = await self.websockets.connect(self.uri)

    async def read_message(self) -> dict:
        try:
            # read message from websocket
            msg = await self.websocket.recv()

            # parse message as JSON
            return json.loads(msg)
        except self.websockets.exceptions.ConnectionClosedError:
            # raise error
            raise EOFError("Websocket closed.")

    async def stop(self):
        # check if websocket is open
        if self.websocket:
            # close websocket
            await self.websocket.close()