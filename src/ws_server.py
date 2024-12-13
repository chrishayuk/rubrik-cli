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

async def server_handler(websocket: websockets.WebSocketServerProtocol, path: str, message_queue: asyncio.Queue) -> None:
    """
    Handles individual WebSocket client connections.
    Receives messages, validates and wraps them into a standardized format (MessageModel),
    then puts them into the message_queue for further processing by downstream handlers.

    Parameters
    ----------
    websocket : websockets.WebSocketServerProtocol
        The client's websocket connection.
    path : str
        The requested path for the websocket (unused in this example).
    message_queue : asyncio.Queue
        A queue where validated messages will be placed for downstream processing.
    """
    connected_clients.add(websocket)
    logger.info(f"New client connected. Total clients: {len(connected_clients)}")

    try:
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

            # Validate message using MessageModel
            try:
                message_obj = MessageModel(**data)
            except ValidationError as ve:
                # Validation failed
                request_id = data.get("request_id", str(uuid.uuid4()))
                logger.error(f"Message validation failed: {ve.errors()}")

                if was_structured:
                    # For structured messages, return a structured error response
                    error_response = {
                        "role": "Server",
                        "message": "Validation error: One or more fields are invalid.",
                        "partial": False,
                        "request_id": request_id,
                        "errors": ve.errors()
                    }
                    await websocket.send(json.dumps(error_response))
                else:
                    # For unstructured, just send a text error response
                    await websocket.send("Invalid message. Please send a non-empty message.")
                continue

            # Validation passed
            structured_message = message_obj.model_dump_json()

            # Add was_structured info to the message before putting it on the queue
            message_dict = json.loads(structured_message)
            message_dict["was_structured"] = was_structured

            logger.debug(f"Validated message (was_structured={was_structured}, "
                         f"request_id={message_dict['request_id']}): {message_dict}")

            # Put the updated message dict as JSON back into the queue for downstream processing
            await message_queue.put(json.dumps(message_dict))

    except ConnectionClosedError as e:
        logger.info(f"Client connection closed unexpectedly: {e}")
    except Exception as e:
        logger.error(f"An error occurred while handling client: {e}")
    finally:
        connected_clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")


async def start_server(server_ws_uri: str, message_queue: asyncio.Queue) -> None:
    """
    Starts the WebSocket server and runs indefinitely.

    Parameters
    ----------
    server_ws_uri : str
        The URI at which to start the WebSocket server (e.g. "ws://localhost:9000").
    message_queue : asyncio.Queue
        A queue to which incoming validated messages are sent.
    """
    parsed = urlparse(server_ws_uri)
    host = parsed.hostname
    port = parsed.port

    logger.info(f"Starting WebSocket server at {server_ws_uri}")

    # Disable ping and timeout intervals to reduce unintended disconnections
    async with websockets.serve(
        lambda ws, p: server_handler(ws, p, message_queue),
        host,
        port,
        ping_interval=None,
        ping_timeout=None,
        close_timeout=None
    ):
        logger.info(f"WebSocket server running at {server_ws_uri}")
        # Keep the server running indefinitely
        await asyncio.Future()
