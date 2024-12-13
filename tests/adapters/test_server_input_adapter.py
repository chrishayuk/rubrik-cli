import pytest
import asyncio
from unittest.mock import AsyncMock
from src.adapters.input.server_input_adapter import ServerInputAdapter
import json

@pytest.mark.asyncio
async def test_server_input_adapter_start():
    q = asyncio.Queue()
    adapter = ServerInputAdapter(q)
    await adapter.start()  # no error expected

@pytest.mark.asyncio
async def test_server_input_adapter_stop():
    q = asyncio.Queue()
    adapter = ServerInputAdapter(q)
    await adapter.start()
    await adapter.stop()

    with pytest.raises(EOFError, match="Adapter is stopped"):
        await adapter.read_message()

@pytest.mark.asyncio
async def test_server_input_adapter_read_valid_message():
    q = asyncio.Queue()
    await q.put(json.dumps({"role": "Questioner", "message": "Hello"}))
    adapter = ServerInputAdapter(q)
    await adapter.start()
    msg = await adapter.read_message()
    assert msg == {"role": "Questioner", "message": "Hello"}

@pytest.mark.asyncio
async def test_server_input_adapter_read_none():
    q = asyncio.Queue()
    await q.put(None)  # signal no more messages
    adapter = ServerInputAdapter(q)
    await adapter.start()
    with pytest.raises(EOFError, match="No more messages"):
        await adapter.read_message()

@pytest.mark.asyncio
async def test_server_input_adapter_read_invalid_json():
    q = asyncio.Queue()
    await q.put("Not JSON")
    adapter = ServerInputAdapter(q)
    await adapter.start()
    with pytest.raises(EOFError, match="Invalid JSON"):
        await adapter.read_message()

@pytest.mark.asyncio
async def test_server_input_adapter_read_unexpected_exception():
    q = AsyncMock()
    q.get.side_effect = Exception("Unexpected error")

    adapter = ServerInputAdapter(q)
    await adapter.start()
    with pytest.raises(EOFError, match="Unexpected error while reading message"):
        await adapter.read_message()
