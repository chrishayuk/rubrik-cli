# adapters/output/output_adapter.py
class OutputAdapter:
    async def start(self):
        # Not implemented yet
        pass

    async def write_message(self, data: dict):
        # Not implemented yet
        raise NotImplementedError("write_message must be implemented.")

    async def stop(self):
        # Not implemented yet
        pass
