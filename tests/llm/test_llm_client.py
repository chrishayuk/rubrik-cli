import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from src.llm.llm_client import LLMClient

@pytest.fixture
def mock_env_openai(monkeypatch):
    # Set up environment variables for openai
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

@pytest.fixture
def messages():
    return [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi, how can I help you today?"}
    ]

def test_init_openai_no_api_key(monkeypatch):
    # Unset API key if it's set
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is not set"):
        LLMClient(provider="openai", model="test-model")

def test_init_openai_with_api_key(mock_env_openai):
    client = LLMClient(provider="openai", model="gpt-4o-mini")
    assert client.provider == "openai"
    assert client.api_key == "test_key"
    assert client.model == "gpt-4o-mini"

def test_init_ollama_no_attr(mocker):
    # Simulate that ollama does not have a chat attribute
    mock_ollama = MagicMock()
    del mock_ollama.chat
    with patch("src.llm.llm_client.ollama", mock_ollama):
        with pytest.raises(ValueError, match="Ollama is not properly configured"):
            LLMClient(provider="ollama", model="some-model")

def test_init_ollama(mocker):
    # Simulate ollama having the chat attribute
    mock_ollama = MagicMock()
    mock_ollama.chat = MagicMock()
    with patch("src.llm.llm_client.ollama", mock_ollama):
        client = LLMClient(provider="ollama", model="some-model")
        assert client.provider == "ollama"

@pytest.mark.parametrize("provider", ["openai", "ollama"])
def test_create_completion(provider, mock_env_openai, mocker, messages):
    mock_response = {"response": "This is a test response", "tool_calls": []}

    if provider == "openai":
        # Mock OpenAI call
        mock_openai_completion = mocker.patch.object(
            LLMClient,
            "_openai_completion",
            return_value=mock_response
        )
        client = LLMClient(provider="openai", model="gpt-4o-mini")
        resp = client.create_completion(messages)
        assert resp == mock_response
        mock_openai_completion.assert_called_once_with(messages, None)
    else:
        # Mock Ollama call
        mock_ollama_completion = mocker.patch.object(
            LLMClient,
            "_ollama_completion",
            return_value=mock_response
        )
        # Need to also patch ollama since constructor checks for `ollama.chat` attribute
        mock_ollama = MagicMock()
        mock_ollama.chat = MagicMock()
        with patch("src.llm.llm_client.ollama", mock_ollama):
            client = LLMClient(provider="ollama", model="some-model")
            resp = client.create_completion(messages)
            assert resp == mock_response
            mock_ollama_completion.assert_called_once_with(messages, None)

def test_openai_completion_non_streaming(mock_env_openai, messages, mocker):
    # Mock the OpenAI class from openai package
    mock_openai_instance = MagicMock()
    mock_response = MagicMock()
    # structure: response.choices[0].message.content
    mock_choice_message = MagicMock(content="Test response", tool_calls=[])
    mock_choice = MagicMock(message=mock_choice_message)
    mock_response.choices = [mock_choice]
    mock_openai_instance.chat.completions.create.return_value = mock_response

    with patch("src.llm.llm_client.OpenAI", return_value=mock_openai_instance):
        client = LLMClient(provider="openai", model="test-model")
        response = client.create_completion(messages)
        assert response["response"] == "Test response"
        assert response["tool_calls"] == []

def test_openai_completion_error(mock_env_openai, messages, mocker):
    mock_openai_instance = MagicMock()
    mock_openai_instance.chat.completions.create.side_effect = Exception("API Error")

    with patch("src.llm.llm_client.OpenAI", return_value=mock_openai_instance):
        client = LLMClient(provider="openai", model="test-model")
        with pytest.raises(ValueError, match="OpenAI API Error: API Error"):
            client.create_completion(messages)

def test_openai_completion_stream(mock_env_openai, messages, mocker):
    # Simulate streaming responses
    # response is an iterator that yields partial chunks
    mock_stream_resp = [
        MagicMock(choices=[MagicMock(delta={"content": "Hello"})]),
        MagicMock(choices=[MagicMock(delta={"content": " world"})])
    ]

    mock_openai_instance = MagicMock()
    mock_openai_instance.chat.completions.create.return_value = iter(mock_stream_resp)

    with patch("src.llm.llm_client.OpenAI", return_value=mock_openai_instance):
        client = LLMClient(provider="openai", model="test-model")
        stream = client.create_completion_stream(messages)
        streamed_text = "".join(list(stream))
        assert streamed_text == "Hello world"

def test_ollama_completion_non_streaming(mocker, messages):
    # Mock ollama
    mock_ollama = MagicMock()
    # ollama.chat returns a response with a 'message' attribute that has 'content'
    mock_message = MagicMock(content="Ollama test response", tool_calls=None)
    mock_response = MagicMock(message=mock_message)
    mock_ollama.chat.return_value = mock_response

    with patch("src.llm.llm_client.ollama", mock_ollama):
        client = LLMClient(provider="ollama", model="test-model")
        response = client.create_completion(messages)
        assert response["response"] == "Ollama test response"
        assert response["tool_calls"] == []

def test_ollama_completion_error(mocker, messages):
    mock_ollama = MagicMock()
    mock_ollama.chat.side_effect = Exception("Ollama Error")

    with patch("src.llm.llm_client.ollama", mock_ollama):
        client = LLMClient(provider="ollama", model="test-model")
        with pytest.raises(ValueError, match="Ollama API Error: Ollama Error"):
            client.create_completion(messages)

def test_ollama_completion_stream(mocker, messages):
    mock_ollama = MagicMock()
    # ollama.chat with stream=True returns an iterator
    mock_ollama.chat.return_value = iter(["Ollama", " ", "stream", " response"])
    with patch("src.llm.llm_client.ollama", mock_ollama):
        client = LLMClient(provider="ollama", model="test-model")
        stream = client.create_completion_stream(messages)
        streamed_text = "".join(list(stream))
        assert streamed_text == "Ollama stream response"
