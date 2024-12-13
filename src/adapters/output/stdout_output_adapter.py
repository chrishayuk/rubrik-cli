# adapters/output/stdout_output_adapter.py
import json
import sys
from .output_adapter import OutputAdapter

class StdOutOutput(OutputAdapter):
    async def start(self):
        pass

    async def write_message(self, data: dict):
        # convert the dictionary to a JSON string and write it to stdout
        try:
            message_str = json.dumps(data) + "\n"
        except (TypeError, ValueError) as e:
            # If data cannot be serialized, raise an EOFError for consistency
            raise EOFError(f"Unable to serialize data: {e}")

        try:
            sys.stdout.write(message_str)
            sys.stdout.flush()
        except Exception as e:
            raise EOFError(f"Failed to write to stdout: {e}")

    async def stop(self):
        pass
