import pytest
import asyncio
import json
from adapters.input.server_input_adapter import ServerInputAdapter

@pytest.mark.asyncio
async def test_server_input_adapter_start():
    # Test that start() does nothing and doesn't raise exceptions
    q = asyncio.Queue()
    adapter = ServerInputAdapter(message_queue=q)
    await adapter.start()  # should do nothing

@pytest.mark.asyncio
async def test_server_input_adapter_stop():
    # Test that stop() does nothing and doesn't raise exceptions
    q = asyncio.Queue()
    adapter = ServerInputAdapter(message_queue=q)
    await adapter.stop()  # should do nothing

@pytest.mark.asyncio
async def test_server_input_adapter_read_message_valid():
    # Test reading a valid JSON message
    q = asyncio.Queue()

    msg = {"role": "Questioner", "message": "hello"}
    await q.put(json.dumps(msg))

    adapter = ServerInputAdapter(message_queue=q)
    result = await adapter.read_message()
    assert result == msg

@pytest.mark.asyncio
async def test_server_input_adapter_read_message_empty_queue():
    # If the queue is empty, read_message should wait.
    # We'll test that read_message doesn't crash or behave unexpectedly
    q = asyncio.Queue()
    adapter = ServerInputAdapter(message_queue=q)

    # We'll put a message after a short delay to mimic real asynchronous behavior
    async def put_message():
        await asyncio.sleep(0.1)
        await q.put(json.dumps({"role": "Questioner", "message": "delayed"}))

    asyncio.create_task(put_message())
    result = await adapter.read_message()
    assert result == {"role": "Questioner", "message": "delayed"}

@pytest.mark.asyncio
async def test_server_input_adapter_read_message_invalid_json():
    # Test what happens if the queue receives invalid JSON
    q = asyncio
