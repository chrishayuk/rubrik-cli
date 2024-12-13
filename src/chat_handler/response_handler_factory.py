from response_handlers.human_handler import HumanHandler
from response_handlers.llm_handler import LLMHandler
from response_handlers.persona_handler import PersonaHandler
from response_handlers.forwarder_handler import ForwarderHandler

def create_response_handler(mode: str, provider: str, model: str, persona: str = None):
    if mode == "human":
        return HumanHandler(), "Human"
    elif mode == "llm":
        return LLMHandler(provider=provider, model=model), f"LLM ({provider}/{model})"
    elif mode == "persona":
        if not persona:
            raise ValueError("persona is required when mode=persona")
        return PersonaHandler(persona_name=persona, provider=provider, model=model), f"Persona ({persona}, {provider}/{model})"
    elif mode == "forwarder":
        return ForwarderHandler(), "forwarder"
    else:
        raise ValueError(f"Unknown mode: {mode}")
