import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.adapters.input.stdin_input_adapter import StdInInput
import json

@pytest.mark.asyncio
async def test_stdin_input_adapter_start_success():
    mock_process = AsyncMock()
    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        adapter = StdInInput(["echo", '{"role":"Questioner","message":"hello"}'])
        await adapter.start()
        assert adapter.process == mock_process

@pytest.mark.asyncio
async def test_stdin_input_adapter_start_failure():
    with patch("asyncio.create_subprocess_exec", side_effect=Exception("Failed")):
        adapter = StdInInput(["nonexistent_command"])
        with pytest.raises(EOFError, match="Failed to start subprocess"):
            await adapter.start()

@pytest.mark.asyncio
async def test_stdin_input_adapter_read_message_valid():
    mock_process = AsyncMock()
    mock_process.stdout.readline = AsyncMock(return_value=b'{"role":"Questioner","message":"hello"}\n')

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        adapter = StdInInput(["echo", '{"role":"Questioner","message":"hello"}'])
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "hello"}

@pytest.mark.asyncio
async def test_stdin_input_adapter_read_message_invalid_json():
    mock_process = AsyncMock()
    mock_process.stdout.readline = AsyncMock(return_value=b'Not JSON\n')

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        adapter = StdInInput(["echo", "Not JSON"])
        await adapter.start()
        with pytest.raises(EOFError, match="Invalid JSON"):
            await adapter.read_message()

@pytest.mark.asyncio
async def test_stdin_input_adapter_read_message_eof():
    # simulate EOF by returning empty bytes
    mock_process = AsyncMock()
    mock_process.stdout.readline = AsyncMock(return_value=b'')

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        adapter = StdInInput(["echo"])
        await adapter.start()
        with pytest.raises(EOFError, match="EOF reached"):
            await adapter.read_message()

@pytest.mark.asyncio
async def test_stdin_input_adapter_read_message_empty_line():
    # empty line (just newline)
    mock_process = AsyncMock()
    mock_process.stdout.readline = AsyncMock(return_value=b'\n')

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        adapter = StdInInput(["echo"])
        await adapter.start()
        with pytest.raises(EOFError, match="EOF reached"):
            await adapter.read_message()

@pytest.mark.asyncio
async def test_stdin_input_adapter_read_message_timeout():
    mock_process = AsyncMock()

    async def timeout_readline():
        await asyncio.sleep(0.1)
        return b''

    mock_process.stdout.readline.side_effect = asyncio.TimeoutError()

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        adapter = StdInInput(["sleep", "10"], timeout=0.01)
        await adapter.start()
        with pytest.raises(EOFError, match="Timed out waiting for input."):
            await adapter.read_message()

@pytest.mark.asyncio
async def test_stdin_input_adapter_stop():
    mock_process = AsyncMock()
    mock_process.terminate = MagicMock()  # Make terminate synchronous
    mock_process.wait = AsyncMock()

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        adapter = StdInInput(["echo"])
        await adapter.start()
        await adapter.stop()

    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_awaited_once()
    assert adapter.process is None

