from adapters.input.input_adapter import InputAdapter

class HumanInput(InputAdapter):
    async def read_message(self) -> dict:
        # Prompt a human user for the next message
        # The user message is considered as a "Questioner"
        content = input("User: ")
        return {"role": "Questioner", "message": content}