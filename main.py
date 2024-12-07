import argparse
import asyncio
from chat_handler import ChatHandler
from transport.websocket_conversation_io import WebSocketConversationIO

def main():
    # setup the parser
    parser = argparse.ArgumentParser(description="Chat Handler Client")

    # now we support human, llm, and persona modes
    parser.add_argument("--mode", choices=["human", "llm", "persona"], default="human",
                        help="Mode of operation: 'human', 'llm', or 'persona'")

    # get the provider
    parser.add_argument("--provider", choices=["openai", "ollama"], default="ollama",
                        help="LLM provider: 'openai' or 'ollama'")

    # get the model
    parser.add_argument("--model", default="llama3.3", help="Model name for the LLM")

    # persona name (required if mode is persona)
    parser.add_argument("--persona", default=None, help="Name of the persona (required if mode is 'persona')")

    # stream flag
    parser.add_argument("--stream", action="store_true", help="Enable streaming mode for responses")

    # parse arguments
    args = parser.parse_args()

    # if persona mode is chosen, ensure persona is provided
    if args.mode == "persona" and not args.persona:
        parser.error("--persona is required when --mode persona")

    # create an instance of the conversation IO
    conversation_io = WebSocketConversationIO(uri="ws://localhost:8000/ws")

    # setup the chat handler with an instance
    handler = ChatHandler(
        conversation_io=conversation_io,
        mode=args.mode,
        provider=args.provider,
        model=args.model,
        persona=args.persona,
        stream=args.stream  # pass the stream flag
    )

    # kick off
    asyncio.run(handler.run())

if __name__ == "__main__":
    main()
