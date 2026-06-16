"""Unit tests for QAgent."""

from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.agent_modes.q_agent import QAgent
from awa.sdk.models.agent_modes.agent_mode_base import CommandResult


@pytest.fixture
def q_agent() -> QAgent:
    """Fixture to provide a QAgent instance."""
    return QAgent()


def test_get_init_file_name(q_agent: QAgent) -> None:
    """Test get_init_file_name returns None."""
    assert q_agent.get_init_file_name() is None


def test_get_init_command(q_agent: QAgent) -> None:
    """Test get_init_command returns None."""
    assert q_agent.get_init_command() is None


def test_get_result_file_name(q_agent: QAgent) -> None:
    """Test get_result_file_name returns the correct filename."""
    assert q_agent.get_result_file_name() == "q_result.json"


def test_supports_mcp(q_agent: QAgent) -> None:
    """Test supports_mcp returns False."""
    assert not q_agent.supports_mcp()


def test_get_mcp_file_name(q_agent: QAgent) -> None:
    """Test get_mcp_file_name returns None."""
    assert q_agent.get_mcp_file_name() is None


@pytest.mark.asyncio
async def test_initialize(q_agent: QAgent) -> None:
    """Test initialize method returns a success CommandResult without doing anything."""
    result = await q_agent.initialize("any command", "/fake/dir")
    assert isinstance(result, CommandResult)
    assert result.status
    assert result.result == "Q agent does not require initialization."


@pytest.mark.asyncio
@patch("awa.core.activities.agent_modes.q_agent.CommandUtils.run_command_async")
async def test_execute_prompt(mock_run_command: AsyncMock, q_agent: QAgent) -> None:
    """Test execute_prompt constructs command and calls run_command_async."""
    mock_run_command.return_value = (True, "output from q")
    prompt = "what is aws q?"
    working_dir = "/fake/dir"
    result = await q_agent.execute_prompt(prompt, working_dir)

    expected_command = "q chat --no-interactive --trust-all-tools 'what is aws q?'"
    mock_run_command.assert_called_once_with(expected_command, working_dir, shell=False)
    assert result.status
    assert result.result == "output from q"
    assert result.content == "output from q"


@pytest.mark.asyncio
async def test_execute_command(q_agent: QAgent) -> None:
    """Test execute_command calls execute_prompt with the correct prompt."""
    command_file = "my_prompt.txt"
    working_dir = "/fake/dir"
    mcp_tools = ["tool1"]

    with patch.object(q_agent, "execute_prompt", new_callable=AsyncMock) as mock_execute_prompt:
        mock_execute_prompt.return_value = CommandResult(status=True, result="mocked result")
        await q_agent.execute_command(command_file, working_dir, mcp_tools)
        mock_execute_prompt.assert_called_once_with(
            f"Read the content from this file {command_file} and execute",
            working_dir,
            mcp_tools,
        )


@pytest.mark.asyncio
async def test_configure_mcp(q_agent: QAgent) -> None:
    """Test configure_mcp returns None as it's not supported."""
    result = await q_agent.configure_mcp("/fake/dir", "{}")
    assert result is None


def test_process_q_output_simple(q_agent: QAgent) -> None:
    """Test _process_q_output with simple text."""
    status = True
    result_text = "This is a simple response."
    command_result = q_agent._process_q_output(status, result_text)
    assert command_result.status == status
    assert command_result.result == result_text
    assert command_result.content == "This is a simple response."


def test_process_q_output_with_ansi_codes(q_agent: QAgent) -> None:
    """Test _process_q_output removes ANSI escape codes."""
    status = True
    result_text = "\x1b[32mSuccess:\x1b[0m The command completed."
    command_result = q_agent._process_q_output(status, result_text)
    assert command_result.status == status
    assert command_result.result == result_text
    assert command_result.content == "Success: The command completed."


def test_process_q_output_with_logo(q_agent: QAgent) -> None:
    """Test _process_q_output removes the Q logo footer."""
    status = True
    result_text = "Here is the answer.\n\n\n⢠⣶⣶⣦ some logo stuff"
    command_result = q_agent._process_q_output(status, result_text)
    assert command_result.status == status
    assert command_result.result == result_text
    assert command_result.content == "Here is the answer."


def test_process_q_output_with_leading_prompt_char(q_agent: QAgent) -> None:
    """Test _process_q_output removes the leading '> ' characters."""
    status = True
    result_text = "> This is the Q response."
    command_result = q_agent._process_q_output(status, result_text)
    assert command_result.status == status
    assert command_result.result == result_text
    assert command_result.content == "This is the Q response."


def test_process_q_output_complex(q_agent: QAgent) -> None:
    """Test _process_q_output with a complex string containing everything."""
    status = True
    result_text = "> \x1b[32mHere is the answer.\x1b[0m\n\n\n⢠⣶⣶⣦ some logo stuff"
    command_result = q_agent._process_q_output(status, result_text)
    assert command_result.status == status
    assert command_result.result == result_text
    assert command_result.content == "Here is the answer."


@pytest.mark.asyncio
async def test_get_log_files(q_agent: QAgent) -> None:
    """Test get_log_files does nothing."""
    # This method is a no-op, so we just call it to ensure it doesn't crash.
    await q_agent.get_log_files()


@pytest.mark.asyncio
async def test_cleanup(q_agent: QAgent) -> None:
    """Test cleanup does nothing."""
    # This method is a no-op, so we just call it to ensure it doesn't crash.
    await q_agent.cleanup()
