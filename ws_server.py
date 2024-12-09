import asyncio
import logging
import json
import uuid
import websockets
from urllib.parse import urlparse
from websockets.exceptions import ConnectionClosedError
from pydantic import ValidationError
from messages.message import MessageModel

logger = logging.getLogger(__name__)

connected_clients = set()

async def server_handler(websocket, path, message_queue: asyncio.Queue):
    """
    Handles individual WebSocket client connections.
    Receives messages, validates and wraps them into a standardized format (MessageModel),
    then puts them into the message_queue for further processing by downstream handlers.
    """
    connected_clients.add(websocket)
    logger.info(f"New client connected. Total clients: {len(connected_clients)}")

    try:
        # Continuously read messages from this client until they disconnect or send 'exit'
        async for raw_message in websocket:
            logger.debug(f"Received raw message from client: {raw_message}")

            # Attempt to parse as JSON
            try:
                data = json.loads(raw_message)
                was_structured = True
            except json.JSONDecodeError:
                # Not valid JSON, treat as plain text
                was_structured = False
                data = {
                    "role": "Questioner",
                    "message": raw_message,
                    "partial": False
                }

            if was_structured:
                # Validate structured message
                try:
                    message_obj = MessageModel(**data)
                except ValidationError as ve:
                    logger.error(f"Message validation failed (structured): {ve.errors()}")
                    error_response = {
                        "role": "Server",
                        "message": "Invalid message format or content. Check fields.",
                        "partial": False,
                        "request_id": data.get("request_id", str(uuid.uuid4()))
                    }
                    # Send structured error response back to the client
                    await websocket.send(json.dumps(error_response))
                    continue

                # Validation passed, forward downstream
                structured_message = message_obj.model_dump_json()
                await message_queue.put(structured_message)

            else:
                # Validate unstructured message
                try:
                    message_obj = MessageModel(**data)
                except ValidationError as ve:
                    logger.error(f"Message validation failed (unstructured): {ve.errors()}")
                    # Respond in plain text since message was not structured
                    await websocket.send("Invalid message. Please send a non-empty message.")
                    continue

                # Validation passed, forward downstream
                structured_message = message_obj.model_dump_json()
                await message_queue.put(structured_message)

                # If needed, respond in plain text:
                # await websocket.send("Received your message.")

    except ConnectionClosedError as e:
        # The client disconnected unexpectedly.
        logger.info(f"Client connection closed unexpectedly: {e}")
    except Exception as e:
        logger.error(f"An error occurred while handling client: {e}")
    finally:
        connected_clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")

async def start_server(server_ws_uri: str, message_queue: asyncio.Queue):
    """
    Starts the WebSocket server and runs indefinitely.
    """
    parsed = urlparse(server_ws_uri)
    host = parsed.hostname
    port = parsed.port

    logger.info(f"Starting WebSocket server at {server_ws_uri}")

    # Disable ping and timeout intervals to reduce unintended disconnections
    async with websockets.serve(
        lambda ws, path: server_handler(ws, path, message_queue),
        host,
        port,
        ping_interval=None,
        ping_timeout=None,
        close_timeout=None
    ):
        logger.info(f"WebSocket server running at {server_ws_uri}")
        # Keep the server running indefinitely, even if clients connect/disconnect
        await asyncio.Future()
