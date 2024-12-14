# chat_handler/server_messages_handler.py
import asyncio
import logging
from websockets.exceptions import ConnectionClosedError
from .ui_renderer import UIRenderer

log = logging.getLogger(__name__)

async def handle_server_messages(chat_handler):
    ui_renderer = UIRenderer()

    while True:
        try:
            server_msg = await chat_handler.output_adapter.read_message()
        except EOFError:
            log.debug("No more server messages for now, will keep waiting.")
            await asyncio.sleep(0.5)
            continue
        except ConnectionClosedError as e:
            log.debug(f"Connection closed while reading server messages: {e}, waiting and continuing.")
            await asyncio.sleep(0.5)
            continue
        except Exception as e:
            log.debug(f"Unexpected error while reading server messages: {e}, waiting and continuing.")
            await asyncio.sleep(0.5)
            continue

        s_role = server_msg.get("role", "unknown")
        s_content = server_msg.get("message", "")
        partial = server_msg.get("partial", False)

        if partial:
            # Handle streaming messages
            if not ui_renderer.is_streaming:
                ui_renderer.start_streaming(chat_handler.server, chat_handler.local_name, chat_handler.remote_name, s_role, s_content)
            else:
                ui_renderer.update_streaming(s_content)
        else:
            # Handle complete messages
            if ui_renderer.is_streaming:
                ui_renderer.end_streaming()
                await ui_renderer.after_message(server_mode=False)
            else:
                ui_renderer.display_complete_message(chat_handler.server, chat_handler.local_name, chat_handler.remote_name, s_role, s_content)
                await ui_renderer.after_message(server_mode=False)
