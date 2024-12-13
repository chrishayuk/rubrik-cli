import pytest
from src.chat_handler.conversation_manager import ConversationManager

def test_conversation_starts_empty():
    manager = ConversationManager()
    assert manager.get_conversation() == [], "Conversation should start empty"

def test_add_message_lowercase_role():
    manager = ConversationManager()
    manager.add_message("USER", "Hello!")
    convo = manager.get_conversation()

    assert len(convo) == 1, "Conversation should have one message"
    assert convo[0]["role"] == "user", "Role should be lowercase"
    assert convo[0]["content"] == "Hello!", "Content should match the added message"

def test_add_multiple_messages():
    manager = ConversationManager()
    manager.add_message("user", "First message")
    manager.add_message("assistant", "Response to first message")
    manager.add_message("USER", "Another user message")

    convo = manager.get_conversation()
    assert len(convo) == 3, "Should have three messages in the conversation"
    assert convo[0]["role"] == "user" and convo[0]["content"] == "First message"
    assert convo[1]["role"] == "assistant" and convo[1]["content"] == "Response to first message"
    assert convo[2]["role"] == "user" and convo[2]["content"] == "Another user message"
