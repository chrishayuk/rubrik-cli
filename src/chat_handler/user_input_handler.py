# chat_handler/user_input_handler.py
import asyncio
import logging
from websockets.exceptions import ConnectionClosedError
from chat_handler.ui_renderer import UIRenderer

log = logging.getLogger(__name__)

async def handle_user_input(chat_handler):
    """
    Handles user input in client mode.
    Delegates UI rendering to UIRenderer.
    """
    ui_renderer = UIRenderer()

    while True:
        try:
            user_msg = await chat_handler.input_adapter.read_message()
        except (EOFError, ConnectionClosedError) as e:
            log.debug(f"User input read error: {e}, will try again.")
            await asyncio.sleep(0.5)
            continue

        u_role = user_msg.get("role", "Unknown")
        u_content = user_msg.get("message", "")

        if u_content.strip().lower() == "exit":
            # User wants to exit
            break

        # Add user message to conversation
        chat_handler.conversation_manager.add_message(u_role, u_content)

        # Display user's message via UIRenderer
        ui_renderer.display_complete_message(
            server=chat_handler.server, 
            local_name=chat_handler.local_name, 
            remote_name=chat_handler.remote_name, 
            role=u_role, 
            content=u_content
        )

        # Relay the user's message to the server (in client mode)
        try:
            await chat_handler.output_adapter.write_message(user_msg)
        except (ConnectionClosedError, EOFError) as e:
            log.debug(f"Failed to relay user message: {e}")
            await asyncio.sleep(0.5)
            continue

        # After showing the user's message and sending it along, show prompt
        await ui_renderer.after_message(server_mode=chat_handler.server)
