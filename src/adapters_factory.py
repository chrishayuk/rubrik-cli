# adapters_factory.py
import asyncio
from typing import Optional

from arg_parser import Config

# Input adapters
from adapters.input.human_input_adapter import HumanInput
from adapters.input.server_input_adapter import ServerInputAdapter
from adapters.input.stdin_input_adapter import StdInInput
from adapters.input.websocket_input_adapter import WebSocketInput

# Output adapters
from adapters.output.human_output_adapter import HumanOutput
from adapters.output.server_output_adapter import ServerOutputAdapter
from adapters.output.stdout_output_adapter import StdOutOutput
from adapters.output.websocket_output_adapter import WebSocketOutput

# Duplex adapter
from adapters.duplex.websocket_duplex_adapter import WebSocketDuplexAdapter

# Server
from ws_server import connected_clients

# UI renderer for human output
from rich_renderer import RichRenderer


def create_input_adapter(config: Config, message_queue: Optional[asyncio.Queue] = None):
    """
    Create and return an input adapter based on the config.
    
    :param config: The configuration object.
    :param message_queue: An asyncio.Queue used for server mode messages.
    :return: An initialized input adapter.
    :raises ValueError: If stdin input is selected without providing a cmd.
    """
    if config.server:
        return ServerInputAdapter(message_queue)

    if config.input_type == "human":
        return HumanInput()
    elif config.input_type == "stdin":
        if not config.cmd:
            raise ValueError("--cmd is required when --input=stdin")
        return StdInInput(cmd=config.cmd)
    else:  # websocket input
        return WebSocketInput(uri=config.input_ws_uri)


def create_output_adapter(config: Config):
    """
    Create and return an output adapter based on the config.
    
    :param config: The configuration object.
    :return: An initialized output adapter.
    """
    if config.server:
        if config.output_type == "websocket" and config.output_ws_uri:
            return WebSocketOutput(uri=config.output_ws_uri)
        else:
            return ServerOutputAdapter(connected_clients)
    else:
        if config.output_type == "human":
            return HumanOutput(renderer=RichRenderer)
        elif config.output_type == "stdout":
            return StdOutOutput()
        else:
            return WebSocketDuplexAdapter(uri=config.output_ws_uri)
