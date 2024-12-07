import argparse
import asyncio
import logging

# handlers
from chat_handler import ChatHandler

# input adapters
from adapters.input.human_input_adapter import HumanInput
from adapters.input.server_input_adapter import ServerInputAdapter
from adapters.input.stdin_input_adapter import StdInInput
from adapters.input.websocket_input_adapter import WebSocketInput

# output adapters
from adapters.output.human_output_adapter import HumanOutput
from adapters.output.server_output_adapter import ServerOutputAdapter
from adapters.output.stdout_output_adapter import StdOutOutput
from adapters.output.websocket_output_adapter import WebSocketOutput

# duplex adapter
from adapters.websocket_duplex_adapter import WebSocketDuplexAdapter

# server
from ws_server import start_server, connected_clients

# set the logger
logger = logging.getLogger(__name__)

# Set up logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.CRITICAL  # Adjust log level as needed
)

async def run_chat(args, message_queue):
    # Validate persona if needed
    if args.mode == "persona" and not args.persona:
        raise ValueError("--persona is required when --mode persona")

    # Choose input/output adapters based on server or client mode
    if args.server:
        # In server mode, read messages from message_queue (from external clients)
        input_adapter = ServerInputAdapter(message_queue)

        # If output=websocket and output-ws-uri provided, use WebSocketOutput
        # otherwise use ServerOutputAdapter
        if args.output == "websocket" and args.output_ws_uri:
            # output to websocket
            output_adapter = WebSocketOutput(uri=args.output_ws_uri)
        else:
            # output to server
            output_adapter = ServerOutputAdapter(connected_clients)
    else:
        # Non-server (client) mode
        # Choose input adapter
        if args.input == "human":
            # input from human
            input_adapter = HumanInput()
        elif args.input == "stdin":
            if not args.cmd:
                raise ValueError("--cmd is required when --input=stdin")
            # input from stdin
            input_adapter = StdInInput(cmd=args.cmd)
        else:
            # WebSocket input (client mode)
            input_adapter = WebSocketInput(uri=args.input_ws_uri)

        # Choose output adapter
        if args.output == "human":
            # output to human
            output_adapter = HumanOutput()
        elif args.output == "stdout":
            # output to stdout
            output_adapter = StdOutOutput()
        else:  # websocket output (client mode)
            # output to websocket
            output_adapter = WebSocketDuplexAdapter(uri=args.output_ws_uri)

    # Initialize the ChatHandler
    handler = ChatHandler(
        input_adapter=input_adapter,
        output_adapter=output_adapter,
        mode=args.mode,
        provider=args.provider,
        model=args.model,
        persona=args.persona,
        stream=args.stream,
        server=args.server
    )

    # start the handler
    await handler.run()


async def run_app(args):
    # setup the message queue
    message_queue = asyncio.Queue()

    if args.server:
        # Run both server and chat concurrently
        await asyncio.gather(
            # start server
            start_server(args.server_ws_uri, message_queue),

            # run chat
            run_chat(args, message_queue)
        )
    else:
        # Just run the handler (no server)
        await run_chat(args, message_queue)


def main():
    # setup the parser
    parser = argparse.ArgumentParser(description="Chat Handler Client")

    # parser arguments
    parser.add_argument("--mode", choices=["human", "llm", "persona", "forwarder"], default="human", help="Mode of operation: 'human', 'llm', 'persona' or 'forwarder'")
    parser.add_argument("--provider", choices=["openai", "ollama"], default="ollama", help="LLM provider")
    parser.add_argument("--model", default="llama3.3", help="Model name for the LLM")
    parser.add_argument("--persona", default=None, help="Persona name if mode=persona")
    parser.add_argument("--stream", action="store_true", help="Enable streaming")
    parser.add_argument("--input", choices=["human", "stdin", "websocket"], default="human", help="Input source")
    parser.add_argument("--output", choices=["human", "stdout", "websocket"], default="human", help="Output destination")
    parser.add_argument("--cmd", nargs='+', default=None, help="Command for stdin input")
    parser.add_argument("--input-ws-uri", default="ws://localhost:8000/ws", help="WebSocket URI for input")
    parser.add_argument("--output-ws-uri", default="ws://localhost:8000/ws", help="WebSocket URI for output")
    parser.add_argument("--server", action="store_true", help="Run as a server")
    parser.add_argument("--server-ws-uri", default="ws://localhost:9000", help="Server WebSocket URI")

    # parse
    args = parser.parse_args()

    # run the app
    asyncio.run(run_app(args))


if __name__ == "__main__":
    # kick of main
    main()
