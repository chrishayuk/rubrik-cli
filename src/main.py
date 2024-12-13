# main.py
import asyncio
import logging
from arg_parser import parse_args, Config
from adapters_factory import create_input_adapter, create_output_adapter
from chat_handler.chat_handler import ChatHandler
from ws_server import start_server

# setup the logger
logger = logging.getLogger(__name__)
logging_level = logging.DEBUG

def setup_logging(level=logging_level) -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=level
    )

async def run_chat(config: Config, message_queue: asyncio.Queue) -> None:
    """
    Run the chat handler according to the provided configuration.
    """
    # check that a persona is specified in persona model
    if config.mode == "persona" and not config.persona:
        raise ValueError("--persona is required when --mode persona")
    
    # create the adapters
    input_adapter = create_input_adapter(config, message_queue)
    output_adapter = create_output_adapter(config)

    # setup the chat handler
    handler = ChatHandler(
        input_adapter=input_adapter,
        output_adapter=output_adapter,
        mode=config.mode,
        provider=config.provider,
        model=config.model,
        persona=config.persona,
        stream=config.stream,
        server=config.server
    )

    # start the chat
    await handler.run()

async def run_app(config: Config) -> None:
    """
    Run the application based on the provided configuration.
    
    :param config: Configuration object.
    """
    # setup a message queue
    message_queue = asyncio.Queue()

    # check if we're running as a server
    if config.server:
        # Server mode: run both the server and chat handler concurrently
        await asyncio.gather(
            start_server(config.server_ws_uri, message_queue),
            run_chat(config, message_queue)
        )
    else:
        # Client mode: just run the chat handler
        await run_chat(config, message_queue)

def main():
    # setup logging
    setup_logging()

    # get the config
    config = parse_args()

    # run the app
    asyncio.run(run_app(config))

if __name__ == "__main__":
    main()