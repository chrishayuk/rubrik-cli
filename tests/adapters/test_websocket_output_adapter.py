import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from websockets.exceptions import ConnectionClosedError
from adapters.output.websocket_output_adapter import WebSocketOutput


@pytest.mark.asyncio
async def test_websocket_output_start_success():
    mock_ws = AsyncMock()
    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketOutput(uri="ws://example.com/ws")
        await adapter.start()
        assert adapter.websocket == mock_ws


@pytest.mark.asyncio
async def test_websocket_output_start_failure():
    async def mock_connect(*args, **kwargs):
        raise Exception("Connection failed")

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketOutput(uri="ws://example.com/ws", max_retries=2, retry_delay=0.01)
        with pytest.raises(EOFError, match="Unable to establish WebSocket connection"):
            await adapter.start()


@pytest.mark.asyncio
async def test_websocket_output_write_message_valid():
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketOutput(uri="ws://example.com/ws")
        await adapter.start()

        data = {"role": "Responder", "message": "Hello"}
        await adapter.write_message(data)

        sent_msg = mock_ws.send.call_args[0][0]
        assert json.loads(sent_msg) == data


@pytest.mark.asyncio
async def test_websocket_output_write_message_non_serializable():
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketOutput(uri="ws://example.com/ws")
        await adapter.start()

        # Non-serializable data (contains a set)
        data = {"role": "Responder", "message": {"non_serializable": {1,2,3}}}
        with pytest.raises(EOFError, match="Unable to send invalid data"):
            await adapter.write_message(data)


@pytest.mark.asyncio
async def test_websocket_output_write_message_connection_closed_once():
    # First attempt fails due to ConnectionClosedError
    first_mock_ws = AsyncMock()
    first_mock_ws.send = AsyncMock(side_effect=ConnectionClosedError(None, None))
    # After reconnect, sending should succeed
    second_mock_ws = AsyncMock()
    second_mock_ws.send = AsyncMock()

    connect_calls = [first_mock_ws, second_mock_ws]

    async def mock_connect(*args, **kwargs):
        return connect_calls.pop(0)

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketOutput(uri="ws://example.com/ws", max_retries=2, retry_delay=0.01)
        await adapter.start()
        data = {"role": "Responder", "message": "Recovered"}
        await adapter.write_message(data)

        # Check second_ws got the correct message after a reconnect
        second_mock_ws.send.assert_awaited_once()
        sent_msg = second_mock_ws.send.call_args[0][0]
        assert json.loads(sent_msg) == data


@pytest.mark.asyncio
async def test_websocket_output_write_message_connection_closed_multiple_times():
    # All attempts fail with ConnectionClosedError
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock(side_effect=ConnectionClosedError(None, None))

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketOutput(uri="ws://example.com/ws", max_retries=2, retry_delay=0.01)
        await adapter.start()
        data = {"role": "Responder", "message": "Fail multiple times"}
        with pytest.raises(EOFError, match="Failed to write message after multiple retries"):
            await adapter.write_message(data)


@pytest.mark.asyncio
async def test_websocket_output_stop():
    mock_ws = AsyncMock()
    mock_ws.close = AsyncMock()

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketOutput(uri="ws://example.com/ws")
        await adapter.start()
        await adapter.stop()
        mock_ws.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_websocket_output_stop_no_connection():
    # If stop is called before start, no exception should occur
    adapter = WebSocketOutput(uri="ws://example.com/ws")
    await adapter.stop()  # no error expected
