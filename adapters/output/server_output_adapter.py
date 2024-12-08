# adapters/output/server_output_adapter.py
import asyncio
import json

class ServerOutputAdapter:
    def __init__(self, clients_set):
        # a reference to connected_clients from ws_server.py
        self.clients = clients_set  

    async def start(self):
        # do nothing
        pass

    async def write_message(self, data):
        # data is a dict like {"role": "Responder", "message": "woof"}
        # Convert to JSON string
        message_str = json.dumps(data)

        # Broadcast this JSON-encoded message to all clients
        await self.broadcast(message_str)

    async def broadcast(self, message_str: str):
        # Initialize a list of clients that need to be removed
        to_remove = []

        # Iterate over all clients
        for client in self.clients:
            try:
                # Send message as a JSON string
                await client.send(message_str)
            except:
                # If send fails, mark client for removal
                to_remove.append(client)
        for client in to_remove:
            # Remove the client from connected_clients
            self.clients.remove(client)

    async def stop(self):
        # do nothing
        pass
