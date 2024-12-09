import asyncio
import logging
import json
import uuid
import websockets
from urllib.parse import urlparse
from websockets.exceptions import ConnectionClosedError
from pydantic import ValidationError
from messages.message import MessageModel

# setup logg
logger = logging.getLogger(__name__)

# connections
connected_clients = set()

async def server_handler(websocket, path, message_queue: asyncio.Queue):
    # add the client
    connected_clients.add(websocket)
    logger.info(f"New client connected. Total clients: {len(connected_clients)}")

    try:
        # get the message
        async for raw_message in websocket:
            # log it
            logger.debug(f"Received raw message from client: {raw_message}")

            # Try JSON parsing
            try:
                # load as json
                data = json.loads(raw_message)

                # structured
                was_structured = True
            except json.JSONDecodeError:
                # failed to parse as json, assume it's a string
                was_structured = False

                # wrap it in a dictionary
                data = {
                    "role": "Questioner",
                    "message": raw_message,
                    "partial": False
                }

            # check if it's valid
            if was_structured:
                # Validate structured message
                try:
                    # Validate the data against your model
                    message_obj = MessageModel(**data)
                except ValidationError as ve:
                    # Log the error
                    logger.error(f"Message validation failed (structured): {ve.errors()}")

                    # data is a dictionary, safe to use get()
                    error_response = {
                        "role": "Server",
                        "message": "Invalid message format or content. Check fields.",
                        "partial": False,
                        "request_id": data.get("request_id", str(uuid.uuid4()))
                    }

                    # Respond with the error response
                    await websocket.send(json.dumps(error_response))

                    # Skip to the next iteration of the loop
                    continue

                # Validation passed
                structured_message = message_obj.model_dump_json()

                # put in the queue
                await message_queue.put(structured_message)

            else:
                # Validate unstructured (plain text wrapped into a dict)
                try:
                    message_obj = MessageModel(**data)
                except ValidationError as ve:
                    logger.error(f"Message validation failed (unstructured): {ve.errors()}")
                    # Respond in plain text since the client sent plain text
                    await websocket.send("Invalid message. Please send a non-empty message.")
                    continue

                # Validation passed
                structured_message = message_obj.model_dump_json()
                await message_queue.put(structured_message)

                # Optionally respond in plain text if needed:
                # await websocket.send("Received your message.")

    except ConnectionClosedError as e:
        logger.info(f"Client connection closed unexpectedly: {e}")
    except Exception as e:
        logger.error(f"An error occurred while handling client: {e}")
    finally:
        connected_clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")


async def start_server(server_ws_uri: str, message_queue: asyncio.Queue):
    parsed = urlparse(server_ws_uri)
    host = parsed.hostname
    port = parsed.port

    logger.info(f"Starting WebSocket server at {server_ws_uri}")

    async with websockets.serve(
        lambda ws, path: server_handler(ws, path, message_queue),
        host,
        port,
        ping_interval=None,
        ping_timeout=None,
        close_timeout=None
    ):
        logger.info(f"WebSocket server running at {server_ws_uri}")
        await asyncio.Future()
