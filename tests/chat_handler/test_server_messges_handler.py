import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.chat_handler.server_messages_handler import handle_server_messages
from websockets.exceptions import ConnectionClosedError

@pytest.mark.asyncio
async def test_server_messages_handler_normal_message():
    # Mock the chat_handler and its output_adapter
    chat_handler = MagicMock()
    chat_handler.server = False
    chat_handler.local_name = "You (Client)"
    chat_handler.remote_name = "Assistant (Server)"

    # First call returns a complete message, second call returns EOFError to keep the loop alive
    chat_handler.output_adapter.read_message = AsyncMock(side_effect=[
        {"role": "assistant", "message": "Hello from server!", "partial": False},
        EOFError("No more messages")
    ])

    # Mock print_prompt to avoid actual I/O
    with patch("src.chat_handler.ui_utils.print_prompt", new_callable=AsyncMock) as mock_prompt:
        mock_prompt.return_value = None  # immediately return

        # Patch UIRenderer
        with patch("src.chat_handler.server_messages_handler.UIRenderer") as MockUIRenderer:
            mock_renderer = MockUIRenderer.return_value
            mock_renderer.is_streaming = False
            mock_renderer.after_message = AsyncMock()

            # Run the handler in a task
            task = asyncio.create_task(handle_server_messages(chat_handler))

            # Give enough time for the message to be processed and display_complete_message to be called
            await asyncio.sleep(1.0)

            # Now cancel the task to stop the loop
            task.cancel()
            # Wait for cancellation to finish
            with pytest.raises(asyncio.CancelledError):
                await task

            # Check that display_complete_message was called with expected arguments
            mock_renderer.display_complete_message.assert_called_once_with(
                False, "You (Client)", "Assistant (Server)", "assistant", "Hello from server!"
            )

            # Check that after_message was awaited
            mock_renderer.after_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_server_messages_handler_streaming_message():
    chat_handler = MagicMock()
    chat_handler.server = False
    chat_handler.local_name = "You"
    chat_handler.remote_name = "Assistant"

    # Sequence: partial "Hel", partial "lo ", final "Hello complete!", then EOF to stop reading
    chat_handler.output_adapter.read_message = AsyncMock(side_effect=[
        {"role": "assistant", "message": "Hel", "partial": True},
        {"role": "assistant", "message": "lo ", "partial": True},
        {"role": "assistant", "message": "Hello complete!", "partial": False},
        EOFError("No more messages")
    ])

    # Mock ui_utils and ui_renderer dependencies
    with patch("src.chat_handler.ui_utils.role_to_display_name", return_value=("Assistant", "assistant")), \
         patch("src.chat_handler.ui_utils.display_message") as mock_display_message, \
         patch("src.chat_handler.ui_utils.print_prompt", new_callable=AsyncMock) as mock_prompt, \
         patch("src.chat_handler.ui_renderer.Live") as mock_live, \
         patch("src.chat_handler.ui_renderer.console") as mock_console, \
         patch("src.chat_handler.server_messages_handler.UIRenderer") as MockUIRenderer:

        # Configure Live mock to behave like a context manager without real I/O
        mock_live.return_value.__enter__.return_value = None
        mock_live.return_value.__exit__.return_value = None

        mock_renderer = MockUIRenderer.return_value
        mock_renderer.is_streaming = False
        mock_renderer.after_message = AsyncMock()

        # Run the handler in a task and allow real sleep
        task = asyncio.create_task(handle_server_messages(chat_handler))
        # Give more time (e.g., 2 seconds) to ensure messages are processed
        await asyncio.sleep(2.0)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # If the test fails, print the mock calls for debugging
        # (You can remove this once it's passing)
        if mock_renderer.start_streaming.call_count == 0:
            print("Mock renderer calls:", mock_renderer.mock_calls)

        # Now verify calls
        # For the first partial chunk "Hel", start_streaming should have been called
        mock_renderer.start_streaming.assert_any_call(False, "You", "Assistant", "assistant", "Hel")

        # For the second partial "lo ", update_streaming should be called
        mock_renderer.update_streaming.assert_any_call("lo ")

        # For the final message "Hello complete!", streaming ends and display_message is called
        mock_renderer.end_streaming.assert_called_once()
        mock_renderer.after_message.assert_awaited()

        # Check that display_message was called for the final complete message
        mock_display_message.assert_any_call(False, "You", "Assistant", "assistant", "Hello complete!")


@pytest.mark.asyncio
async def test_server_messages_handler_eof_error(mocker):
    chat_handler = MagicMock()
    chat_handler.server = False
    chat_handler.local_name = "You"
    chat_handler.remote_name = "Assistant"

    # EOF first, then a complete message, then another EOF to stop
    chat_handler.output_adapter.read_message = AsyncMock(side_effect=[
        EOFError("No messages"),
        {"role": "assistant", "message": "After EOF", "partial": False},
        EOFError("No more messages")
    ])

    with patch("src.chat_handler.server_messages_handler.UIRenderer") as MockUIRenderer:
        mock_renderer = MockUIRenderer.return_value
        mock_renderer.is_streaming = False
        mock_renderer.after_message = AsyncMock()

        with patch("asyncio.sleep", return_value=None):
            task = asyncio.create_task(handle_server_messages(chat_handler))
            await asyncio.sleep(0.5)
            task.cancel()

        mock_renderer.display_complete_message.assert_any_call(
            False, "You", "Assistant", "assistant", "After EOF"
        )
        mock_renderer.after_message.assert_awaited()


@pytest.mark.asyncio
async def test_server_messages_handler_connection_closed_error(mocker):
    chat_handler = MagicMock()
    chat_handler.server = False
    chat_handler.local_name = "You"
    chat_handler.remote_name = "Assistant"

    # Simulate connection closed first, then a normal message
    # Use None, None to indicate a closure without codes that fits websockets.ConnectionClosedError
    chat_handler.output_adapter.read_message = AsyncMock(side_effect=[
        ConnectionClosedError(None, None),
        {"role": "assistant", "message": "After reconnect", "partial": False},
        EOFError("No more messages")
    ])

    with patch("src.chat_handler.server_messages_handler.UIRenderer") as MockUIRenderer:
        mock_renderer = MockUIRenderer.return_value
        mock_renderer.is_streaming = False
        mock_renderer.after_message = AsyncMock()

        with patch("asyncio.sleep", return_value=None):
            task = asyncio.create_task(handle_server_messages(chat_handler))
            await asyncio.sleep(0.5)
            task.cancel()

        mock_renderer.display_complete_message.assert_any_call(
            False, "You", "Assistant", "assistant", "After reconnect"
        )
        mock_renderer.after_message.assert_awaited()
