# tests/test_messages.py
import pytest
from pydantic import ValidationError
from src.messages.message_types import ChatMessage, HealthCheckMessage, MessageRole, MessageType

def test_chat_message_non_partial():
    msg = ChatMessage(role=MessageRole.RESPONDER, message="Hello", partial=False)
    assert msg.message == "Hello"
    assert msg.partial == False

def test_chat_message_non_partial_empty_message_raises():
    with pytest.raises(ValidationError):
        ChatMessage(role=MessageRole.QUESTIONER, message="", partial=False)

def test_chat_message_partial_empty_is_ok():
    # Allowed if we define partial messages as separate, or just partial=True in ChatMessage
    msg = ChatMessage(role=MessageRole.RESPONDER, message="", partial=True)
    assert msg.partial == True
    # message can be empty since partial=True

def test_health_check_message():
    msg = HealthCheckMessage(role=MessageRole.SERVER, type=MessageType.HEALTHCHECK)
    # No message needed
    assert msg.type == MessageType.HEALTHCHECK
