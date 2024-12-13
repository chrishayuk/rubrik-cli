# adapters/output/server_output_adapter.py
import json
import asyncio

class ServerOutputAdapter:
    def __init__(self, clients_set, max_send_retries=3, retry_delay=1.0):
        self.clients = clients_set
        self._stopped = False
        self.max_send_retries = max_send_retries
        self.retry_delay = retry_delay

    async def start(self):
        pass

    async def write_message(self, data):
        if self._stopped:
            raise EOFError("Adapter is stopped and cannot write messages.")

        try:
            message_str = json.dumps(data)
        except (TypeError, ValueError) as e:
            raise EOFError(f"Unable to serialize data: {e}")

        await self._broadcast_with_retries(message_str)

    async def broadcast(self, message_str: str):
        # Reintroducing broadcast method for tests that call it directly.
        await self._broadcast_with_retries(message_str)

    async def _broadcast_with_retries(self, message_str: str):
        to_remove = []
        for client in self.clients:
            success = False
            for attempt in range(self.max_send_retries):
                try:
                    await client.send(message_str)
                    success = True
                    break
                except Exception:
                    if attempt < self.max_send_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                    else:
                        to_remove.append(client)
            # If after all retries success is False, client will be removed.

        for client in to_remove:
            self.clients.remove(client)

    async def stop(self):
        self._stopped = True
