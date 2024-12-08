# adapters/output/stdout_output_adapter.py
import json
import sys
from adapters.output.output_adapter import OutputAdapter


class StdOutOutput(OutputAdapter):
    async def write_message(self, data: dict):
        # convert the dictionary to a JSON string and write it to stdout
        sys.stdout.write(json.dumps(data) + "\n")

        # flush the output buffer to ensure that the message is immediately displayed
        sys.stdout.flush()