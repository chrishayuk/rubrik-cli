# adapters/websocket_duplex_adapter.py
import json
import asyncio
import logging
import websockets
from websockets.exceptions import ConnectionClosedError

log = logging.getLogger(__name__)

class WebSocketDuplexAdapter:
    def __init__(self, uri="ws://localhost:8000/ws", max_retries=3, retry_delay=2):
        self.uri = uri
        self.websocket = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def start(self):
        await self._connect_with_retries()

    async def read_message(self) -> dict:
        while True:
            try:
                msg = await self.websocket.recv()
                try:
                    data = json.loads(msg)
                    return data
                except json.JSONDecodeError as e:
                    log.debug(f"Invalid JSON message received: {e}")
                    # Instead of ending the conversation, just continue reading next messages
                    continue
            except ConnectionClosedError as e:
                log.debug(f"Connection lost during read_message: {e}")
                await self._reconnect()
            except Exception as e:
                log.debug(f"Unexpected error during read_message: {e}")
                # Attempt to reconnect and continue
                await self._reconnect()

    async def write_message(self, data: dict):
        while True:
            try:
                # Validate that data can be serialized to JSON
                msg = json.dumps(data)
                await self.websocket.send(msg)
                return
            except ConnectionClosedError as e:
                log.debug(f"Connection lost during write_message: {e}")
                await self._reconnect()
            except TypeError as e:
                log.debug(f"Data serialization error: {e}")
                # If data can't be serialized, log and skip sending this message
                # This avoids killing the conversation. The malformed message is just not sent.
                return
            except Exception as e:
                log.debug(f"Unexpected error during write_message: {e}")
                # Attempt to reconnect and try again
                await self._reconnect()

    async def stop(self):
        if self.websocket:
            await self.websocket.close()

    async def get_user_input_and_send(self):
        # Continuously prompt user for input and send it
        while True:
            user_input = input("").strip()
            if user_input.lower() == "quit":
                break
            await self.write_message({"role": "Questioner", "message": user_input})

    async def _connect_with_retries(self):
        attempt = 0
        while True:
            attempt += 1
            try:
                self.websocket = await websockets.connect(self.uri)
                log.debug(f"Connected to {self.uri} on attempt {attempt}")
                return
            except Exception as e:
                log.debug(f"Failed to connect (attempt {attempt}): {e}")
                await asyncio.sleep(self.retry_delay)
                # Keep retrying indefinitely or add logic to give up after many attempts

    async def _reconnect(self):
        if self.websocket:
            await self.websocket.close()
        await self._connect_with_retries()
