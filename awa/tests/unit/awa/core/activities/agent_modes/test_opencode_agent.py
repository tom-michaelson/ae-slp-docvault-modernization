"""Unit tests for OpenCodeAgent."""

from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.agent_modes.opencode_agent import OpenCodeAgent


@pytest.fixture
def opencode_agent() -> OpenCodeAgent:
    """Fixture to provide an OpenCodeAgent instance."""
    return OpenCodeAgent()


def test_get_init_file_name(opencode_agent: OpenCodeAgent) -> None:
    """Test get_init_file_name returns empty string."""
    assert opencode_agent.get_init_file_name() == ""


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_command(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_command formats the command correctly and calls execute_prompt."""
    mock_run_command.return_value = (True, "Command executed successfully")
    command = "my_command.txt"
    working_dir = "/fake/dir"
    mcp_tools = ["tool1", "tool2"]
    session_id = "test-session"

    with patch.object(opencode_agent, "execute_prompt", new_callable=AsyncMock) as mock_execute_prompt:
        mock_execute_prompt.return_value = mock_run_command.return_value
        await opencode_agent.execute_command(command, working_dir, mcp_tools, session_id)

        expected_formatted_command = f"Read the content from this file {command} and execute"
        mock_execute_prompt.assert_called_once_with(expected_formatted_command, working_dir, mcp_tools)


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_success(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_prompt formats the command correctly and handles success case."""
    mock_run_command.return_value = (True, "Prompt executed successfully")
    prompt = "Write a hello world program"
    working_dir = "/fake/dir"
    mcp_tools = ["tool1"]
    session_id = "test-session"

    result = await opencode_agent.execute_prompt(prompt, working_dir, mcp_tools, session_id)

    expected_command = f'opencode -p "{prompt}"'
    mock_run_command.assert_called_once_with(  # noqa: S604
        command=expected_command,
        working_dir=working_dir,
        shell=True,
    )
    assert result.status
    assert result.result == "Prompt executed successfully"


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_failure(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_prompt handles command failure correctly."""
    mock_run_command.return_value = (False, "Command failed")
    prompt = "Write a hello world program"
    working_dir = "/fake/dir"

    result = await opencode_agent.execute_prompt(prompt, working_dir)

    expected_command = f'opencode -p "{prompt}"'
    mock_run_command.assert_called_once_with(  # noqa: S604
        command=expected_command,
        working_dir=working_dir,
        shell=True,
    )
    assert not result.status
    assert result.result == "Command failed"


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_api_error(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_prompt handles API error by setting status to False."""
    mock_run_command.return_value = (True, "API Error: Authentication failed")
    prompt = "Write a hello world program"
    working_dir = "/fake/dir"

    result = await opencode_agent.execute_prompt(prompt, working_dir)

    expected_command = f'opencode -p "{prompt}"'
    mock_run_command.assert_called_once_with(  # noqa: S604
        command=expected_command,
        working_dir=working_dir,
        shell=True,
    )
    assert not result.status  # Should be False due to API Error
    assert result.result == "API Error: Authentication failed"


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_api_error_partial_match(
    mock_run_command: AsyncMock,
    opencode_agent: OpenCodeAgent,
) -> None:
    """Test execute_prompt handles various API error formats."""
    mock_run_command.return_value = (True, "API Error: Rate limit exceeded")
    prompt = "Write a hello world program"

    result = await opencode_agent.execute_prompt(prompt)

    assert not result.status  # Should be False due to API Error
    assert result.result == "API Error: Rate limit exceeded"


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_no_working_dir(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_prompt works without working directory."""
    mock_run_command.return_value = (True, "Success")
    prompt = "Write a hello world program"

    result = await opencode_agent.execute_prompt(prompt)

    expected_command = f'opencode -p "{prompt}"'
    mock_run_command.assert_called_once_with(  # noqa: S604
        command=expected_command,
        working_dir=None,
        shell=True,
    )
    assert result.status
    assert result.result == "Success"


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_with_quotes_in_prompt(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_prompt handles quotes in prompt correctly."""
    mock_run_command.return_value = (True, "Success with quotes")
    prompt = 'Write a program that prints "Hello World"'

    result = await opencode_agent.execute_prompt(prompt)

    expected_command = f'opencode -p "{prompt}"'
    mock_run_command.assert_called_once_with(  # noqa: S604
        command=expected_command,
        working_dir=None,
        shell=True,
    )
    assert result.status
    assert result.result == "Success with quotes"


@pytest.mark.asyncio
async def test_get_log_files_empty_implementation(opencode_agent: OpenCodeAgent) -> None:
    """Test get_log_files has empty implementation."""
    # Test that it doesn't raise an exception and returns None
    result = await opencode_agent.get_log_files("/fake/dir", "session-id")
    assert result is None


@pytest.mark.asyncio
async def test_get_log_files_no_args(opencode_agent: OpenCodeAgent) -> None:
    """Test get_log_files works with no arguments."""
    result = await opencode_agent.get_log_files()
    assert result is None


@pytest.mark.asyncio
async def test_cleanup_empty_implementation(opencode_agent: OpenCodeAgent) -> None:
    """Test cleanup has empty implementation."""
    # Test that it doesn't raise an exception and returns None
    result = await opencode_agent.cleanup("session-id")
    assert result is None


@pytest.mark.asyncio
async def test_cleanup_no_session_id(opencode_agent: OpenCodeAgent) -> None:
    """Test cleanup works without session_id."""
    result = await opencode_agent.cleanup()
    assert result is None


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_command_with_all_params(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_command with all parameters provided."""
    mock_run_command.return_value = (True, "All params test successful")
    command = "test_command.txt"
    working_dir = "/test/dir"
    mcp_tools = ["tool1", "tool2", "tool3"]
    session_id = "test-session-all-params"

    with patch.object(opencode_agent, "execute_prompt", new_callable=AsyncMock) as mock_execute_prompt:
        mock_execute_prompt.return_value = mock_run_command.return_value
        await opencode_agent.execute_command(command, working_dir, mcp_tools, session_id)

        expected_formatted_command = f"Read the content from this file {command} and execute"
        mock_execute_prompt.assert_called_once_with(expected_formatted_command, working_dir, mcp_tools)


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_with_all_params(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_prompt with all parameters provided."""
    mock_run_command.return_value = (True, "All params prompt test successful")
    prompt = "Create a comprehensive test suite"
    working_dir = "/test/dir"
    mcp_tools = ["tool1", "tool2", "tool3"]
    session_id = "test-session-all-params"

    result = await opencode_agent.execute_prompt(prompt, working_dir, mcp_tools, session_id)

    expected_command = f'opencode -p "{prompt}"'
    mock_run_command.assert_called_once_with(  # noqa: S604
        command=expected_command,
        working_dir=working_dir,
        shell=True,
    )
    assert result.status
    assert result.result == "All params prompt test successful"


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_command_utils_exception(
    mock_run_command: AsyncMock,
    opencode_agent: OpenCodeAgent,
) -> None:
    """Test execute_prompt handles CommandUtils exceptions gracefully."""
    mock_run_command.side_effect = Exception("Command execution failed")
    prompt = "Test exception handling"

    with pytest.raises(Exception, match="Command execution failed"):
        await opencode_agent.execute_prompt(prompt)


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_empty_result(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_prompt handles empty result correctly."""
    mock_run_command.return_value = (True, "")
    prompt = "Test empty result"

    result = await opencode_agent.execute_prompt(prompt)

    assert result.status
    assert result.result == ""


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_api_error_case_insensitive(
    mock_run_command: AsyncMock,
    opencode_agent: OpenCodeAgent,
) -> None:
    """Test execute_prompt API error detection is case sensitive (should only match exact case)."""
    # Test that it only matches exact case "API Error:"
    mock_run_command.return_value = (True, "api error: something went wrong")
    prompt = "Test case sensitivity"

    result = await opencode_agent.execute_prompt(prompt)

    # Should NOT be treated as API error because it's lowercase
    assert result.status
    assert result.result == "api error: something went wrong"


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_api_error_exact_match(mock_run_command: AsyncMock, opencode_agent: OpenCodeAgent) -> None:
    """Test execute_prompt API error detection with exact match."""
    mock_run_command.return_value = (True, "API Error: Exact match test")
    prompt = "Test exact match"

    result = await opencode_agent.execute_prompt(prompt)

    # Should be treated as API error
    assert not result.status
    assert result.result == "API Error: Exact match test"
