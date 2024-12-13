# argparser.py
import argparse
from typing import Optional, List

class Config:
    """Configuration object to store command line arguments."""
    def __init__(self, args: argparse.Namespace):
        self.mode = args.mode
        self.provider = args.provider
        self.model = args.model
        self.persona = args.persona
        self.stream = args.stream
        self.input_type = args.input
        self.output_type = args.output
        self.cmd = args.cmd
        self.input_ws_uri = args.input_ws_uri
        self.output_ws_uri = args.output_ws_uri
        self.server = args.server
        self.server_ws_uri = args.server_ws_uri

def parse_args(argv: Optional[List[str]] = None) -> Config:
    """
    Parse command line arguments and return a Config object.
    
    :param argv: Optional list of arguments (for testing or custom invocation).
    :return: A Config object populated with the parsed arguments.
    """
    # setup the parser
    parser = argparse.ArgumentParser(description="Chat Handler Client")
    
    # add the arguments
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

    # parse arguments
    args = parser.parse_args(argv)

    # return the config
    return Config(args)
