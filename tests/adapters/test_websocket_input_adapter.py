import pytest
from unittest.mock import AsyncMock, patch
import json
from websockets.exceptions import ConnectionClosedError
from src.adapters.input.websocket_input_adapter import WebSocketInput

@pytest.mark.asyncio
async def test_websocket_input_start_success():
    mock_ws = AsyncMock()
    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketInput(uri="ws://example.com/ws")
        await adapter.start()
        assert adapter.websocket == mock_ws

@pytest.mark.asyncio
async def test_websocket_input_start_failure():
    # Simulate connect failing all attempts by raising Exception
    async def mock_connect(*args, **kwargs):
        raise Exception("Connection failed")

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketInput(uri="ws://example.com/ws", max_retries=2, retry_delay=0.01)
        with pytest.raises(EOFError, match="Unable to establish WebSocket connection"):
            await adapter.start()

@pytest.mark.asyncio
async def test_websocket_input_start_retries_then_success():
    mock_ws = AsyncMock()
    attempts = [Exception("Failed once"), mock_ws]

    async def mock_connect(*args, **kwargs):
        val = attempts.pop(0)
        if isinstance(val, Exception):
            raise val
        return val

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketInput(uri="ws://example.com/ws", max_retries=2, retry_delay=0.01)
        await adapter.start()
        assert adapter.websocket == mock_ws

@pytest.mark.asyncio
async def test_websocket_input_read_message_valid():
    mock_ws = AsyncMock()
    mock_ws.recv = AsyncMock(return_value=json.dumps({"role": "Questioner", "message": "Hello"}))

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketInput(uri="ws://example.com/ws")
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "Hello"}

@pytest.mark.asyncio
async def test_websocket_input_read_message_invalid_json():
    mock_ws = AsyncMock()
    mock_ws.recv = AsyncMock(return_value="Not JSON")

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketInput(uri="ws://example.com/ws")
        await adapter.start()
        with pytest.raises(EOFError, match="Received invalid JSON"):
            await adapter.read_message()

@pytest.mark.asyncio
async def test_websocket_input_read_message_connection_closed_once():
    # First read attempt fails
    first_mock_ws = AsyncMock()
    first_mock_ws.recv = AsyncMock(side_effect=ConnectionClosedError(None, None))

    # After reconnect, a valid message is returned
    second_mock_ws = AsyncMock()
    second_mock_ws.recv = AsyncMock(return_value=json.dumps({"role": "Questioner", "message": "Recovered"}))

    attempts = [first_mock_ws, second_mock_ws]

    async def mock_connect(*args, **kwargs):
        return attempts.pop(0)

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketInput(uri="ws://example.com/ws", max_retries=2, retry_delay=0.01)
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "Recovered"}

@pytest.mark.asyncio
async def test_websocket_input_read_message_connection_closed_multiple_times():
    mock_ws = AsyncMock()
    mock_ws.recv = AsyncMock(side_effect=ConnectionClosedError(None, None))

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketInput(uri="ws://example.com/ws", max_retries=2, retry_delay=0.01)
        await adapter.start()
        with pytest.raises(EOFError, match="Failed to read message after multiple retries."):
            await adapter.read_message()

@pytest.mark.asyncio
async def test_websocket_input_stop():
    mock_ws = AsyncMock()
    mock_ws.close = AsyncMock()

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketInput(uri="ws://example.com/ws")
        await adapter.start()
        await adapter.stop()
        mock_ws.close.assert_awaited_once()
        assert adapter.websocket is not None

@pytest.mark.asyncio
async def test_websocket_input_stop_no_connection():
    adapter = WebSocketInput(uri="ws://example.com/ws")
    await adapter.stop()  # no error expected

@pytest.mark.asyncio
async def test_websocket_input_read_message_no_connection():
    async def mock_connect(*args, **kwargs):
        raise Exception("Connection failed")

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketInput(uri="ws://example.com/ws", max_retries=1, retry_delay=0.01)
        with pytest.raises(EOFError, match="Unable to establish WebSocket connection"):
            await adapter.start()
