# llm_handler.py
from typing import List, Dict
from llm.llm_client import LLMClient

class LLMHandler:
    def __init__(self, provider: str, model: str, system_prompt: str = None):
        # set the provider, model and system prompt
        self.provider = provider
        self.model = model
        self.system_prompt = system_prompt

        # set the llm client
        self.llm_client = LLMClient(provider=provider, model=model)

    def _build_messages(self, question: str, conversation: List[Dict]) -> List[Dict]:
        # clear messages
        msgs = []

        # If a system prompt is set, add it as the first message
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})

        # Convert internal conversation format to LLM messages
        for msg in conversation:
            role = "system"
            if msg["role"] == "questioner":
                role = "user"
            elif msg["role"] == "responder":
                role = "assistant"
            msgs.append({"role": role, "content": msg["content"]})

        # Add the new user question
        msgs.append({"role": "user", "content": question})

        # return messages
        return msgs

    def get_response(self, question: str, conversation: List[Dict]) -> str:
        # build messages
        messages = self._build_messages(question, conversation)

        # call create completion on the llm
        result = self.llm_client.create_completion(messages)

        # return the response
        return result["response"]

    def get_response_stream(self, question: str, conversation: List[Dict]):
        # build messages
        messages = self._build_messages(question, conversation)

        # stream the response
        for token in self.llm_client.create_completion_stream(messages):
            # get the response chunk
            text = token.message.content if hasattr(token, 'message') and token.message and token.message.content else ""

            # yield it back
            yield text
