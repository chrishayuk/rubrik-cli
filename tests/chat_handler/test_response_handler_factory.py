import pytest
from src.response_handlers.human_handler import HumanHandler
from src.response_handlers.llm_handler import LLMHandler
from src.response_handlers.persona_handler import PersonaHandler
from src.response_handlers.forwarder_handler import ForwarderHandler
from src.response_handlers.response_handler_factory import create_response_handler

def test_create_response_handler_human():
    handler, description = create_response_handler(mode="human", provider="openai", model="test-model")
    assert isinstance(handler, HumanHandler)
    assert description == "Human"

def test_create_response_handler_llm():
    handler, description = create_response_handler(mode="llm", provider="openai", model="gpt-4")
    assert isinstance(handler, LLMHandler)
    assert description == "LLM (openai/gpt-4)"
    # Optionally, check internal attributes if desired:
    assert handler.provider == "openai"
    assert handler.model == "gpt-4"

def test_create_response_handler_persona():
    handler, description = create_response_handler(mode="persona", provider="ollama", model="llama3.3", persona="helpful_persona")
    assert isinstance(handler, PersonaHandler)
    assert description == "Persona (helpful_persona, ollama/llama3.3)"
    # Check internal attributes
    assert handler.persona_name == "helpful_persona"
    assert handler.provider == "ollama"
    assert handler.model == "llama3.3"

def test_create_response_handler_persona_missing_persona():
    with pytest.raises(ValueError, match="persona is required when mode=persona"):
        create_response_handler(mode="persona", provider="openai", model="test-model")

def test_create_response_handler_forwarder():
    handler, description = create_response_handler(mode="forwarder", provider="openai", model="gpt-4")
    assert isinstance(handler, ForwarderHandler)
    assert description == "forwarder"

def test_create_response_handler_unknown_mode():
    with pytest.raises(ValueError, match="Unknown mode: random"):
        create_response_handler(mode="random", provider="openai", model="test-model")
