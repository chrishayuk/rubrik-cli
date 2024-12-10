import pytest
from unittest.mock import AsyncMock, patch
from adapters.input.stdin_input_adapter import StdInInput

@pytest.mark.asyncio
async def test_stdin_input_adapter_read_message_valid_json():
    mock_process = AsyncMock()
    # Simulate a single valid JSON line (no Future needed, just bytes)
    mock_process.stdout.readline = AsyncMock(return_value=b'{"role":"Questioner","message":"hello"}\n')

    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        adapter = StdInInput(["echo", '{"role":"Questioner","message":"hello"}'])
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "hello"}

@pytest.mark.asyncio
async def test_stdin_input_adapter_read_message_non_json():
    mock_process = AsyncMock()
    # Simulate non-JSON output
    mock_process.stdout.readline = AsyncMock(return_value=b'Just some text\n')

    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        adapter = StdInInput(["echo", "Just some text"])
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "assistant", "message": "Just some text"}

@pytest.mark.asyncio
async def test_stdin_input_adapter_read_message_eof():
    mock_process = AsyncMock()
    # An empty byte string signals EOF
    mock_process.stdout.readline = AsyncMock(return_value=b'')

    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        adapter = StdInInput(["echo", ""])
        await adapter.start()
        with pytest.raises(EOFError, match="EOF reached."):
            await adapter.read_message()
