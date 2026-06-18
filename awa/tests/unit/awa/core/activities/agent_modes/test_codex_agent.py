"""Unit tests for CodexAgent."""

from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.agent_modes.codex_agent import CodexAgent


@pytest.fixture
def codex_agent() -> CodexAgent:
    """Fixture to provide a CodexAgent instance."""
    return CodexAgent()


def test_get_init_file_name(codex_agent: CodexAgent) -> None:
    """Test get_init_file_name returns an empty string."""
    assert codex_agent.get_init_file_name() == ""


@pytest.mark.asyncio
@patch("awa.core.activities.agent_modes.codex_agent.CodexAgent.execute_prompt")
async def test_execute_command(mock_execute_prompt: AsyncMock, codex_agent: CodexAgent) -> None:
    """Test execute_command calls execute_prompt with the correct prompt."""
    command = "my_command.txt"
    await codex_agent.execute_command(command, "/fake/dir", ["tool1"])

    expected_prompt = f"Read the content from this file {command} and execute"
    mock_execute_prompt.assert_called_once_with(expected_prompt, "/fake/dir", ["tool1"])


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_success(mock_run_command: AsyncMock, codex_agent: CodexAgent) -> None:
    """Test execute_prompt with a successful command execution."""
    mock_run_command.return_value = (True, "Mock response from codex")
    prompt = "do something"
    result = await codex_agent.execute_prompt(prompt, "/fake/dir")

    assert result.status
    assert "mock response" in result.result.lower()
    mock_run_command.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_api_error(mock_run_command: AsyncMock, codex_agent: CodexAgent) -> None:
    """Test execute_prompt with API error detection."""
    mock_run_command.return_value = (True, "API Error: Something went wrong")
    prompt = "tell me about python"
    result = await codex_agent.execute_prompt(prompt, "/fake/dir")

    assert not result.status  # Should be False because result starts with "API Error:"
    assert "API Error" in result.result
    mock_run_command.assert_called_once()
