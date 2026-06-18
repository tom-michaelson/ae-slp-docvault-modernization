"""GitHub Copilot CLI agent implementation."""

import re

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.command_utils import CommandUtils
from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase, CommandResult

logger = get_logger(LoggerComponent.ACTIVITY)


class GithubCopilotAgent(AgentModeBase):
    """GitHub Copilot CLI agent implementation.

    Executes prompts using the GitHub Copilot CLI.
    Requires GitHub Copilot CLI installed: npm install -g @github/copilot

    Authentication is handled by the GitHub Copilot CLI itself.
    Ensure you've authenticated via: gh auth login
    """

    def get_init_file_name(self) -> str:
        """Return the initialization file name (empty for GitHub Copilot)."""
        return ""

    def _clean_output(self, output: str) -> str:
        """Clean GitHub Copilot CLI output by removing debug messages and usage statistics.

        Args:
            output: Raw output from GitHub Copilot CLI

        Returns:
            Cleaned output with only the relevant content

        """
        lines = output.split("\n")
        cleaned_lines = []

        # Track if we've hit the usage statistics section
        in_usage_section = False

        for line in lines:
            # Skip debug messages
            if line.strip().startswith("🔥 AGENT DEBUG:"):
                continue

            # Detect start of usage statistics section
            if re.match(r"^(Total usage|Total duration|Total code changes|Usage by model)", line.strip()):
                in_usage_section = True
                continue

            # Skip lines in usage section
            if in_usage_section:
                continue

            # Keep all other lines
            cleaned_lines.append(line)

        # Join lines and strip leading/trailing whitespace
        cleaned_output = "\n".join(cleaned_lines).strip()

        return cleaned_output

    async def execute_command(
        self,
        command: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        """Execute a command file by reading and executing its contents.

        Args:
            command: Path to the command file
            working_dir: Working directory for execution
            mcp_tools: MCP tools to use (unused)
            session_id: Session ID (unused)
            stream_enabled: Whether to enable streaming output (unused)

        Returns:
            CommandResult with status and output

        """
        formatted_command = f"Read the content from this file {command} and execute"
        return await self.execute_prompt(formatted_command, working_dir, mcp_tools, session_id)

    async def execute_prompt(
        self,
        prompt: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,  # noqa: ARG002
        session_id: str | None = None,  # noqa: ARG002
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        """Execute a prompt using GitHub Copilot CLI.

        Args:
            prompt: The prompt to execute
            working_dir: Working directory for execution
            mcp_tools: MCP tools to use (unused)
            session_id: Session ID (unused)
            stream_enabled: Whether to enable streaming output (unused)

        Returns:
            CommandResult with status and output

        """
        # Collapse multi-line prompts to single line
        single_line_prompt = " ".join(prompt.strip().split())

        # Format command with --allow-all-tools for non-interactive execution
        formatted_command = f'copilot -p "{single_line_prompt}" --allow-all-tools'

        logger.debug(f"Executing GitHub Copilot command (cwd: {working_dir}): {formatted_command}")

        # Execute command (GitHub Copilot CLI handles authentication)
        status, result = await CommandUtils.run_command_async(  # noqa: S604
            command=formatted_command,
            working_dir=working_dir,
            shell=True,
        )

        # Clean the output to remove debug messages and usage statistics
        cleaned_result = self._clean_output(result)

        # Detect common error patterns in output
        error_patterns = ["API Error:", "Error:", "authentication failed", "not authenticated"]
        if any(error_pattern in cleaned_result for error_pattern in error_patterns):
            status = False
            logger.error(f"GitHub Copilot command failed with error: {cleaned_result}")

        return CommandResult(status=status, result=cleaned_result)

    async def stream_output(
        self,
        prompt: str | None = None,
        command_path: str | None = None,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        **kwargs,  # noqa: ANN003, ARG002
    ) -> CommandResult:
        """Stream live output from an ongoing GitHub Copilot CLI agent execution.

        GitHub Copilot CLI does not currently support streaming output, so this method
        falls back to execute_prompt with the full result returned at once.

        Args:
            prompt: The prompt to send to GitHub Copilot (if applicable).
            command_path: Path to the command or script to execute (if applicable).
            working_dir: The working directory for agent execution.
            mcp_tools: List of allowed MCP tools for the agent (not currently supported).
            session_id: Unique identifier for the agent session to stream from.
            **kwargs: Additional agent-specific parameters.

        Returns:
            CommandResult: Contains output and session status.

        """
        # Determine the prompt to use
        if prompt:
            actual_prompt = prompt
        elif command_path:
            actual_prompt = f"Read the content from this file {command_path} and execute"
        else:
            actual_prompt = "Please provide a simple response to test functionality."

        # GitHub Copilot CLI doesn't support streaming, so we execute the prompt normally
        return await self.execute_prompt(actual_prompt, working_dir, mcp_tools, session_id)

    async def get_log_files(
        self,
        working_dir: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """Get log files (no-op for GitHub Copilot)."""

    async def cleanup(self, session_id: str | None = None) -> None:
        """Clean up resources (no-op for GitHub Copilot)."""
