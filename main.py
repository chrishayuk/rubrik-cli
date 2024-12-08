import argparse
import asyncio

# handlers
from chat_handler import ChatHandler

# response handlers
from response_handlers.llm_handler import LLMHandler
from response_handlers.human_handler import HumanHandler
from response_handlers.persona_handler import PersonaHandler
from response_handlers.forwarder_handler import ForwarderHandler

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

async def run_chat(args, message_queue):
    # Validate persona if needed
    if args.mode == "persona" and not args.persona:
        raise ValueError("--persona is required when --mode persona")

    # Choose responder handler based on mode
    if args.mode == "human":
        responder = HumanHandler()
    elif args.mode == "llm":
        responder = LLMHandler(provider=args.provider, model=args.model)
    elif args.mode == "forwarder":
        responder = ForwarderHandler()
    else:
        responder = PersonaHandler(persona_name=args.persona, provider=args.provider, model=args.model)

    # Choose input/output adapters based on server or client mode
    if args.server:
        # In server mode, read messages from message_queue (from external clients)
        input_adapter = ServerInputAdapter(message_queue)
        # Use ServerOutputAdapter to send responses back to clients
        output_adapter = ServerOutputAdapter(connected_clients)
    else:
        # Non-server (client) mode
        # Choose input adapter
        if args.input == "human":
            input_adapter = HumanInput()
        elif args.input == "stdin":
            if not args.cmd:
                raise ValueError("--cmd is required when --input=stdin")
            input_adapter = StdInInput(cmd=args.cmd)
        else:
            # websocket input (client mode)
            input_adapter = WebSocketInput(uri=args.input_ws_uri)

        # Choose output adapter
        if args.output == "human":
            output_adapter = HumanOutput()
        elif args.output == "stdout":
            output_adapter = StdOutOutput()
        else:  # websocket output (client mode)
            output_adapter = WebSocketDuplexAdapter(uri=args.output_ws_uri)

    handler = ChatHandler(
        input_adapter=input_adapter,
        output_adapter=output_adapter,
        mode=args.mode,
        provider=args.provider,
        model=args.model,
        persona=args.persona,
        stream=args.stream,
        server=args.server  # <--- IMPORTANT: Pass server flag here
    )

    await handler.run()


async def run_app(args):
    message_queue = asyncio.Queue()

    if args.server:
        # Run both server and chat concurrently
        await asyncio.gather(
            start_server(args.server_ws_uri, message_queue),
            run_chat(args, message_queue)
        )
    else:
        # Just run the handler (no server)
        await run_chat(args, message_queue)

def main():
    parser = argparse.ArgumentParser(description="Chat Handler Client")

    parser.add_argument("--mode", choices=["human", "llm", "persona", "forwarder"], default="human",
                        help="Mode of operation: 'human', 'llm', 'persona' or 'forwarder'")

    parser.add_argument("--provider", choices=["openai", "ollama"], default="ollama",
                        help="LLM provider")

    parser.add_argument("--model", default="llama3.3", help="Model name for the LLM")
    parser.add_argument("--persona", default=None, help="Persona name if mode=persona")
    parser.add_argument("--stream", action="store_true", help="Enable streaming")

    parser.add_argument("--input", choices=["human", "stdin", "websocket"], default="human",
                        help="Input source")
    parser.add_argument("--output", choices=["human", "stdout", "websocket"], default="human",
                        help="Output destination")

    parser.add_argument("--cmd", nargs='+', default=None, help="Command for stdin input")
    parser.add_argument("--input-ws-uri", default="ws://localhost:8000/ws", help="WebSocket URI for input")
    parser.add_argument("--output-ws-uri", default="ws://localhost:8000/ws", help="WebSocket URI for output")

    parser.add_argument("--server", action="store_true", help="Run as a server")
    parser.add_argument("--server-ws-uri", default="ws://localhost:9000", help="Server WebSocket URI")

    args = parser.parse_args()

    asyncio.run(run_app(args))

if __name__ == "__main__":
    main()
