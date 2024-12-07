import os
import uuid
import ollama
from openai import OpenAI
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List, Generator

# Load environment variables
load_dotenv()

class LLMClient:
    def __init__(self, provider="openai", model="gpt-4o-mini", api_key=None):
        # set the provider, model and api key
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        # ensure we have the api key for openai if set
        if self.provider == "openai" and not self.api_key:
            raise ValueError("The OPENAI_API_KEY environment variable is not set.")
        
        # check ollama is good
        if self.provider == "ollama" and not hasattr(ollama, "chat"):
            raise ValueError("Ollama is not properly configured in this environment.")

    def create_completion(self, messages: List[Dict], tools: List = None) -> Dict[str, Any]:
        """Create a chat completion using the specified LLM provider (non-streaming)."""
        if self.provider == "openai":
            return self._openai_completion(messages, tools)
        elif self.provider == "ollama":
            return self._ollama_completion(messages, tools)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def create_completion_stream(self, messages: List[Dict], tools: List = None) -> Generator[str, None, None]:
        """
        Create a chat completion in streaming mode. Yields tokens or partial responses as they arrive.
        
        Example usage:
            for token in llm_client.create_completion_stream(messages):
                print(token, end="", flush=True)
        """
        if self.provider == "openai":
            yield from self._openai_completion_stream(messages, tools)
        elif self.provider == "ollama":
            yield from self._ollama_completion_stream(messages, tools)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _openai_completion(self, messages: List[Dict], tools: List) -> Dict[str, Any]:
        """Handle OpenAI chat completions (non-streaming)."""
        client = OpenAI(api_key=self.api_key)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools or [],
            )
            return {
                "response": response.choices[0].message.content,
                "tool_calls": getattr(response.choices[0].message, "tool_calls", []),
            }
        except Exception as e:
            logging.error(f"OpenAI API Error: {str(e)}")
            raise ValueError(f"OpenAI API Error: {str(e)}")

    def _openai_completion_stream(self, messages: List[Dict], tools: List) -> Generator[str, None, None]:
        """Handle OpenAI chat completions (streaming)."""
        client = OpenAI(api_key=self.api_key)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools or [],
                stream=True
            )
            # OpenAI's Python client returns a generator for streamed responses
            for partial in response:
                if partial.choices and partial.choices[0].delta and 'content' in partial.choices[0].delta:
                    yield partial.choices[0].delta.content
        except Exception as e:
            logging.error(f"OpenAI API Error (stream): {str(e)}")
            raise ValueError(f"OpenAI API Error: {str(e)}")

    def _ollama_completion(self, messages: List[Dict], tools: List) -> Dict[str, Any]:
        """Handle Ollama chat completions (non-streaming)."""
        ollama_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

        try:
            response = ollama.chat(
                model=self.model,
                messages=ollama_messages,
                stream=False,
                tools=tools or []
            )

            logging.info(f"Ollama raw response: {response}")

            message = response.message
            tool_calls = []
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool in message.tool_calls:
                    tool_calls.append({
                        "id": str(uuid.uuid4()),
                        "type": "function",
                        "function": {
                            "name": tool.function.name,
                            "arguments": tool.function.arguments
                        }
                    })
            return {
                "response": message.content if message else "No response",
                "tool_calls": tool_calls
            }

        except Exception as e:
            logging.error(f"Ollama API Error: {str(e)}")
            raise ValueError(f"Ollama API Error: {str(e)}")

    def _ollama_completion_stream(self, messages: List[Dict], tools: List) -> Generator[str, None, None]:
        """Handle Ollama chat completions (streaming)."""
        ollama_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]

        try:
            # Ollama can stream responses token-by-token.
            # Assume ollama.chat with stream=True returns a generator that yields tokens or chunks.
            for partial in ollama.chat(
                model=self.model,
                messages=ollama_messages,
                stream=True,
                tools=tools or []
            ):
                # partial might be a string or an object with a token attribute
                # If partial is a simple string token:
                yield partial

        except Exception as e:
            logging.error(f"Ollama API Error (stream): {str(e)}")
            raise ValueError(f"Ollama API Error: {str(e)}")
