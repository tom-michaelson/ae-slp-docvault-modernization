from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.command_utils import CommandUtils
from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase, CommandResult

logger = get_logger(LoggerComponent.ACTIVITY)


class OpenCodeAgent(AgentModeBase):
    """OpenCode agent implementation for executing OpenCode CLI commands.

    This agent handles initialization and command execution through the OpenCode CLI,
    managing subprocess execution and output handling.
    """

    def get_init_file_name(self) -> str:
        return ""

    async def execute_command(
        self,
        command: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,  # noqa: ARG002
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        formatted_command: str = f"Read the content from this file {command} and execute"
        return await self.execute_prompt(formatted_command, working_dir, mcp_tools)

    async def execute_prompt(
        self,
        prompt: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,  # noqa: ARG002
        session_id: str | None = None,  # noqa: ARG002
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        formatted_command: str = f'opencode -p "{prompt}"'

        logger.debug(f"Executing command (cwd: {working_dir}): {formatted_command}")

        status, result = await CommandUtils.run_command_async(  # noqa: S604
            command=formatted_command,
            working_dir=working_dir,
            shell=True,
        )

        if result.startswith("API Error:"):
            status = False

        return CommandResult(status=status, result=result)

    async def get_log_files(
        self,
        working_dir: str | None = None,
        session_id: str | None = None,
    ) -> None:
        pass

    async def stream_output(
        self,
        prompt: str | None = None,
        command_path: str | None = None,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        **kwargs,  # noqa: ANN003, ARG002
    ) -> CommandResult:
        """Stream live output from an ongoing OpenCode agent execution.

        OpenCode CLI does not currently support streaming output, so this method
        falls back to execute_prompt with the full result returned at once.

        Args:
            prompt: The prompt to send to OpenCode (if applicable).
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

        # Opencode doesn't support streaming, so we execute the prompt normally
        return await self.execute_prompt(actual_prompt, working_dir, mcp_tools, session_id)

    async def cleanup(self, session_id: str | None = None) -> None:
        pass
