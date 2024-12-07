import json
import os
from llm_client import LLMClient

class PersonaHandler:
    def __init__(self, persona_name: str, provider: str = "ollama", model: str = "llama3.3"):
        self.provider = provider
        self.model = model
        self.persona_name = persona_name
        self.llm_client = LLMClient(provider=self.provider, model=self.model)
        self.system_prompt = self.load_system_prompt()

    def load_system_prompt(self) -> str:
        """Load the system prompt from personas.json based on the persona name."""

        # load the personas json file
        json_file = os.path.join(os.path.dirname(__file__), "personas.json")
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"personas.json not found at {json_file}")

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # get the person
        if self.persona_name not in data:
            raise ValueError(f"No system prompt found for persona '{self.persona_name}'.")
        
        # set the system prompt for the persona
        return data[self.persona_name]["system_prompt"]

    def get_response(self, question: str, conversation: list) -> str:
        """
        Given the conversation and the latest question, call the LLM to generate a response.
        Insert a system message at the start using the system prompt to set the persona.
        """
        transformed_messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        for msg in conversation:
            if msg["role"] == "questioner":
                r = "user"
            elif msg["role"] == "responder":
                r = "assistant"
            else:
                r = "system"
            transformed_messages.append({"role": r, "content": msg["content"]})

        response_data = self.llm_client.create_completion(transformed_messages)
        return response_data["response"]
