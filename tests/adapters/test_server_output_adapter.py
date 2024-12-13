import pytest
import json
from unittest.mock import AsyncMock
from src.adapters.output.server_output_adapter import ServerOutputAdapter

@pytest.mark.asyncio
async def test_server_output_adapter_start():
    clients = set()
    adapter = ServerOutputAdapter(clients)
    await adapter.start()  # no error expected

@pytest.mark.asyncio
async def test_server_output_adapter_stop():
    clients = set()
    adapter = ServerOutputAdapter(clients)
    await adapter.start()
    await adapter.stop()

    with pytest.raises(EOFError, match="Adapter is stopped"):
        await adapter.write_message({"role": "Responder", "message": "Hi"})

@pytest.mark.asyncio
async def test_server_output_adapter_write_valid_message():
    client1 = AsyncMock()
    client2 = AsyncMock()
    clients = {client1, client2}

    adapter = ServerOutputAdapter(clients)
    data = {"role": "Responder", "message": "woof"}
    await adapter.write_message(data)

    message_str = json.dumps(data)
    client1.send.assert_awaited_once_with(message_str)
    client2.send.assert_awaited_once_with(message_str)
    assert clients == {client1, client2}

@pytest.mark.asyncio
async def test_server_output_adapter_write_no_clients():
    clients = set()
    adapter = ServerOutputAdapter(clients)
    data = {"role": "Responder", "message": "empty"}
    # No clients means just no broadcast, no error
    await adapter.write_message(data)

@pytest.mark.asyncio
async def test_server_output_adapter_write_non_serializable():
    clients = set()
    adapter = ServerOutputAdapter(clients)
    data = {"role": "Responder", "message": {"non_serializable": set([1,2,3])}}

    with pytest.raises(EOFError, match="Unable to serialize data"):
        await adapter.write_message(data)

@pytest.mark.asyncio
async def test_server_output_adapter_broadcast_remove_failed_clients():
    good_client = AsyncMock()
    bad_client = AsyncMock()
    bad_client.send.side_effect = Exception("Send failed")
    clients = {good_client, bad_client}

    # Configure the adapter with no retries
    adapter = ServerOutputAdapter(clients, max_send_retries=1)
    message_str = "some message"
    await adapter.broadcast(message_str)

    good_client.send.assert_awaited_once_with(message_str)
    bad_client.send.assert_awaited_once_with(message_str)
    assert clients == {good_client}


