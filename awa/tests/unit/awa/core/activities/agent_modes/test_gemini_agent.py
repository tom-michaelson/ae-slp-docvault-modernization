"""Unit tests for GeminiAgent."""

from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.agent_modes.gemini_agent import GeminiAgent


@pytest.fixture
def gemini_agent() -> GeminiAgent:
    """Fixture to provide a GeminiAgent instance."""
    return GeminiAgent()


@pytest.mark.asyncio
@patch("awa.core.activities.agent_modes.gemini_agent.GeminiAgent._execute_gemini_command")
async def test_execute_command(mock_execute: AsyncMock, gemini_agent: GeminiAgent) -> None:
    """Test execute_command formats the command correctly."""
    command = "analyze this code"
    await gemini_agent.execute_command(command, "/fake/dir")

    expected_command = f'gemini -p "{command}" --output-format json'
    mock_execute.assert_called_once_with(expected_command, "/fake/dir")


@pytest.mark.asyncio
@patch("awa.core.activities.agent_modes.gemini_agent.GeminiAgent._execute_gemini_command")
async def test_execute_prompt(mock_execute: AsyncMock, gemini_agent: GeminiAgent) -> None:
    """Test execute_prompt formats the prompt correctly and cleans multiline."""
    prompt = "tell me a story\nabout gemini"
    await gemini_agent.execute_prompt(prompt, "/fake/dir")

    cleaned_prompt = "tell me a story about gemini"
    expected_command = f'gemini -p "{cleaned_prompt}" --output-format json'
    mock_execute.assert_called_once_with(expected_command, "/fake/dir")


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_gemini_command_success(
    mock_run_command: AsyncMock,
    gemini_agent: GeminiAgent,
) -> None:
    """Test _execute_gemini_command with a successful command and valid JSON response."""
    gemini_output = """{
  "response": "This is the poem response",
  "stats": {
    "models": {
      "gemini-2.5-pro": {
        "tokens": {
          "prompt": 100,
          "candidates": 50
        }
      }
    }
  }
}
[DEBUG] CLI: Some debug message
Session ID: test-123"""
    mock_run_command.return_value = (True, gemini_output)
    result = await gemini_agent._execute_gemini_command("gemini test", "/fake/dir")

    assert result.status
    assert result.content == "This is the poem response"
    assert "response" in result.result
    assert "[DEBUG]" not in result.result  # Debug logs should be stripped
    mock_run_command.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_gemini_command_failure(
    mock_run_command: AsyncMock,
    gemini_agent: GeminiAgent,
) -> None:
    """Test _execute_gemini_command with a failed command."""
    mock_run_command.return_value = (False, "Error: Command failed")
    result = await gemini_agent._execute_gemini_command("gemini test", "/fake/dir")

    assert not result.status
    assert "Error parsing JSON result from Gemini" in result.result


def test_process_gemini_output_success(gemini_agent: GeminiAgent) -> None:
    """Test _process_gemini_output with valid JSON response."""
    raw_output = """{
  "response": "A fluffy llama poem",
  "stats": {
    "models": {
      "gemini-2.5-pro": {
        "tokens": {
          "prompt": 7378,
          "candidates": 132
        }
      }
    }
  }
}
[DEBUG] CLI: Delegating hierarchical memory
Session ID: 6da0af7e"""

    result = gemini_agent._process_gemini_output(status=True, result=raw_output)

    assert result.status
    assert result.content == "A fluffy llama poem"
    assert "[DEBUG]" not in result.result
    assert "Session ID:" not in result.result
    assert "response" in result.result


def test_process_gemini_output_invalid_json(gemini_agent: GeminiAgent) -> None:
    """Test _process_gemini_output with invalid JSON."""
    raw_output = "This is not JSON"

    result = gemini_agent._process_gemini_output(status=True, result=raw_output)

    assert not result.status
    assert "Error parsing JSON result from Gemini" in result.result
    assert result.content is None


def test_process_gemini_output_no_response_field(gemini_agent: GeminiAgent) -> None:
    """Test _process_gemini_output when JSON is valid but has no response field."""
    raw_output = '{"stats": {"models": {}}}'

    result = gemini_agent._process_gemini_output(status=True, result=raw_output)

    assert result.status
    assert result.content is None  # No response field, so content should be None
    assert "stats" in result.result


def test_process_gemini_output_empty_output(gemini_agent: GeminiAgent) -> None:
    """Test _process_gemini_output with empty output."""
    raw_output = "[DEBUG] Only debug logs"

    result = gemini_agent._process_gemini_output(status=True, result=raw_output)

    assert not result.status
    assert result.result == "No JSON output found in Gemini response"
    assert result.content is None


@pytest.mark.asyncio
async def test_get_log_files(gemini_agent: GeminiAgent) -> None:
    """Test get_log_files is a no-op (Gemini doesn't support log export)."""
    # Should not raise any errors
    await gemini_agent.get_log_files("/fake/dir", "test-session")


@pytest.mark.asyncio
async def test_cleanup(gemini_agent: GeminiAgent) -> None:
    """Test cleanup is a no-op (Gemini doesn't require explicit cleanup)."""
    # Should not raise any errors
    await gemini_agent.cleanup("test-session")


@pytest.mark.asyncio
async def test_cleanup_no_session_id(gemini_agent: GeminiAgent) -> None:
    """Test cleanup does nothing if no session_id is provided."""
    # Should not raise any errors
    await gemini_agent.cleanup(None)
