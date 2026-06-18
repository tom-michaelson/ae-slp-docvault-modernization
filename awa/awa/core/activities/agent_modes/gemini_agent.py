import json

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.command_utils import CommandUtils
from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase, CommandResult

logger = get_logger(LoggerComponent.ACTIVITY)


class GeminiAgent(AgentModeBase):
    """Gemini agent implementation for executing Gemini CLI commands.

    This agent handles command and prompt execution through the Gemini CLI,
    managing subprocess execution and output handling.
    """

    async def execute_command(
        self,
        command: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,  # noqa: ARG002
        session_id: str | None = None,  # noqa: ARG002
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        """Execute a command using the Gemini CLI.

        Args:
            command: The command to execute
            working_dir: The working directory to execute the command in
            mcp_tools: MCP tools to use (not currently supported for Gemini)
            session_id: Session ID for this execution (not currently supported for Gemini)
            stream_enabled: Whether to enable streaming output (not currently supported for Gemini)

        Returns:
            CommandResult with status and output

        """
        formatted_command = f'gemini -p "{command}" --output-format json'
        return await self._execute_gemini_command(formatted_command, working_dir)

    async def execute_prompt(
        self,
        prompt: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,  # noqa: ARG002
        session_id: str | None = None,  # noqa: ARG002
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        """Execute a prompt using the Gemini CLI.

        Args:
            prompt: The prompt to execute
            working_dir: The working directory to execute the prompt in
            mcp_tools: MCP tools to use (not currently supported for Gemini)
            session_id: Session ID for this execution (not currently supported for Gemini)
            stream_enabled: Whether to enable streaming output (not currently supported for Gemini)

        Returns:
            CommandResult with status and output

        """
        # Clean up the prompt - it might be multiple lines and we want a single line
        prompt = " ".join(prompt.splitlines())

        formatted_command = f'gemini -p "{prompt}" --output-format json'
        return await self._execute_gemini_command(formatted_command, working_dir)

    async def _execute_gemini_command(
        self,
        command: str,
        working_dir: str | None = None,
    ) -> CommandResult:
        """Execute a Gemini CLI command.

        Args:
            command: The formatted Gemini CLI command to execute
            working_dir: The working directory to execute in

        Returns:
            CommandResult with status and output

        """
        logger.debug(f"Executing Gemini command (cwd: {working_dir}): {command}")

        status, result = await CommandUtils.run_command_async(  # noqa: S604
            command=command,
            working_dir=working_dir,
            shell=True,
        )

        logger.debug(f"Gemini command result: {result}")
        return self._process_gemini_output(status, result)

    def _process_gemini_output(self, status: bool, result: str) -> CommandResult:
        """Process Gemini CLI output to extract clean response.

        Args:
            status: The command execution status
            result: The raw output from Gemini CLI

        Returns:
            CommandResult with extracted content and cleaned result

        """
        logger.debug(f"Raw output from Gemini agent: {result}")
        content: str | None = None

        try:
            # Split output by newlines and find the JSON part (before debug logs)
            lines = result.strip().split("\n")
            json_lines = []

            # Collect lines until we hit debug logs
            for line in lines:
                if line.startswith(("[DEBUG]", "Flushing", "Clearcut", "Session ID:")):
                    break
                json_lines.append(line)

            # Join the JSON lines and parse
            json_str = "\n".join(json_lines).strip()
            if json_str:
                gemini_data = json.loads(json_str)

                # Extract the response field
                if "response" in gemini_data and isinstance(gemini_data["response"], str):
                    content = gemini_data["response"]

                # Store the full parsed data as result
                result = json.dumps(gemini_data, indent=2)
            else:
                status = False
                result = "No JSON output found in Gemini response"

        except json.JSONDecodeError as e:
            status = False
            result = f"Error parsing JSON result from Gemini: {e}\n\nResult:\n{result}"
        except Exception as e:  # noqa: BLE001
            status = False
            result = f"Error processing Gemini output: {e}\n\nResult:\n{result}"

        return CommandResult(status=status, result=result, content=content)

    async def get_log_files(
        self,
        working_dir: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """Get log files from the Gemini agent.

        Gemini CLI does not currently provide a dedicated log export mechanism.
        This method is a no-op for now but is required by the AgentModeBase interface.

        Args:
            working_dir: The working directory (unused)
            session_id: Session ID (unused)

        """
        # Gemini doesn't have a native log export command
        # Session history is managed through checkpointing but not explicitly exported

    async def stream_output(
        self,
        prompt: str | None = None,
        command_path: str | None = None,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        **kwargs,  # noqa: ANN003, ARG002
    ) -> CommandResult:
        """Stream live output from an ongoing Gemini agent execution.

        Gemini CLI does not currently support streaming output, so this method
        falls back to execute_prompt with the full result returned at once.

        Args:
            prompt: The prompt to send to Gemini (if applicable).
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

        # Gemini doesn't support streaming, so we execute the prompt normally
        return await self.execute_prompt(actual_prompt, working_dir, mcp_tools, session_id)

    async def cleanup(self, session_id: str | None = None) -> None:
        """Clean up the Gemini agent session.

        Gemini CLI does not require explicit session cleanup.
        Session management is handled through checkpointing but does not require
        manual cleanup commands. This method is a no-op but is required by
        the AgentModeBase interface.

        Args:
            session_id: Session ID to clean up (unused)

        """
        # Gemini doesn't require explicit session cleanup
        # Sessions are managed through checkpointing
