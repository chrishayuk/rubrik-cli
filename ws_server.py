import asyncio
import websockets
from urllib.parse import urlparse

# connected clients
connected_clients = set()

async def server_handler(websocket, path, message_queue: asyncio.Queue):
    # When a client connects
    connected_clients.add(websocket)
    print(f"New client connected! Total clients: {len(connected_clients)}")

    try:
        # Receive messages from this client
        async for message in websocket:
            # Instead of broadcasting, put the message into the queue for the chat handler
            await message_queue.put(message)

    finally:
        # When client disconnects
        connected_clients.remove(websocket)
        print(f"Client disconnected! Total clients: {len(connected_clients)}")

async def start_server(server_ws_uri: str, message_queue: asyncio.Queue):
    # Parse the URL
    parsed = urlparse(server_ws_uri)
    host = parsed.hostname
    port = parsed.port

    # Pass the message_queue into the lambda so server_handler receives it
    async with websockets.serve(lambda ws, path: server_handler(ws, path, message_queue), host, port):
        print(f"WebSocket server running at {server_ws_uri}")
        # Keep the server running indefinitely
        await asyncio.Future()  
