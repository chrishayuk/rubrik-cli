# response_handlers/persona_handler.py
import json
import os
from response_handlers.llm_handler import LLMHandler

class PersonaHandler(LLMHandler):
    def __init__(self, persona_name: str, provider: str = "ollama", model: str = "llama3.3"):
        # set persona name and system prompt
        self.persona_name = persona_name
        self.system_prompt = self.load_system_prompt()

        # Initialize LLMHandler with the system prompt
        super().__init__(provider=provider, model=model, system_prompt=self.system_prompt)


    def load_system_prompt(self) -> str:
        """Load the system prompt from personas.json based on the persona name."""
        json_file = os.path.join(os.path.dirname(__file__), "../../personas.json")

        # check we have a personas json
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"personas.json not found at {json_file}")

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # check we found a persona
        if self.persona_name not in data:
            raise ValueError(f"No system prompt found for persona '{self.persona_name}'.")
        
        # set the system prompt
        return data[self.persona_name]["system_prompt"]