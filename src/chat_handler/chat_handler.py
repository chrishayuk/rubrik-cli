import asyncio
import logging
from websockets.exceptions import ConnectionClosedError
from .conversation_manager import ConversationManager
from .server_input_handler import handle_server_input
from .user_input_handler import handle_user_input
from .server_messages_handler import handle_server_messages
from .adapters import start_adapters, stop_adapters
from .ui_utils import print_environment_info, print_prompt, console
from response_handlers.response_handler_factory import create_response_handler
from rich.panel import Panel

log = logging.getLogger(__name__)

class ChatHandler:
    def __init__(self, 
                 input_adapter,
                 output_adapter,
                 mode: str = "human", 
                 provider: str = "ollama", 
                 model: str = "llama3.3", 
                 persona: str = None,
                 stream: bool = False,
                 server: bool = False):

        self.input_adapter = input_adapter
        self.output_adapter = output_adapter
        self.mode = mode
        self.provider = provider
        self.model = model
        self.persona = persona
        self.stream = stream
        self.server = server

        # Conversation manager for tracking conversation state
        self.conversation_manager = ConversationManager()

        # Create the appropriate responder handler and mode description
        self.responder_handler, local_mode_desc = create_response_handler(mode, provider, model, persona)

        # Determine local and remote roles
        if self.server:
            self.local_name = f"Assistant ({local_mode_desc}, Server)"
            self.remote_name = "Questioner (Client)"
        else:
            self.local_name = f"You ({local_mode_desc}, Client)"
            self.remote_name = "Assistant (Server)"

    async def run(self):
        # Print environment info at start
        print_environment_info(
            server=self.server,
            mode=self.mode,
            persona=self.persona,
            provider=self.provider,
            model=self.model,
            input_adapter_name=self.input_adapter.__class__.__name__,
            output_adapter_name=self.output_adapter.__class__.__name__,
            local_name=self.local_name,
            remote_name=self.remote_name
        )

        # Start adapters if they have start methods
        await start_adapters(self.input_adapter, self.output_adapter)

        # If human client and not server, print initial prompt
        if self.mode == "human" and not self.server:
            console.print()
            await print_prompt(server_mode=False)

        try:
            if self.server:
                # In server mode, handle input from server_input_handler
                await handle_server_input(self)
            else:
                # In client mode, handle user input and possibly server messages
                user_input_task = asyncio.create_task(handle_user_input(self))
                tasks = [user_input_task]

                # If output_adapter supports reading messages, handle server messages too
                if hasattr(self.output_adapter, "read_message"):
                    server_response_task = asyncio.create_task(handle_server_messages(self))
                    tasks.append(server_response_task)

                # Wait for tasks to complete
                await asyncio.gather(*tasks)
        except (ConnectionClosedError, EOFError) as e:
            log.debug(f"Connection ended abruptly: {e}")
        finally:
            await stop_adapters(self.input_adapter, self.output_adapter)
            from chat_handler.ui_utils import print_panel
            print_panel("Chat", "The conversation has concluded. Thank you.", "system")
