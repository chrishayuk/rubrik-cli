import pytest
import asyncio
from unittest.mock import patch
from adapters.input.human_input_adapter import HumanInput

@pytest.mark.asyncio
async def test_human_input_basic():
    # Mock input to return "Hello"
    with patch("builtins.input", return_value="Hello"):
        adapter = HumanInput()
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "Hello"}

@pytest.mark.asyncio
async def test_human_input_empty_input():
    # Mock input to return empty string
    with patch("builtins.input", return_value=""):
        adapter = HumanInput()
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": ""}

@pytest.mark.asyncio
async def test_human_input_stop():
    # Once stop is called, read_message should raise EOFError
    with patch("builtins.input", return_value="Hello"):
        adapter = HumanInput()
        await adapter.start()
        # First call works
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "Hello"}

        await adapter.stop()
        with pytest.raises(EOFError, match="stopped"):
            await adapter.read_message()

@pytest.mark.asyncio
async def test_human_input_eof():
    # Simulate EOFError (end of input)
    with patch("builtins.input", side_effect=EOFError):
        adapter = HumanInput()
        await adapter.start()
        with pytest.raises(EOFError, match="No more user input available"):
            await adapter.read_message()

@pytest.mark.asyncio
async def test_human_input_keyboard_interrupt():
    # Simulate Ctrl+C interrupt
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        adapter = HumanInput()
        await adapter.start()
        with pytest.raises(EOFError, match="Interrupted by user"):
            await adapter.read_message()

@pytest.mark.asyncio
async def test_human_input_custom_prompt():
    # Check that the custom prompt is passed to input()
    custom_prompt = "Enter your query: "
    def mock_input(prompt):
        if prompt == custom_prompt:
            return "Hi"
        else:
            return None

    with patch("builtins.input", side_effect=mock_input) as mock_input_fn:
        adapter = HumanInput(prompt=custom_prompt)
        await adapter.start()
        msg = await adapter.read_message()
        assert msg == {"role": "Questioner", "message": "Hi"}
        mock_input_fn.assert_called_once_with(custom_prompt)
