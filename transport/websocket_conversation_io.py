# transport/websocket_conversation_io.py
import json
import websockets
from typing import Dict, Any
from transport.conversation_io import ConversationIO

class WebSocketConversationIO(ConversationIO):
    def __init__(self, uri="ws://localhost:8000/ws"):
        self.uri = uri
        self.websocket = None

    async def start_conversation(self):
        self.websocket = await websockets.connect(self.uri)

    async def listen(self) -> Dict[str, Any]:
        message = await self.websocket.recv()
        return json.loads(message)

    async def respond(self, data: Dict[str, Any]):
        await self.websocket.send(json.dumps(data))

    async def end_conversation(self):
        if self.websocket:
            await self.websocket.close()