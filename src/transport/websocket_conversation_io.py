# transport/websocket_conversation_io.py
import json
import websockets
from typing import Dict, Any, AsyncGenerator
from transport.conversation_io import ConversationIO, ConversationEndedError

class WebSocketConversationIO(ConversationIO):
    def __init__(self, uri="ws://localhost:8000/ws"):
        self.uri = uri
        self.websocket = None

    async def start_conversation(self):
        self.websocket = await websockets.connect(self.uri)

    async def listen(self) -> Dict[str, Any]:
        try:
            message = await self.websocket.recv()
        except websockets.exceptions.ConnectionClosedError:
            raise ConversationEndedError("The conversation ended unexpectedly.")
        return json.loads(message)

    async def respond(self, data: Dict[str, Any]):
        await self.websocket.send(json.dumps(data))

    async def end_conversation(self):
        if self.websocket:
            await self.websocket.close()

    async def listen_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            while True:
                raw_msg = await self.websocket.recv()
                msg = json.loads(raw_msg)
                yield msg
                if msg.get("done", False):
                    break
        except websockets.exceptions.ConnectionClosedError:
            raise ConversationEndedError("The conversation ended unexpectedly during streaming.")

