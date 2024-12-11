# adapters/input/server_input_adapter.py
import asyncio
import json

class ServerInputAdapter:
    def __init__(self, message_queue: asyncio.Queue):
        self.message_queue = message_queue
        self._stopped = False

    async def start(self):
        # No initialization needed
        pass

    async def read_message(self):
        if self._stopped:
            raise EOFError("Adapter is stopped and no further messages can be read.")

        try:
            msg = await self.message_queue.get()
            if msg is None:
                # If None is used to signal no more messages, treat as EOF
                raise EOFError("No more messages available (None received).")
            data = json.loads(msg)
            return data
        except json.JSONDecodeError:
            raise EOFError("Invalid JSON message received from the queue.")
        except asyncio.CancelledError:
            # If reading is cancelled, return EOFError to unify error handling
            raise EOFError("Read operation cancelled.")
        except Exception as e:
            raise EOFError(f"Unexpected error while reading message: {e}")

    async def stop(self):
        self._stopped = True
