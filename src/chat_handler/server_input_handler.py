# chat_handler/server_input_handler.py
import asyncio
import logging
import uuid
from websockets.exceptions import ConnectionClosedError
from pydantic import ValidationError, parse_obj_as
from messages.message_types import MessageUnion
from .response_utils import get_response, safe_get_response
from .ui_renderer import UIRenderer
from .ui_utils import display_message, console

log = logging.getLogger(__name__)

async def handle_server_input(chat_handler):
    """
    Handles input from the server in server mode.
    Processes user messages, including partial and complete messages, and obtains
    responses from the responder. If streaming is enabled, the final completion
    message is now handled by `get_response` only, to avoid duplication.
    """
    # Track ongoing partial messages per request_id
    partial_messages = {}

    while True:
        try:
            user_msg = await chat_handler.input_adapter.read_message()
        except (EOFError, ConnectionClosedError) as e:
            log.debug(f"Server input read error: {e}. Attempting to continue.")
            await asyncio.sleep(0.5)
            continue

        # Ensure type field is present; assume "chat" if missing
        if "type" not in user_msg:
            user_msg["type"] = "chat"

        # Ensure request_id is present; generate one if missing
        if "request_id" not in user_msg:
            log.warning("Received message without request_id. Assigning a temporary ID.")
            user_msg["request_id"] = str(uuid.uuid4())

        # Attempt to validate and parse message using MessageUnion
        try:
            message_obj = parse_obj_as(MessageUnion, user_msg)
        except ValidationError as ve:
            log.error(f"Message validation failed: {ve.errors()}")
            continue

        # Extract fields from the validated model
        role = message_obj.role.value  # role is an Enum, get its string value
        request_id = str(message_obj.request_id)  # Convert UUID to string
        partial = getattr(message_obj, 'partial', False)
        message_text = getattr(message_obj, 'message', "")

        # Access the partial_messages state for this request_id
        if request_id not in partial_messages:
            partial_messages[request_id] = {
                "chunks": [],
                "ui_renderer": None,
                "role": role,
                "finalized": False
            }

        msg_state = partial_messages[request_id]

        if partial:
            # Handle partial chunk
            msg_state["chunks"].append(message_text)

            # Start or update the streaming UI
            if msg_state["ui_renderer"] is None:
                msg_state["ui_renderer"] = UIRenderer()
                initial_text = "".join(msg_state["chunks"])
                msg_state["ui_renderer"].start_streaming(
                    server=chat_handler.server,
                    local_name=chat_handler.local_name,
                    remote_name=chat_handler.remote_name,
                    role=role,
                    initial_text=initial_text
                )
            else:
                # Update streaming display with the new chunk
                msg_state["ui_renderer"].update_streaming(message_text)

        else:
            # Final message
            msg_state["chunks"].append(message_text)
            full_prompt = "".join(msg_state["chunks"])
            msg_state["finalized"] = True

            # End streaming if it was ongoing
            if msg_state["ui_renderer"] and msg_state["ui_renderer"].is_streaming:
                msg_state["ui_renderer"].end_streaming()

            # Display the complete user message
            msg_state["ui_renderer"] = msg_state["ui_renderer"] or UIRenderer()
            msg_state["ui_renderer"].display_complete_message(
                server=chat_handler.server,
                local_name=chat_handler.local_name,
                remote_name=chat_handler.remote_name,
                role=role,
                content=full_prompt
            )

            # Add the user message to the conversation
            chat_handler.conversation_manager.add_message(role, full_prompt)

            # Process the prompt fully using the responder
            answer = await safe_get_response(
                lambda q: get_response(
                    chat_handler.responder_handler,
                    chat_handler.output_adapter,
                    q,
                    chat_handler.conversation_manager.get_conversation(),
                    chat_handler.stream,
                    chat_handler.local_name,
                    console,
                    request_id=request_id
                ),
                full_prompt
            )

            chat_handler.conversation_manager.add_message("responder", answer)

            # Only display the final complete message here if we're NOT streaming.
            # In streaming mode, get_response handles all UI updates, including the final state.
            if not chat_handler.stream:
                msg_state["ui_renderer"].display_complete_message(
                    server=chat_handler.server,
                    local_name=chat_handler.local_name,
                    remote_name=chat_handler.remote_name,
                    role="responder",
                    content=answer
                )

            # After responding, show the prompt again
            await msg_state["ui_renderer"].after_message(server_mode=chat_handler.server)

            # Remove the request_id since we're done with this message
            del partial_messages[request_id]
