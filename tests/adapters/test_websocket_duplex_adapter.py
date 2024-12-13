import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from websockets.exceptions import ConnectionClosedError
from src.adapters.duplex.websocket_duplex_adapter import WebSocketDuplexAdapter


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_start_success():
    mock_ws = AsyncMock()
    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketDuplexAdapter(uri="ws://example.com/ws")
        await adapter.start()
        assert adapter.websocket == mock_ws


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_start_retry_then_success():
    # Simulate failing once, then succeeding
    mock_ws = AsyncMock()
    connect_calls = [Exception("Failed once"), mock_ws]

    async def mock_connect(uri):
        val = connect_calls.pop(0)
        if isinstance(val, Exception):
            raise val
        return val

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketDuplexAdapter(uri="ws://example.com/ws", max_retries=3, retry_delay=0.01)
        await adapter.start()
        assert adapter.websocket == mock_ws


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_read_message_valid():
    mock_ws = AsyncMock()
    mock_ws.recv = AsyncMock(return_value=json.dumps({"role": "Questioner", "message": "Hello"}))

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketDuplexAdapter()
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "Hello"}


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_read_message_invalid_json():
    mock_ws = AsyncMock()
    # First return invalid JSON, then valid JSON
    mock_ws.recv = AsyncMock(side_effect=["Not JSON", json.dumps({"role": "Questioner", "message": "Hi"})])

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketDuplexAdapter()
        await adapter.start()
        msg = await adapter.read_message()
        # The adapter skips invalid JSON and returns the next valid one
        assert msg == {"role": "Questioner", "message": "Hi"}


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_read_message_connection_closed():
    # First websocket fails
    first_mock_ws = AsyncMock()
    first_mock_ws.recv = AsyncMock(side_effect=ConnectionClosedError(None, None))
    # After reconnect, return a valid message
    second_mock_ws = AsyncMock()
    second_mock_ws.recv = AsyncMock(return_value=json.dumps({"role": "Questioner", "message": "Recovered"}))

    connect_calls = [first_mock_ws, second_mock_ws]

    async def mock_connect(uri):
        return connect_calls.pop(0)

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketDuplexAdapter(max_retries=2, retry_delay=0.01)
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "Recovered"}


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_read_message_unexpected_error():
    # First websocket raises a generic exception
    first_mock_ws = AsyncMock()
    first_mock_ws.recv = AsyncMock(side_effect=Exception("Unexpected error"))
    # After reconnect, return a valid message
    second_mock_ws = AsyncMock()
    second_mock_ws.recv = AsyncMock(return_value=json.dumps({"role": "Questioner", "message": "AfterError"}))

    connect_calls = [first_mock_ws, second_mock_ws]

    async def mock_connect(uri):
        return connect_calls.pop(0)

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketDuplexAdapter(max_retries=2, retry_delay=0.01)
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "AfterError"}


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_write_message_valid():
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketDuplexAdapter()
        await adapter.start()
        await adapter.write_message({"role": "Questioner", "message": "Hello"})
        mock_ws.send.assert_awaited_once()
        sent_msg = mock_ws.send.call_args[0][0]
        assert json.loads(sent_msg) == {"role": "Questioner", "message": "Hello"}


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_write_message_non_serializable():
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketDuplexAdapter()
        await adapter.start()

        # Non-serializable data
        await adapter.write_message({"role": "Questioner", "message": {"non_serializable": {1,2,3}}})
        # Should not call send at all
        mock_ws.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_write_message_connection_closed():
    # First attempt fails with ConnectionClosedError
    first_mock_ws = AsyncMock()
    first_mock_ws.send = AsyncMock(side_effect=ConnectionClosedError(None, None))
    # After reconnect, sending succeeds
    second_mock_ws = AsyncMock()
    second_mock_ws.send = AsyncMock()

    connect_calls = [first_mock_ws, second_mock_ws]

    async def mock_connect(uri):
        return connect_calls.pop(0)

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketDuplexAdapter(retry_delay=0.01)
        await adapter.start()
        await adapter.write_message({"role": "Questioner", "message": "Recovered"})
        second_mock_ws.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_write_message_unexpected_error():
    # First attempt fails with an unexpected error
    first_mock_ws = AsyncMock()
    first_mock_ws.send = AsyncMock(side_effect=Exception("Unexpected error"))
    # After reconnect, sending succeeds
    second_mock_ws = AsyncMock()
    second_mock_ws.send = AsyncMock()

    connect_calls = [first_mock_ws, second_mock_ws]

    async def mock_connect(uri):
        return connect_calls.pop(0)

    with patch("websockets.connect", new_callable=AsyncMock, side_effect=mock_connect):
        adapter = WebSocketDuplexAdapter(retry_delay=0.01)
        await adapter.start()
        await adapter.write_message({"role": "Questioner", "message": "AfterError"})
        second_mock_ws.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_stop():
    mock_ws = AsyncMock()
    mock_ws.close = AsyncMock()

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws):
        adapter = WebSocketDuplexAdapter()
        await adapter.start()
        await adapter.stop()
        mock_ws.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_websocket_duplex_adapter_get_user_input_and_send():
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()

    inputs = ["Hello", "Another message", "quit"]
    def input_side_effect(*args, **kwargs):
        return inputs.pop(0)

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_ws), \
         patch("builtins.input", side_effect=input_side_effect):
        adapter = WebSocketDuplexAdapter()
        await adapter.start()
        task = asyncio.create_task(adapter.get_user_input_and_send())
        await task

        assert mock_ws.send.await_count == 2
        sent_args = [call_args[0][0] for call_args in mock_ws.send.call_args_list]
        sent_data = [json.loads(arg) for arg in sent_args]
        assert sent_data == [
            {"role": "Questioner", "message": "Hello"},
            {"role": "Questioner", "message": "Another message"}
        ]
