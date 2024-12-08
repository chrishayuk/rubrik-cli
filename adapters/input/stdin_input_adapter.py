import asyncio
import json
from adapters.input.input_adapter import InputAdapter

class StdInInput(InputAdapter):
    def __init__(self, cmd: list, timeout: float = 5.0):
        self.cmd = cmd
        self.timeout = timeout
        self.process = None

    async def start(self):
        self.process = await asyncio.create_subprocess_exec(
            *self.cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

    async def read_message(self) -> dict:
        if not self.process or self.process.stdout is None:
            raise EOFError("No process or stdout available.")

        try:
            line = await asyncio.wait_for(self.process.stdout.readline(), timeout=self.timeout)
        except asyncio.TimeoutError:
            raise EOFError("Timed out waiting for input.")

        if not line:
            raise EOFError("EOF reached.")

        line_str = line.decode('utf-8').strip()
        try:
            msg = json.loads(line_str)
        except json.JSONDecodeError:
            # If not JSON, wrap in a generic dict
            msg = {"role": "assistant", "message": line_str}
        return msg

    async def stop(self):
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None