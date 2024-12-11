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
from adapters.duplex.websocket_duplex_adapter import WebSocketDuplexAdapter

# server
from ws_server import start_server, connected_clients

# UI renderer for human output
from rich_renderer import RichRenderer

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.CRITICAL
)

async def run_chat(args, message_queue):
    if args.mode == "persona" and not args.persona:
        raise ValueError("--persona is required when --mode persona")

    if args.server:
        # Server mode
        input_adapter = ServerInputAdapter(message_queue)

        if args.output == "websocket" and args.output_ws_uri:
            output_adapter = WebSocketOutput(uri=args.output_ws_uri)
        else:
            output_adapter = ServerOutputAdapter(connected_clients)
    else:
        # Client mode
        if args.input == "human":
            input_adapter = HumanInput()
        elif args.input == "stdin":
            if not args.cmd:
                raise ValueError("--cmd is required when --input=stdin")
            input_adapter = StdInInput(cmd=args.cmd)
        else:  # websocket input
            input_adapter = WebSocketInput(uri=args.input_ws_uri)

        if args.output == "human":
            # Integrate the Rich-based renderer
            output_adapter = HumanOutput(renderer=RichRenderer)
        elif args.output == "stdout":
            output_adapter = StdOutOutput()
        else:  # websocket output
            output_adapter = WebSocketDuplexAdapter(uri=args.output_ws_uri)

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

    await handler.run()

async def run_app(args):
    message_queue = asyncio.Queue()

    if args.server:
        await asyncio.gather(
            start_server(args.server_ws_uri, message_queue),
            run_chat(args, message_queue)
        )
    else:
        await run_chat(args, message_queue)

def main():
    parser = argparse.ArgumentParser(description="Chat Handler Client")
    parser.add_argument("--mode", choices=["human", "llm", "persona", "forwarder"], default="human")
    parser.add_argument("--provider", choices=["openai", "ollama"], default="ollama")
    parser.add_argument("--model", default="llama3.3")
    parser.add_argument("--persona", default=None)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--input", choices=["human", "stdin", "websocket"], default="human")
    parser.add_argument("--output", choices=["human", "stdout", "websocket"], default="human")
    parser.add_argument("--cmd", nargs='+', default=None)
    parser.add_argument("--input-ws-uri", default="ws://localhost:8000/ws")
    parser.add_argument("--output-ws-uri", default="ws://localhost:8000/ws")
    parser.add_argument("--server", action="store_true")
    parser.add_argument("--server-ws-uri", default="ws://localhost:9000")

    args = parser.parse_args()
    asyncio.run(run_app(args))

if __name__ == "__main__":
    main()
