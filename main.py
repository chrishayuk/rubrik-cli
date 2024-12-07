import argparse
import asyncio
from chat_handler import ChatHandler

def main():
    # setup the parser
    parser = argparse.ArgumentParser(description="Chat Handler Client")

    # check if the mode is human or llm
    parser.add_argument("--mode", choices=["human", "llm"], default="human",
                        help="Mode of operation: 'human' for manual input, 'llm' for automated LLM responses")
    
    # get the provider
    parser.add_argument("--provider", choices=["openai", "ollama"], default="ollama",
                        help="LLM provider: 'openai' or 'ollama'")
    
    # get the model
    parser.add_argument("--model", default="llama3.3", help="Model name for the LLM")
    
    # parse arguments
    args = parser.parse_args()

    # setup the chat handler
    handler = ChatHandler(mode=args.mode, provider=args.provider, model=args.model)

    # kick off
    asyncio.run(handler.run())

if __name__ == "__main__":
    main()
