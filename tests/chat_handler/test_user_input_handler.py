import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.chat_handler.user_input_handler import handle_user_input

@pytest.mark.asyncio
async def test_handle_user_input_normal_message(mocker):
    chat_handler = MagicMock()
    chat_handler.server = False
    chat_handler.local_name = "You (Human, Client)"
    chat_handler.remote_name = "Assistant (Server)"
    chat_handler.conversation_manager = MagicMock()

    chat_handler.input_adapter.read_message = AsyncMock(side_effect=[
        {"role": "user", "message": "Hello!"},
        {"role": "user", "message": "exit"}
    ])

    chat_handler.output_adapter = AsyncMock()

    with patch("src.chat_handler.user_input_handler.UIRenderer") as MockUIRenderer:
        mock_renderer = MockUIRenderer.return_value
        # Make after_message an async mock
        mock_renderer.after_message = AsyncMock()

        await handle_user_input(chat_handler)

        chat_handler.conversation_manager.add_message.assert_any_call("user", "Hello!")
        mock_renderer.display_complete_message.assert_any_call(
            server=False,
            local_name="You (Human, Client)",
            remote_name="Assistant (Server)",
            role="user",
            content="Hello!"
        )

        # Now that after_message is an AsyncMock, we can check it was awaited
        assert mock_renderer.after_message.await_count > 0

        chat_handler.output_adapter.write_message.assert_any_call({"role": "user", "message": "Hello!"})

@pytest.mark.asyncio
async def test_handle_user_input_exit(mocker):
    # Test that when user types "exit", we break out of the loop
    chat_handler = MagicMock()
    chat_handler.server = False
    chat_handler.local_name = "You"
    chat_handler.remote_name = "Assistant"
    chat_handler.conversation_manager = MagicMock()

    chat_handler.input_adapter.read_message = AsyncMock(return_value={"role": "user", "message": "exit"})
    chat_handler.output_adapter = AsyncMock()

    with patch("src.chat_handler.user_input_handler.UIRenderer") as MockUIRenderer:
        mock_renderer = MockUIRenderer.return_value

        await handle_user_input(chat_handler)

        # exit should break immediately, so no add_message calls
        chat_handler.conversation_manager.add_message.assert_not_called()
        mock_renderer.display_complete_message.assert_not_called()
        chat_handler.output_adapter.write_message.assert_not_called()

@pytest.mark.asyncio
async def test_handle_user_input_read_error(mocker):
    # Simulate EOFError or ConnectionClosedError leading to a retry
    chat_handler = MagicMock()
    chat_handler.server = False
    chat_handler.local_name = "You"
    chat_handler.remote_name = "Assistant"
    chat_handler.conversation_manager = MagicMock()

    # First call raises EOFError, second call returns a message, then exit
    chat_handler.input_adapter.read_message = AsyncMock(side_effect=[
        EOFError("No input"),
        {"role": "user", "message": "Hi there!"},
        {"role": "user", "message": "exit"}
    ])
    chat_handler.output_adapter = AsyncMock()

    with patch("src.chat_handler.user_input_handler.UIRenderer") as MockUIRenderer:
        mock_renderer = MockUIRenderer.return_value
        # Make after_message an async mock
        mock_renderer.after_message = AsyncMock()

        # We'll also patch asyncio.sleep to speed test up
        with patch("asyncio.sleep", return_value=None):
            await handle_user_input(chat_handler)

        # After the EOFError, we eventually got a message "Hi there!"
        chat_handler.conversation_manager.add_message.assert_any_call("user", "Hi there!")
        mock_renderer.display_complete_message.assert_any_call(
            server=False,
            local_name="You",
            remote_name="Assistant",
            role="user",
            content="Hi there!"
        )
        chat_handler.output_adapter.write_message.assert_any_call({"role": "user", "message": "Hi there!"})


@pytest.mark.asyncio
async def test_handle_user_input_write_error(mocker):
    # If writing to output_adapter fails, it should retry after a delay
    chat_handler = MagicMock()
    chat_handler.server = False
    chat_handler.local_name = "You"
    chat_handler.remote_name = "Assistant"
    chat_handler.conversation_manager = MagicMock()

    chat_handler.input_adapter.read_message = AsyncMock(side_effect=[
        {"role": "user", "message": "Test message"},
        {"role": "user", "message": "exit"}
    ])
    chat_handler.output_adapter = AsyncMock()

    # First attempt to write message fails with EOFError, second should not occur since loop ends with exit
    # Actually, since we immediately get "exit" after the first message, we might only see one fail
    # We'll just verify that the error is handled (logged) and not raised
    chat_handler.output_adapter.write_message.side_effect = [EOFError("Write error"), None]

    with patch("src.chat_handler.user_input_handler.UIRenderer") as MockUIRenderer:
        mock_renderer = MockUIRenderer.return_value

        with patch("asyncio.sleep", return_value=None):
            await handle_user_input(chat_handler)

        # Message added to conversation
        chat_handler.conversation_manager.add_message.assert_any_call("user", "Test message")
        # Displayed
        mock_renderer.display_complete_message.assert_any_call(
            server=False,
            local_name="You",
            remote_name="Assistant",
            role="user",
            content="Test message"
        )
        # Attempted to write to output_adapter, failed once
        assert chat_handler.output_adapter.write_message.call_count == 1
