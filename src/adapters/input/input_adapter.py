# adapters/input/input_adapter.py
class InputAdapter:
    async def start(self):
        pass

    async def read_message(self) -> dict:
        raise NotImplementedError("read_message must be implemented.")

    async def stop(self):
        pass