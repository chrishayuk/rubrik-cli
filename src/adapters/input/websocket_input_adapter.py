# adapters/input/websocket_input_adapter.py
import json
import asyncio
import logging
import websockets
from websockets.exceptions import ConnectionClosedError
from adapters.input.input_adapter import InputAdapter

log = logging.getLogger(__name__)

class WebSocketInput(InputAdapter):
    def __init__(self, uri="ws://localhost:8000/ws", max_retries=3, retry_delay=2):
        self.uri = uri
        self.websocket = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def start(self):
        await self._connect_with_retries()

    async def read_message(self) -> dict:
        for attempt in range(self.max_retries):
            try:
                msg = await self.websocket.recv()
                return json.loads(msg)
            except ConnectionClosedError as e:
                log.debug(f"Connection lost during read_message: {e}")
                await self._reconnect()
            except json.JSONDecodeError as e:
                log.debug(f"Invalid JSON message received: {e}")
                raise EOFError("Received invalid JSON message from WebSocket.")
        raise EOFError("Failed to read message after multiple retries.")

    async def stop(self):
        if self.websocket:
            await self.websocket.close()

    async def _connect_with_retries(self):
        for attempt in range(self.max_retries):
            try:
                self.websocket = await websockets.connect(self.uri)
                return
            except Exception as e:
                log.debug(f"Failed to connect (attempt {attempt+1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)
        raise EOFError("Unable to establish WebSocket connection after multiple attempts.")

    async def _reconnect(self):
        if self.websocket:
            await self.websocket.close()
        await self._connect_with_retries()
