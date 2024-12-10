import pytest
from unittest.mock import patch
from adapters.input.human_input_adapter import HumanInput

@pytest.mark.asyncio
async def test_human_input_reads_message():
    # Mock the built-in input function to return a preset string
    with patch("builtins.input", return_value="Hello there"):
        adapter = HumanInput()
        result = await adapter.read_message()

    assert result == {"role": "Questioner", "message": "Hello there"}

@pytest.mark.asyncio
async def test_human_input_empty_input():
    # Test what happens if the user just presses enter (empty message)
    with patch("builtins.input", return_value=""):
        adapter = HumanInput()
        result = await adapter.read_message()

    assert result == {"role": "Questioner", "message": ""}

@pytest.mark.asyncio
async def test_human_input_special_chars():
    # Test input with some special characters or whitespace
    test_str = "   some special input   "
    with patch("builtins.input", return_value=test_str):
        adapter = HumanInput()
        result = await adapter.read_message()

    assert result == {"role": "Questioner", "message": test_str}

@pytest.mark.asyncio
async def test_human_input_start():
    adapter = HumanInput()
    # Just call start and ensure no errors.
    await adapter.start()

@pytest.mark.asyncio
async def test_human_input_stop():
    adapter = HumanInput()
    # Just call stop and ensure no errors.
    await adapter.stop()
