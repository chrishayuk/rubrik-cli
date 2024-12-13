import pytest
from src.adapters.input.input_adapter import InputAdapter

@pytest.mark.asyncio
async def test_input_adapter_read_message_not_implemented():
    adapter = InputAdapter()
    with pytest.raises(NotImplementedError):
        await adapter.read_message()

@pytest.mark.asyncio
async def test_input_adapter_start():
    adapter = InputAdapter()
    # start() does nothing, but we can still call it to ensure no exceptions.
    await adapter.start()

@pytest.mark.asyncio
async def test_input_adapter_stop():
    adapter = InputAdapter()
    # stop() does nothing, but we can still call it to ensure no exceptions.
    await adapter.stop()
