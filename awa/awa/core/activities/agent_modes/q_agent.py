import re
import shlex

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.command_utils import CommandUtils
from awa.sdk.models.agent_modes.agent_configuration import McpTool
from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase, CommandResult

logger = get_logger(LoggerComponent.ACTIVITY)


class QAgent(AgentModeBase):
    """AWS Q agent implementation for executing Q CLI commands."""

    def get_init_file_name(self) -> str | None:
        """Return the filename expected for Q agent initialization."""
        return None

    def get_init_command(self) -> str | None:
        """Return the command string used to initialize the Q agent."""
        return None

    def get_result_file_name(self) -> str:
        """Return the filename where the Q agent's execution result is stored."""
        return "q_result.json"

    def supports_mcp(self) -> bool:
        """Indicate whether the agent supports Meta Command Prompt (MCP)."""
        return False

    def get_mcp_file_name(self) -> str | None:
        """Return the filename used for the Meta Command Prompt (MCP) file."""
        return None

    async def initialize(
        self,
        command: str,  # noqa: ARG002
        working_dir: str | None = None,  # noqa: ARG002
        session_id: str | None = None,  # noqa: ARG002
    ) -> CommandResult:
        """Initialize the Q agent. This is a no-op for Q."""
        return CommandResult(status=True, result="Q agent does not require initialization.")

    async def execute_command(
        self,
        command: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,  # noqa: ARG002
    ) -> CommandResult:
        prompt = f"Read the content from this file {command} and execute"
        return await self.execute_prompt(prompt, working_dir, mcp_tools)

    async def execute_prompt(
        self,
        prompt: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,  # noqa: ARG002
        session_id: str | None = None,  # noqa: ARG002
    ) -> CommandResult:
        command_list: list[str] = [
            "q",
            "chat",
            "--no-interactive",
            "--trust-all-tools",
            prompt,
        ]

        command_str = " ".join(shlex.quote(s) for s in command_list)

        status, result = await CommandUtils.run_command_async(command_str, working_dir, shell=False)
        return self._process_q_output(status, result)

    async def configure_mcp(
        self,
        working_dir: str,  # noqa: ARG002
        mcp_json: str,  # noqa: ARG002
        mcp_allowed_tools: list[McpTool] | None = None,  # noqa: ARG002
    ) -> list[str] | None:
        """MCP is not supported for Q agent."""
        return None

    def _process_q_output(self, status: bool, result: str) -> CommandResult:
        logger.debug(f"Raw output from Q agent: {result}")

        # The output from `q chat` can contain a footer with a logo and tips.
        # We try to heuristically remove it. The logo starts with braille characters.
        content = result
        braille_logo_start = "⢠⣶⣶⣦"
        if braille_logo_start in content:
            content = content.split(braille_logo_start)[0]

        # A more comprehensive regex to remove various ANSI escape codes
        # This includes colors, cursor movement, and other control sequences.
        ansi_escape = re.compile(
            r"""
            \x1b  # ESC
            (?:   # Non-capturing group
                \[    # Control Sequence Introducer (CSI)
                [0-?]*  # Parameters for the sequence
                [ -/]*     # Intermediate bytes
                [@-~]      # Final byte
            |   # OR
                \].*?\x07  # Operating System Command (OSC)
            |   # OR
                \(.       # Designate character set
            )
        """,
            re.VERBOSE,
        )
        content = ansi_escape.sub("", content).strip()

        # Remove the leading "> " if it exists.
        content = content.removeprefix("> ")

        return CommandResult(status=status, result=result, content=content)

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
        """Stream live output from an ongoing Q agent execution.

        Q CLI does not currently support streaming output, so this method
        falls back to execute_prompt with the full result returned at once.

        Args:
            prompt: The prompt to send to Q (if applicable).
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

        # Q doesn't support streaming, so we execute the prompt normally
        return await self.execute_prompt(actual_prompt, working_dir, mcp_tools, session_id)

    async def cleanup(self, session_id: str | None = None) -> None:
        pass
