import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock
from adapters.output.server_output_adapter import ServerOutputAdapter

@pytest.mark.asyncio
async def test_server_output_adapter_start():
    clients = set()
    adapter = ServerOutputAdapter(clients)
    # start does nothing but should not raise an exception
    await adapter.start()

@pytest.mark.asyncio
async def test_server_output_adapter_stop():
    clients = set()
    adapter = ServerOutputAdapter(clients)
    # stop does nothing but should not raise an exception
    await adapter.stop()

@pytest.mark.asyncio
async def test_server_output_adapter_write_message():
    # Create a few mock clients
    client1 = AsyncMock()
    client2 = AsyncMock()
    clients = {client1, client2}

    adapter = ServerOutputAdapter(clients)
    data = {"role": "Responder", "message": "woof"}
    await adapter.write_message(data)

    # Verify that both clients' send was called with the JSON-serialized message
    message_str = json.dumps(data)
    client1.send.assert_awaited_once_with(message_str)
    client2.send.assert_awaited_once_with(message_str)

    # Ensure no clients were removed since no errors occurred
    assert clients == {client1, client2}

@pytest.mark.asyncio
async def test_server_output_adapter_broadcast_remove_failed_clients():
    # Create mock clients, one of which fails
    good_client = AsyncMock()
    bad_client = AsyncMock()
    bad_client.send.side_effect = Exception("Send failed")
    clients = {good_client, bad_client}

    adapter = ServerOutputAdapter(clients)
    message_str = "some message"
    await adapter.broadcast(message_str)

    # good_client should have received the message
    good_client.send.assert_awaited_once_with(message_str)
    # bad_client should have tried to send but failed
    bad_client.send.assert_awaited_once_with(message_str)

    # Verify bad_client is removed from the set
    assert clients == {good_client}

@pytest.mark.asyncio
async def test_server_output_adapter_write_message_failure():
    # Test scenario: If one client fails during write_message
    good_client = AsyncMock()
    bad_client = AsyncMock()
    bad_client.send.side_effect = Exception("Send failed")  # Set side_effect on send, not bad_client

    clients = {good_client, bad_client}
    adapter = ServerOutputAdapter(clients)
    data = {"role": "Responder", "message": "woof"}
    await adapter.write_message(data)

    message_str = json.dumps(data)
    good_client.send.assert_awaited_once_with(message_str)
    bad_client.send.assert_awaited_once_with(message_str)

    # bad_client should be removed after the failure
    assert clients == {good_client}

