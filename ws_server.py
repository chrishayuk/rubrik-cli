import asyncio
import logging
from urllib.parse import urlparse
import websockets

# set the logger
logger = logging.getLogger(__name__)

# Connected clients
connected_clients = set()

async def server_handler(websocket, path, message_queue: asyncio.Queue):
    """
    Handles individual WebSocket client connections.
    """
    connected_clients.add(websocket)
    logger.debug(f"New client connected. Total clients: {len(connected_clients)}")

    try:
        async for message in websocket:
            # Log and enqueue incoming messages
            logger.debug(f"Received message from client: {message}")

            # put the message in the queue
            await message_queue.put(message)
    except websockets.exceptions.ConnectionClosedError as e:
        # Handle unexpected client disconnections
        logger.debug(f"Client connection closed unexpectedly: {e}")
    except Exception as e:
        # Catch-all for unexpected errors
        logger.debug(f"An error occurred while handling client: {e}")
    finally:
        # Ensure the client is removed from the set safely
        connected_clients.discard(websocket)
        logger.debug(f"Client disconnected. Total clients: {len(connected_clients)}")

async def start_server(server_ws_uri: str, message_queue: asyncio.Queue):
    """
    Starts the WebSocket server.
    """
    parsed = urlparse(server_ws_uri)
    host = parsed.hostname
    port = parsed.port

    logger.debug(f"Starting WebSocket server at {server_ws_uri}")
    async with websockets.serve(lambda ws, path: server_handler(ws, path, message_queue), host, port):
        # running
        logger.debug(f"WebSocket server running at {server_ws_uri}")

        # Keep the server running indefinitely
        await asyncio.Future()
