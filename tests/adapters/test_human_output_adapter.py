import pytest
from unittest.mock import MagicMock
from adapters.output.human_output_adapter import HumanOutput

@pytest.mark.asyncio
async def test_human_output_write_message_with_custom_renderer():
    # Create a mock renderer that will be passed to HumanOutput
    mock_renderer = MagicMock()

    adapter = HumanOutput(renderer=mock_renderer)
    data = {"role": "Questioner", "message": "Hello there!"}
    await adapter.write_message(data)

    # Ensure the renderer was called with the correct data
    mock_renderer.assert_called_once_with(data)

@pytest.mark.asyncio
async def test_human_output_write_message_with_default_renderer(capsys):
    # If no renderer is provided, the default renderer prints "role: message"
    adapter = HumanOutput()
    data = {"role": "Responder", "message": "This is a test."}
    await adapter.write_message(data)

    # Capture the output
    captured = capsys.readouterr()
    # Check the default format
    assert captured.out.strip() == "Responder: This is a test."

@pytest.mark.asyncio
async def test_human_output_start():
    adapter = HumanOutput()
    await adapter.start()  # Should do nothing and not raise

@pytest.mark.asyncio
async def test_human_output_stop():
    adapter = HumanOutput()
    await adapter.stop()  # Should do nothing and not raise
