import pytest
from unittest.mock import AsyncMock, MagicMock
from src.chat_handler.adapters import start_adapters, stop_adapters

@pytest.mark.asyncio
async def test_start_adapters_with_start_methods(mocker):
    input_adapter = AsyncMock()
    output_adapter = AsyncMock()

    await start_adapters(input_adapter, output_adapter)

    input_adapter.start.assert_awaited_once()
    output_adapter.start.assert_awaited_once()

@pytest.mark.asyncio
async def test_start_adapters_without_start_methods(mocker):
    input_adapter = MagicMock()
    output_adapter = MagicMock()

    # No start methods defined
    # `callable(getattr(adapter, "start", None))` will be False if there's no `start` attribute.

    await start_adapters(input_adapter, output_adapter)
    # No exceptions should be raised and nothing should be awaited


@pytest.mark.asyncio
async def test_stop_adapters_with_stop_methods(mocker):
    input_adapter = AsyncMock()
    output_adapter = AsyncMock()

    await stop_adapters(input_adapter, output_adapter)

    input_adapter.stop.assert_awaited_once()
    output_adapter.stop.assert_awaited_once()

@pytest.mark.asyncio
async def test_stop_adapters_without_stop_methods():
    # Adapters without stop methods
    input_adapter = MagicMock()
    output_adapter = MagicMock()

    await stop_adapters(input_adapter, output_adapter)

    # Since there's no stop method, nothing should be called or raised
    # Just ensure we had no exceptions

@pytest.mark.asyncio
async def test_stop_adapters_with_exceptions(mocker, caplog):
    caplog.set_level("DEBUG")

    input_adapter = AsyncMock()
    input_adapter.stop.side_effect = Exception("Input stop error")

    output_adapter = AsyncMock()
    output_adapter.stop.side_effect = Exception("Output stop error")

    await stop_adapters(input_adapter, output_adapter)

    assert any("Error stopping input_adapter: Input stop error" in rec.message for rec in caplog.records)
    assert any("Error stopping output_adapter: Output stop error" in rec.message for rec in caplog.records)
    
