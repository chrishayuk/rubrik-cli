# chat_handler/conversation_manager.py
class ConversationManager:
    """
    Manages the state of the conversation between the user and the responder.
    It stores a list of messages, each represented as a dictionary with 'role' and 'content'.
    """

    def __init__(self):
        self.conversation = []

    def add_message(self, role: str, content: str):
        """Add a new message to the conversation."""
        self.conversation.append({"role": role.lower(), "content": content})

    def get_conversation(self):
        """Return the entire conversation as a list of message dictionaries."""
        return self.conversation
