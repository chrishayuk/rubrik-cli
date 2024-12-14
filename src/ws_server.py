import asyncio
import logging
import json
import uuid
import websockets
from urllib.parse import urlparse
from websockets.exceptions import ConnectionClosedError
from pydantic import ValidationError, parse_obj_as
from messages.message_types import MessageUnion  # Import your union of message models

logger = logging.getLogger(__name__)

connected_clients = set()

async def server_handler(websocket: websockets.WebSocketServerProtocol, message_queue: asyncio.Queue) -> None:
    """
    Handles individual WebSocket client connections.
    Receives messages, validates and converts them into a standardized format (using MessageUnion),
    then puts them into the message_queue for further processing.
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
                # Not valid JSON, treat as a simple chat message from a Questioner
                was_structured = False
                data = {
                    "role": "Questioner",
                    "type": "chat",
                    "message": raw_message,
                    "partial": False
                }

            # Validate message using MessageUnion
            try:
                # Use parse_obj_as for union parsing
                message_obj = parse_obj_as(MessageUnion, data)
            except ValidationError as ve:
                # Validation failed
                request_id = data.get("request_id", str(uuid.uuid4()))
                logger.error(f"Message validation failed: {ve.errors()}")

                # Convert errors to a JSON-serializable structure
                error_list = ve.errors()
                for err in error_list:
                    if 'ctx' in err and 'error' in err['ctx']:
                        # Convert the exception object to a string
                        err['ctx']['error'] = str(err['ctx']['error'])

                if was_structured:
                    # Return a structured error response
                    error_response = {
                        "role": "Server",
                        "message": "Validation error: One or more fields are invalid.",
                        "partial": False,
                        "request_id": request_id,
                        "errors": error_list
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
    """
    parsed = urlparse(server_ws_uri)
    host = parsed.hostname
    port = parsed.port

    logger.info(f"Starting WebSocket server at {server_ws_uri}")

    # Disable ping and timeout intervals to reduce unintended disconnections
    async with websockets.serve(
        lambda ws: server_handler(ws, message_queue),
        host,
        port,
        ping_interval=None,
        ping_timeout=None,
        close_timeout=None
    ):
        logger.info(f"WebSocket server running at {server_ws_uri}")
        # Keep the server running indefinitely
        await asyncio.Future()
