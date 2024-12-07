# transport/conversation_io.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class ConversationEndedError(Exception):
    """Raised when the conversation unexpectedly ends or no more messages are available."""
    pass

class ConversationIO(ABC):
    @abstractmethod
    async def start_conversation(self):
        """Begin the interaction with the conversation source."""
        pass

    @abstractmethod
    async def listen(self) -> Dict[str, Any]:
        """
        Wait and listen for the next message in the conversation.
        If the conversation ends, raise ConversationEndedError.
        """
        pass

    @abstractmethod
    async def respond(self, data: Dict[str, Any]):
        """Send a response to the conversation partner."""
        pass

    @abstractmethod
    async def end_conversation(self):
        """Gracefully end the conversation."""
        pass
