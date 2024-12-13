import pytest
from src.adapters.output.output_adapter import OutputAdapter

@pytest.mark.asyncio
async def test_output_adapter_start():
    adapter = OutputAdapter()
    # start does nothing, should not raise exception
    await adapter.start()

@pytest.mark.asyncio
async def test_output_adapter_stop():
    adapter = OutputAdapter()
    # stop does nothing, should not raise exception
    await adapter.stop()

@pytest.mark.asyncio
async def test_output_adapter_write_message_not_implemented():
    adapter = OutputAdapter()
    with pytest.raises(NotImplementedError, match="write_message must be implemented."):
        await adapter.write_message({"role": "Questioner", "message": "Hello"})
