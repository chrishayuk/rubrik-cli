import pytest
import sys
import json
from unittest.mock import MagicMock, patch
from adapters.output.stdout_output_adapter import StdOutOutput

@pytest.mark.asyncio
async def test_stdout_output_write_message_valid(capsys):
    adapter = StdOutOutput()
    data = {"role": "Responder", "message": "Hello!"}
    await adapter.write_message(data)

    captured = capsys.readouterr()
    assert captured.out.strip() == json.dumps(data)

@pytest.mark.asyncio
async def test_stdout_output_write_message_empty_message(capsys):
    adapter = StdOutOutput()
    data = {"role": "Responder", "message": ""}
    await adapter.write_message(data)

    captured = capsys.readouterr()
    assert captured.out.strip() == json.dumps(data)

@pytest.mark.asyncio
async def test_stdout_output_write_message_non_serializable():
    adapter = StdOutOutput()
    data = {"role": "Responder", "message": {"non_serializable": set([1,2,3])}}
    with pytest.raises(EOFError, match="Unable to serialize data"):
        await adapter.write_message(data)

@pytest.mark.asyncio
async def test_stdout_output_write_message_failure():
    adapter = StdOutOutput()
    data = {"role": "Responder", "message": "Test"}

    mock_stdout = MagicMock()
    mock_stdout.write.side_effect = Exception("Write failed")

    with patch.object(sys, 'stdout', mock_stdout):
        with pytest.raises(EOFError, match="Failed to write to stdout"):
            await adapter.write_message(data)

@pytest.mark.asyncio
async def test_stdout_output_start():
    adapter = StdOutOutput()
    await adapter.start()  # no error expected

@pytest.mark.asyncio
async def test_stdout_output_stop():
    adapter = StdOutOutput()
    await adapter.stop()  # no error expected
