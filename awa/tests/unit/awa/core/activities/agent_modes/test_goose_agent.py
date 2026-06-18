"""Unit tests for GooseAgent."""

from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.agent_modes.goose_agent import GooseAgent


@pytest.fixture
def goose_agent() -> GooseAgent:
    """Fixture to provide a GooseAgent instance."""
    return GooseAgent()


@pytest.mark.asyncio
@patch("awa.core.activities.agent_modes.goose_agent.GooseAgent._execute_goose_command")
async def test_execute_command(mock_execute: AsyncMock, goose_agent: GooseAgent) -> None:
    """Test execute_command formats the command correctly."""
    command = "do a thing"
    session_id = "test-session"
    await goose_agent.execute_command(command, "/fake/dir", session_id=session_id)

    expected_base_command = f'goose run -n "{session_id}" -i "{command}"'
    mock_execute.assert_called_once_with(expected_base_command, "/fake/dir", session_id)


@pytest.mark.asyncio
@patch("awa.core.activities.agent_modes.goose_agent.GooseAgent._execute_goose_command")
async def test_execute_prompt(mock_execute: AsyncMock, goose_agent: GooseAgent) -> None:
    """Test execute_prompt formats the prompt correctly."""
    prompt = "tell me a story\nabout a goose"
    session_id = "test-session-prompt"
    await goose_agent.execute_prompt(prompt, "/fake/dir", session_id=session_id)

    cleaned_prompt = "".join(prompt.splitlines())
    expected_base_command = f'goose run -n "{session_id}" -t "{cleaned_prompt}"'
    mock_execute.assert_called_once_with(expected_base_command, "/fake/dir", session_id)


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_goose_command_success(mock_run_command: AsyncMock, goose_agent: GooseAgent) -> None:
    """Test _execute_goose_command with a successful command."""
    mock_run_command.return_value = (True, "Success")
    result = await goose_agent._execute_goose_command("goose test", "/fake/dir", "sid")

    assert result.status
    assert result.result == "Success"
    mock_run_command.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_goose_command_failure(mock_run_command: AsyncMock, goose_agent: GooseAgent) -> None:
    """Test _execute_goose_command detects failure string."""
    error_message = "Something failed. Please retry if you think this is a transient or recoverable error."
    mock_run_command.return_value = (True, error_message)
    result = await goose_agent._execute_goose_command("goose test", "/fake/dir", "sid")

    assert not result.status
    assert result.result == error_message


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_get_log_files(mock_run_command: AsyncMock, goose_agent: GooseAgent) -> None:
    """Test get_log_files calls the correct export command."""
    session_id = "log-session"
    await goose_agent.get_log_files("/fake/dir", session_id)

    expected_command = f'goose session export --name "{session_id}" --output session.md'
    mock_run_command.assert_called_once_with(expected_command, "/fake/dir")


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_cleanup(mock_run_command: AsyncMock, goose_agent: GooseAgent) -> None:
    """Test cleanup calls the correct remove command."""
    session_id = "cleanup-session"
    await goose_agent.cleanup(session_id)

    expected_command = f'goose session remove -i "{session_id}"'
    mock_run_command.assert_called_once_with(expected_command)


@pytest.mark.asyncio
async def test_cleanup_no_session_id(goose_agent: GooseAgent) -> None:
    """Test cleanup does nothing if no session_id is provided."""
    with patch("awa.core.utils.command_utils.CommandUtils.run_command_async") as mock_run_command:
        await goose_agent.cleanup(None)
        mock_run_command.assert_not_called()
