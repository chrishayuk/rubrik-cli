# chat_handler/server_input_handler.py
import asyncio
import logging
from websockets.exceptions import ConnectionClosedError
from response_utils import get_response, safe_get_response

from chat_handler.ui_renderer import UIRenderer
from ui_utils import display_message, console

log = logging.getLogger(__name__)

async def handle_server_input(chat_handler):
    """
    Handles input from the server in server mode. This function reads messages
    from the input_adapter, which are typically user prompts from a client,
    and then responds using the responder_handler associated with the chat_handler.

    We now use UIRenderer to handle the display of partial and complete messages.
    Since multiple request_ids can be handled at once, we store a separate
    UIRenderer instance for each request_id in partial_messages.
    """
    # Dictionary to track ongoing partial messages
    # Key: request_id
    # Value: dict with 'chunks' (list of text), 'ui_renderer' (UIRenderer instance), 'role', 'finalized' (bool)
    partial_messages = {}

    while True:
        try:
            user_msg = await chat_handler.input_adapter.read_message()
        except (EOFError, ConnectionClosedError) as e:
            log.debug(f"Server input read error: {e}. Attempting to continue.")
            await asyncio.sleep(0.5)
            continue

        u_role = user_msg.get("role", "Unknown")
        chunk = user_msg.get("message", "")
        partial = user_msg.get("partial", False)
        request_id = user_msg.get("request_id", None)
        message_number = user_msg.get("message_number", None)

        if request_id is None:
            log.warning("Received message without request_id. Assigning a temporary ID.")
            request_id = f"temp_{id(user_msg)}"

        # Get or create the state for this request_id
        if request_id not in partial_messages:
            partial_messages[request_id] = {
                "chunks": [],
                "ui_renderer": None,
                "role": u_role,
                "finalized": False
            }

        msg_state = partial_messages[request_id]

        if partial:
            # We are receiving a partial chunk for this request_id
            msg_state["chunks"].append(chunk)

            # If no UI renderer started for this request yet, start now
            if msg_state["ui_renderer"] is None:
                msg_state["ui_renderer"] = UIRenderer()
                # Start streaming display
                initial_text = "".join(msg_state["chunks"])
                msg_state["ui_renderer"].start_streaming(
                    server=chat_handler.server,
                    local_name=chat_handler.local_name,
                    remote_name=chat_handler.remote_name,
                    role=u_role,
                    initial_text=initial_text
                )
            else:
                # Update streaming display with the new chunk
                msg_state["ui_renderer"].update_streaming(chunk)

        else:
            # This is the final chunk for the request_id
            msg_state["chunks"].append(chunk)
            full_prompt = "".join(msg_state["chunks"])
            msg_state["finalized"] = True

            # If we had a UI renderer for streaming, end it now
            if msg_state["ui_renderer"] and msg_state["ui_renderer"].is_streaming:
                msg_state["ui_renderer"].end_streaming()

            # Display the final user message
            msg_state["ui_renderer"] = msg_state["ui_renderer"] or UIRenderer()
            msg_state["ui_renderer"].display_complete_message(
                server=chat_handler.server,
                local_name=chat_handler.local_name,
                remote_name=chat_handler.remote_name,
                role=u_role,
                content=full_prompt
            )

            # Add the user message to the conversation
            chat_handler.conversation_manager.add_message(u_role, full_prompt)

            # Now we process the prompt fully using the responder
            answer = await safe_get_response(
                lambda q: get_response(
                    chat_handler.responder_handler,
                    chat_handler.output_adapter,
                    q,
                    chat_handler.conversation_manager.get_conversation(),
                    chat_handler.stream,
                    chat_handler.local_name,
                    console
                ),
                full_prompt
            )

            chat_handler.conversation_manager.add_message("responder", answer)

            # Send the final response message back
            try:
                if chat_handler.stream and hasattr(chat_handler.responder_handler, "get_response_stream"):
                    # If streaming was used for the answer, it should have been handled inside get_response_stream,
                    # and now we just finalize:
                    await chat_handler.output_adapter.write_message({"role": "Responder", "partial": False, "request_id": request_id})
                else:
                    # Normal non-streamed message
                    await chat_handler.output_adapter.write_message({"role": "Responder", "message": answer, "request_id": request_id})
                    msg_state["ui_renderer"].display_complete_message(
                        server=chat_handler.server,
                        local_name=chat_handler.local_name,
                        remote_name=chat_handler.remote_name,
                        role="responder",
                        content=answer
                    )
            except (ConnectionClosedError, EOFError) as e:
                log.debug(f"Failed to send responder message: {e}")

            # After responding, show the prompt again (server_mode=True since this is the server side)
            await msg_state["ui_renderer"].after_message(server_mode=chat_handler.server)

            # Remove the entry from partial_messages since we're done with this request_id
            del partial_messages[request_id]
