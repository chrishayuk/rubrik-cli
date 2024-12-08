# adapters/output/websocket_output_adapter.py
import json
import asyncio
import logging
import websockets
from websockets.exceptions import ConnectionClosedError
from adapters.output.output_adapter import OutputAdapter

log = logging.getLogger(__name__)

class WebSocketOutput(OutputAdapter):
    def __init__(self, uri="ws://localhost:8000/ws", max_retries=3, retry_delay=2):
        self.uri = uri
        self.websocket = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def start(self):
        await self._connect_with_retries()

    async def write_message(self, data: dict):
        for attempt in range(self.max_retries):
            try:
                await self.websocket.send(json.dumps(data))
                return
            except ConnectionClosedError as e:
                log.debug(f"Connection lost during write_message: {e}")
                await self._reconnect()
            except TypeError as e:
                log.debug(f"Data serialization error: {e}")
                raise EOFError("Unable to send invalid data over WebSocket.")
        raise EOFError("Failed to write message after multiple retries.")

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
