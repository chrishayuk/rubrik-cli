from llm_client import LLMClient

class LLMHandler:
    def __init__(self, provider: str = "ollama", model: str = "llama3.3"):
        # setup the llm client
        self.llm_client = LLMClient(provider=provider, model=model)

    def get_response(self, question: str, conversation: list) -> str:
        """
        Given the conversation and the latest question, call the LLM to generate a response.
        
        conversation is a list of messages in the format:
        [{"role": "questioner"/"responder"/"verifier", "content": "..."}]

        We need to convert these roles into a format understood by the LLMClient:
        - questioner -> user
        - responder -> assistant
        - verifier -> system (or user, depending on your design)
        """
        transformed_messages = []
        for msg in conversation:
            if msg["role"] == "questioner":
                r = "user"
            elif msg["role"] == "responder":
                r = "assistant"
            else:
                r = "system"  # For verifier, treat as system message
            transformed_messages.append({"role": r, "content": msg["content"]})

        response_data = self.llm_client.create_completion(transformed_messages)
        return response_data["response"]
