# adapters/input/stdin_input_adapter.py
import asyncio
import json
from .input_adapter import InputAdapter

class StdInInput(InputAdapter):
    def __init__(self, cmd: list, timeout: float = 5.0, max_retries=3, retry_delay=1.0):
        self.cmd = cmd
        self.timeout = timeout
        self.process = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.restart_attempts = 0

    async def start(self):
        await self._start_process_with_retries()

    async def _start_process_with_retries(self):
        for attempt in range(self.max_retries):
            try:
                self.process = await asyncio.create_subprocess_exec(
                    *self.cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                return
            except Exception:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    # Match the test's expectation for the error message
                    raise EOFError("Failed to start subprocess")

    async def read_message(self) -> dict:
        if not self.process or self.process.stdout is None:
            raise EOFError("No process or stdout available.")

        for attempt in range(self.max_retries):
            try:
                line = await asyncio.wait_for(self.process.stdout.readline(), timeout=self.timeout)
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise EOFError("Timed out waiting for input.")

            if not line:
                # If we get empty bytes, EOF reached. The test expects "EOF reached"
                raise EOFError("EOF reached")

            line_str = line.decode('utf-8').strip()
            if not line_str:
                # Empty line - treat as EOF for simplicity
                raise EOFError("EOF reached")

            try:
                msg = json.loads(line_str)
                return msg
            except json.JSONDecodeError:
                if attempt < self.max_retries - 1:
                    # Retry on invalid JSON
                    continue
                else:
                    raise EOFError("Invalid JSON received from subprocess.")

    async def stop(self):
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None

