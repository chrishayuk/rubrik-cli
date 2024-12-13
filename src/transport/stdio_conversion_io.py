# transport/stdio_conversation_io.py
import json
import asyncio
import subprocess
from typing import Dict, Any
from conversation_io import ConversationIO, ConversationEndedError

class StdioConversationIO(ConversationIO):
    def __init__(self, cmd: list, timeout: float = 5.0):
        """
        cmd: command to run as the buddy process, e.g. ["python", "buddy_script.py"]
        timeout: how long to wait for a response before giving up
        """
        self.cmd = cmd
        self.timeout = timeout
        self.process = None

    async def start_conversation(self):
        # Start the process
        self.process = await asyncio.create_subprocess_exec(
            *self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    async def listen(self) -> Dict[str, Any]:
        # Try to read one line from the process's stdout
        # If your buddy prints a single JSON message or a single line per response,
        # you may need a protocol to define how messages are delimited.
        
        # Example: Buddy prints one JSON per line.
        if not self.process or self.process.stdout is None:
            raise ConversationEndedError("Process not started or no stdout.")

        try:
            line = await asyncio.wait_for(self.process.stdout.readline(), timeout=self.timeout)
        except asyncio.TimeoutError:
            # If no output in time, consider conversation ended or return empty
            raise ConversationEndedError("No response from buddy within timeout.")

        if not line:
            # EOF reached
            raise ConversationEndedError("Buddy closed the conversation.")

        # Decode and strip line
        line_str = line.decode('utf-8').strip()

        # Suppose the buddy returns JSON lines
        # If it's plain text, wrap it in a dict
        import json
        try:
            msg = json.loads(line_str)
        except json.JSONDecodeError:
            # If not JSON, just return a simple dict
            msg = {"role": "assistant", "message": line_str}

        return msg

    async def respond(self, data: Dict[str, Any]):
        # Write a line to the subprocess stdin
        if not self.process or self.process.stdin is None:
            raise ConversationEndedError("Process not started or no stdin available.")

        # Convert data to JSON or a line of text depending on your buddy's protocol
        line = json.dumps(data) + "\n"

        # Write line to stdin
        self.process.stdin.write(line.encode('utf-8'))

        # Flush the output buffer
        await self.process.stdin.drain()

    async def end_conversation(self):
        # Terminate the subprocess and wait for it to exit
        if self.process:
            # Send a signal to the subprocess
            self.process.terminate()

            # Wait for the process to terminate
            await self.process.wait()

            # clean up
            self.process = None
