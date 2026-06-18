from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.command_utils import CommandUtils
from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase, CommandResult

logger = get_logger(LoggerComponent.ACTIVITY)


class GooseAgent(AgentModeBase):
    """Goose agent implementation for executing Goose CLI commands.

    This agent handles initialization and command execution through the Goose CLI,
    managing subprocess execution and output handling.
    """

    async def execute_command(
        self,
        command: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,  # noqa: ARG002
        session_id: str | None = None,
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        base_command: str = f'goose run -n "{session_id}" -i "{command}"'
        return await self._execute_goose_command(base_command, working_dir, session_id)

    async def execute_prompt(
        self,
        prompt: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,  # noqa: ARG002
        session_id: str | None = None,
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        # lets clean up the prompt, it might be multiple lines and we want a single line
        prompt = "".join(prompt.splitlines())

        base_command: str = f'goose run -n "{session_id}" -t "{prompt}"'
        return await self._execute_goose_command(base_command, working_dir, session_id)

    async def _execute_goose_command(
        self,
        base_command: str,
        working_dir: str | None = None,
        session_id: str | None = None,
    ) -> CommandResult:
        formatted_command = base_command
        if session_id:
            formatted_command = f"{formatted_command}"

        logger.debug(f"Executing command (cwd: {working_dir}): {formatted_command}")

        status, result = await CommandUtils.run_command_async(  # noqa: S604
            command=formatted_command,
            working_dir=working_dir,
            shell=True,
        )

        # Goose will output this specific error string as its final message,
        # but there may be a few extra characters after it depending on settings.
        error_string: str = "Please retry if you think this is a transient or recoverable error."
        if error_string in result[-(len(error_string) + 20) :]:
            status = False

        logger.debug(f"Goose command result: {result}")
        return CommandResult(status=status, result=result)

    async def get_log_files(self, working_dir: str | None = None, session_id: str | None = None) -> None:
        # goose session export --name my-session --output session.md
        await CommandUtils.run_command_async(
            f'goose session export --name "{session_id}" --output session.md',
            working_dir,
        )

    async def stream_output(
        self,
        prompt: str | None = None,
        command_path: str | None = None,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        **kwargs,  # noqa: ANN003, ARG002
    ) -> CommandResult:
        """Stream live output from an ongoing Goose agent execution.

        Goose CLI does not currently support streaming output, so this method
        falls back to execute_prompt with the full result returned at once.

        Args:
            prompt: The prompt to send to Goose (if applicable).
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

        # Goose doesn't support streaming, so we execute the prompt normally
        return await self.execute_prompt(actual_prompt, working_dir, mcp_tools, session_id)

    async def cleanup(self, session_id: str | None = None) -> None:
        if not session_id:
            return
        try:
            # Delete the goose session so it's not unintentionally reused on task retries
            await CommandUtils.run_command_async(f'goose session remove -i "{session_id}"')
        except Exception as e:  # noqa: BLE001
            logger.warning(f'Error removing Goose session "{session_id}": {e}', exc_info=e)
