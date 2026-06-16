from abc import ABC, abstractmethod
from dataclasses import dataclass

from awa.client.models.agent_modes.agent_configuration import McpTool


@dataclass
class CommandResult:
    """Result of an agent command execution.

    Attributes:
        success: Whether the command executed successfully
        result: The output message or error message from the command

    """

    status: bool
    result: str
    session_id: str | None = None
    content: str | None = None


class AgentModeBase(ABC):
    def get_init_file_name(self) -> str:
        return ""

    def get_init_command(self) -> str:
        return ""

    def get_result_file_name(self) -> str:
        return "agent_result.txt"

    def get_mcp_file_name(self) -> str:
        return ""

    def supports_mcp(self) -> bool:
        return False

    async def configure_mcp(
        self,
        working_dir: str,
        mcp_json: str,
        mcp_allowed_tools: list[McpTool] | None = None,
    ) -> list[str] | None:
        """Configure MCP by saving the JSON file. Tool discovery is handled separately."""
        raise NotImplementedError

    async def initialize(
        self,
        command: str,
        working_dir: str | None = None,
        session_id: str | None = None,
    ) -> CommandResult:
        raise NotImplementedError

    @abstractmethod
    async def execute_command(
        self,
        command: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
    ) -> CommandResult:
        raise NotImplementedError

    @abstractmethod
    async def execute_prompt(
        self,
        prompt: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
    ) -> CommandResult:
        raise NotImplementedError

    # pylint: disable=unused-argument
    @abstractmethod
    async def get_log_files(
        self,
        working_dir: str | None = None,
        session_id: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def stream_output(
        self,
        prompt: str | None = None,
        command_path: str | None = None,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        **kwargs,  # noqa: ANN003
    ) -> CommandResult:
        """Stream live output from an ongoing agent execution.

        This method provides real-time access to the agent's output stream
        for monitoring progress during long-running operations.

        Args:
            prompt: The prompt to send to the agent (if applicable).
            command_path: Path to the command or script to execute (if applicable).
            working_dir: The working directory for agent execution.
            mcp_tools: List of allowed MCP tools for the agent.
            session_id: Unique identifier for the agent session to stream from.
            **kwargs: Additional agent-specific parameters.

        Returns:
            CommandResult: Contains streaming output and session status.

        Raises:
            NotImplementedError: If streaming is not supported by the agent mode.

        """
        raise NotImplementedError()

    # pylint: disable=unused-argument
    @abstractmethod
    async def cleanup(self, session_id: str | None = None) -> None:
        pass
