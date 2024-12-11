# adapters/output/human_output_adapter.py
from adapters.output.output_adapter import OutputAdapter

class HumanOutput(OutputAdapter):
    def __init__(self, renderer=None):
        """
        Optionally accept a renderer callable that handles the display of the message data.
        If no renderer is provided, it will just print the role and message in plain text.
        """
        self.renderer = renderer if renderer is not None else self._default_renderer

    async def start(self):
        # Nothing to do when starting
        pass

    async def write_message(self, data: dict):
        # Delegate to the renderer for displaying the message
        self.renderer(data)

    async def stop(self):
        # Nothing to do when stopping
        pass

    def _default_renderer(self, data: dict):
        # A simple fallback that prints role and message in plain text
        role = data.get("role", "Unknown")
        message = data.get("message", "")
        print(f"{role}: {message}")
