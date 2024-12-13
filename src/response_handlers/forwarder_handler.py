# response_handlers/forwarder_handler.py

class ForwarderHandler:
    def get_response(self, question: str, conversation: list) -> str:
        # Just return the question unchanged.
        # This makes the server act as a forwarder: it takes input and outputs it verbatim.
        return question

    def get_response_stream(self, question: str, conversation: list):
        # If you're using streaming mode, this method should yield tokens.
        # For forwarding, we can just yield the entire question as one token,
        # or just yield once and return.
        yield question
