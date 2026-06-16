"""Unit tests for GitHub Copilot CLI agent."""

from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.agent_modes.github_copilot_agent import GithubCopilotAgent
from awa.sdk.models.agent_modes.agent_mode_base import CommandResult


@pytest.fixture
def github_copilot_agent() -> GithubCopilotAgent:
    """Fixture for GitHub Copilot agent instance."""
    return GithubCopilotAgent()


class TestGithubCopilotAgent:
    """Test suite for GitHub Copilot CLI agent."""

    def test_get_init_file_name(self, github_copilot_agent) -> None:
        """Test that init file name is empty."""
        assert github_copilot_agent.get_init_file_name() == ""

    def test_clean_output_removes_debug_and_stats(self, github_copilot_agent) -> None:
        """Test that _clean_output removes debug messages and usage statistics."""
        raw_output = """🔥 AGENT DEBUG: Used GithubCopilotAgent for provider=github_copilot, mode=analyze
● Here's a rhyming 3-stanza poem featuring a llama, exploding, and sogginess:

   **The Soggy Llama's Tale**

   A llama stood in morning rain so soggy,
   Its woolly coat all damp and slightly groggy,
   It munched on hay beside a puddle's edge,
   While water dripped from every grassy hedge.

   The llama found a barrel, round and red,
   "What could be in this thing?" the creature said,
   It nudged the top—the lid began to fly—
   A burst of confetti filled the sky!

   The barrel did explode with quite a boom,
   Now soggy bits of paper filled the gloom,
   The llama sneezed and shook its dripping head,
   Then wandered off to find a barn instead.



Total usage est:       1 Premium request
Total duration (API):  7.6s
Total duration (wall): 9.0s
Total code changes:    0 lines added, 0 lines removed
Usage by model:
    claude-sonnet-4.5    20.0k input, 187 output, 2.1k cache read, 17.9k cache write (Est. 1 Premium request)"""

        cleaned = github_copilot_agent._clean_output(raw_output)

        # Should not contain debug message
        assert "🔥 AGENT DEBUG:" not in cleaned
        assert "Used GithubCopilotAgent" not in cleaned

        # Should not contain usage statistics
        assert "Total usage est:" not in cleaned
        assert "Total duration" not in cleaned
        assert "Total code changes:" not in cleaned
        assert "Usage by model:" not in cleaned
        assert "claude-sonnet-4.5" not in cleaned

        # Should contain the actual content
        assert "The Soggy Llama's Tale" in cleaned
        assert "A llama stood in morning rain so soggy" in cleaned
        assert "Then wandered off to find a barn instead." in cleaned

    def test_clean_output_preserves_content_without_metadata(
        self,
        github_copilot_agent,
    ) -> None:
        """Test that _clean_output preserves content when there's no metadata."""
        raw_output = "Simple output without any metadata"
        cleaned = github_copilot_agent._clean_output(raw_output)
        assert cleaned == "Simple output without any metadata"

    @pytest.mark.asyncio
    async def test_execute_command_delegates_to_execute_prompt(
        self,
        github_copilot_agent,
    ) -> None:
        """Test that execute_command formats and delegates to execute_prompt."""
        with patch.object(
            github_copilot_agent,
            "execute_prompt",
            new_callable=AsyncMock,
        ) as mock_execute:
            mock_execute.return_value = CommandResult(status=True, result="success")

            result = await github_copilot_agent.execute_command(
                command="commands.txt",
                working_dir="/test/dir",
            )

            mock_execute.assert_called_once_with(
                "Read the content from this file commands.txt and execute",
                "/test/dir",
                None,
                None,
            )
            assert result.status is True

    @pytest.mark.asyncio
    async def test_execute_prompt_success(self, github_copilot_agent) -> None:
        """Test execute_prompt with successful execution."""
        with patch(
            "awa.core.utils.command_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = (True, "Code executed successfully")

            result = await github_copilot_agent.execute_prompt(
                prompt="Fix the bug in main.py",
                working_dir="/test/dir",
            )

            # Verify command format
            call_args = mock_run.call_args
            assert 'copilot -p "Fix the bug in main.py" --allow-all-tools' in call_args.kwargs["command"]
            assert call_args.kwargs["working_dir"] == "/test/dir"
            assert call_args.kwargs["shell"] is True

            assert result.status is True
            assert result.result == "Code executed successfully"

    @pytest.mark.asyncio
    async def test_execute_prompt_multiline_prompt(self, github_copilot_agent) -> None:
        """Test that multi-line prompts are collapsed to single line."""
        with patch(
            "awa.core.utils.command_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = (True, "Success")

            multiline_prompt = """
            Fix the bug
            in main.py
            and test it
            """

            await github_copilot_agent.execute_prompt(
                prompt=multiline_prompt,
                working_dir="/test",
            )

            # Verify prompt collapsed to single line
            command = mock_run.call_args.kwargs["command"]
            assert 'copilot -p "Fix the bug in main.py and test it"' in command

    @pytest.mark.asyncio
    async def test_execute_prompt_detects_api_error(self, github_copilot_agent) -> None:
        """Test that API errors are detected in output."""
        with patch(
            "awa.core.utils.command_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = (True, "API Error: Rate limit exceeded")

            result = await github_copilot_agent.execute_prompt(
                prompt="Test",
                working_dir="/test",
            )

            assert result.status is False
            assert "API Error:" in result.result

    @pytest.mark.asyncio
    async def test_execute_prompt_detects_auth_error(self, github_copilot_agent) -> None:
        """Test that authentication errors are detected."""
        with patch(
            "awa.core.utils.command_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = (True, "Error: authentication failed")

            result = await github_copilot_agent.execute_prompt(
                prompt="Test",
                working_dir="/test",
            )

            assert result.status is False

    @pytest.mark.asyncio
    async def test_get_log_files_noop(self, github_copilot_agent) -> None:
        """Test that get_log_files is a no-op."""
        result = await github_copilot_agent.get_log_files(
            working_dir="/test",
            session_id="test_session",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_noop(self, github_copilot_agent) -> None:
        """Test that cleanup is a no-op."""
        result = await github_copilot_agent.cleanup(session_id="test_session")
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_prompt_detects_generic_error(self, github_copilot_agent) -> None:
        """Test that generic 'Error:' prefix is detected."""
        with patch(
            "awa.core.utils.command_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = (True, "Error: Something went wrong")

            result = await github_copilot_agent.execute_prompt(
                prompt="Test",
                working_dir="/test",
            )

            assert result.status is False
            assert "Error:" in result.result

    @pytest.mark.asyncio
    async def test_execute_prompt_detects_not_authenticated_error(
        self,
        github_copilot_agent,
    ) -> None:
        """Test that 'not authenticated' error is detected."""
        with patch(
            "awa.core.utils.command_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = (True, "You are not authenticated with GitHub")

            result = await github_copilot_agent.execute_prompt(
                prompt="Test",
                working_dir="/test",
            )

            assert result.status is False

    @pytest.mark.asyncio
    async def test_execute_prompt_command_execution_failure(
        self,
        github_copilot_agent,
    ) -> None:
        """Test that command execution failures are properly handled."""
        with patch(
            "awa.core.utils.command_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_run:
            mock_run.return_value = (False, "Command not found")

            result = await github_copilot_agent.execute_prompt(
                prompt="Test",
                working_dir="/test",
            )

            assert result.status is False
            assert result.result == "Command not found"

    @pytest.mark.asyncio
    async def test_stream_output_with_prompt(self, github_copilot_agent) -> None:
        """Test stream_output delegates to execute_prompt with a prompt."""
        with patch.object(
            github_copilot_agent,
            "execute_prompt",
            new_callable=AsyncMock,
        ) as mock_execute:
            mock_execute.return_value = CommandResult(status=True, result="Success")

            result = await github_copilot_agent.stream_output(
                prompt="Test prompt",
                working_dir="/test/dir",
                mcp_tools=["tool1"],
                session_id="test-session",
            )

            mock_execute.assert_called_once_with(
                "Test prompt",
                "/test/dir",
                ["tool1"],
                "test-session",
            )
            assert result.status is True
            assert result.result == "Success"

    @pytest.mark.asyncio
    async def test_stream_output_with_command_path(self, github_copilot_agent) -> None:
        """Test stream_output delegates to execute_prompt with a command path."""
        with patch.object(
            github_copilot_agent,
            "execute_prompt",
            new_callable=AsyncMock,
        ) as mock_execute:
            mock_execute.return_value = CommandResult(status=True, result="Executed")

            result = await github_copilot_agent.stream_output(
                command_path="/path/to/command.txt",
                working_dir="/test/dir",
            )

            mock_execute.assert_called_once_with(
                "Read the content from this file /path/to/command.txt and execute",
                "/test/dir",
                None,
                None,
            )
            assert result.status is True

    @pytest.mark.asyncio
    async def test_stream_output_with_neither_prompt_nor_command(
        self,
        github_copilot_agent,
    ) -> None:
        """Test stream_output uses default prompt when neither prompt nor command is provided."""
        with patch.object(
            github_copilot_agent,
            "execute_prompt",
            new_callable=AsyncMock,
        ) as mock_execute:
            mock_execute.return_value = CommandResult(status=True, result="Default")

            result = await github_copilot_agent.stream_output(
                working_dir="/test/dir",
                session_id="test-session",
            )

            # Should use default fallback prompt
            call_args = mock_execute.call_args
            assert "test" in call_args[0][0].lower()
            assert result.status is True
