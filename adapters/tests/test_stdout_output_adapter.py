import pytest
import sys
import json
from unittest.mock import MagicMock, patch
from adapters.output.stdout_output_adapter import StdOutOutput

@pytest.mark.asyncio
async def test_stdout_output_write_message():
    adapter = StdOutOutput()

    # Prepare a mock for sys.stdout
    mock_stdout = MagicMock()
    with patch.object(sys, 'stdout', mock_stdout):
        data = {"role": "Responder", "message": "Hello!"}
        await adapter.write_message(data)

        # The adapter writes JSON + newline
        expected_output = json.dumps(data) + "\n"

        # Check that sys.stdout.write() was called with the expected output
        mock_stdout.write.assert_called_once_with(expected_output)

        # Check that sys.stdout.flush() was called
        mock_stdout.flush.assert_called_once()

@pytest.mark.asyncio
async def test_stdout_output_start():
    adapter = StdOutOutput()
    # start does nothing, should not raise an exception
    await adapter.start()

@pytest.mark.asyncio
async def test_stdout_output_stop():
    adapter = StdOutOutput()
    # stop does nothing, should not raise an exception
    await adapter.stop()
