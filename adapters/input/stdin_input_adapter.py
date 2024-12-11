# adapters/input/stdin_input_adapter.py
import asyncio
import json
from adapters.input.input_adapter import InputAdapter

class StdInInput(InputAdapter):
    def __init__(self, cmd: list, timeout: float = 5.0):
        self.cmd = cmd
        self.timeout = timeout
        self.process = None

    async def start(self):
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except Exception as e:
            # If process fails to start
            raise EOFError(f"Failed to start subprocess: {e}")

    async def read_message(self) -> dict:
        if not self.process or self.process.stdout is None:
            raise EOFError("No process or stdout available.")

        try:
            line = await asyncio.wait_for(self.process.stdout.readline(), timeout=self.timeout)
        except asyncio.TimeoutError:
            raise EOFError("Timed out waiting for input.")

        if not line:
            # EOF reached from the subprocess
            raise EOFError("EOF reached.")

        line_str = line.decode('utf-8').strip()
        if not line_str:
            # Empty line, treat as EOF or just retry?
            # Here we consider empty line as EOF for simplicity
            raise EOFError("EOF reached (empty line).")

        try:
            msg = json.loads(line_str)
        except json.JSONDecodeError:
            raise EOFError("Invalid JSON received from subprocess.")

        return msg

    async def stop(self):
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
