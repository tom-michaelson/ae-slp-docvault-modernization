"""Unit tests for AgentModeBase."""

import pytest

from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase, CommandResult


# Concrete implementation of the abstract base class for testing
class ConcreteAgentMode(AgentModeBase):
    """A concrete implementation of AgentModeBase for testing purposes."""

    async def execute_command(
        self,
        _command: str,
        _working_dir: str | None = None,
        _mcp_tools: list[str] | None = None,
        _session_id: str | None = None,
    ) -> CommandResult:
        """Mock implementation for abstract method."""
        return CommandResult(status=True, result="command executed")

    async def execute_prompt(
        self,
        _prompt: str,
        _working_dir: str | None = None,
        _mcp_tools: list[str] | None = None,
        _session_id: str | None = None,
    ) -> CommandResult:
        """Mock implementation for abstract method."""
        return CommandResult(status=True, result="prompt executed")

    async def get_log_files(
        self,
        _working_dir: str | None = None,
        _session_id: str | None = None,
    ) -> None:
        """Mock implementation for abstract method."""

    async def stream_output(
        self,
        _prompt: str | None = None,
        _command_path: str | None = None,
        _working_dir: str | None = None,
        _mcp_tools: list[str] | None = None,
        _session_id: str | None = None,
        **_kwargs,  # noqa: ANN003
    ) -> CommandResult:
        """Mock implementation for abstract method."""
        return CommandResult(status=True, result="streamed output")

    async def cleanup(self, _session_id: str | None = None) -> None:
        """Mock implementation for abstract method."""


@pytest.fixture
def agent_mode() -> ConcreteAgentMode:
    """Fixture to provide a ConcreteAgentMode instance."""
    return ConcreteAgentMode()


def test_get_init_file_name(agent_mode: AgentModeBase) -> None:
    """Test the default implementation of get_init_file_name."""
    assert agent_mode.get_init_file_name() == ""


def test_get_init_command(agent_mode: AgentModeBase) -> None:
    """Test the default implementation of get_init_command."""
    assert agent_mode.get_init_command() == ""


def test_get_result_file_name(agent_mode: AgentModeBase) -> None:
    """Test the default implementation of get_result_file_name."""
    assert agent_mode.get_result_file_name() == "agent_result.txt"


def test_get_mcp_file_name(agent_mode: AgentModeBase) -> None:
    """Test the default implementation of get_mcp_file_name."""
    assert agent_mode.get_mcp_file_name() == ""


def test_supports_mcp(agent_mode: AgentModeBase) -> None:
    """Test the default implementation of supports_mcp."""
    assert not agent_mode.supports_mcp()


@pytest.mark.asyncio
async def test_configure_mcp_raises_not_implemented(agent_mode: AgentModeBase) -> None:
    """Test that configure_mcp raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        await agent_mode.configure_mcp("some_dir", "some_json")


@pytest.mark.asyncio
async def test_initialize_raises_not_implemented(agent_mode: AgentModeBase) -> None:
    """Test that initialize raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        await agent_mode.initialize("some_command", "some_dir")


@pytest.mark.asyncio
async def test_get_log_files_does_nothing(agent_mode: AgentModeBase) -> None:
    """Test that get_log_files runs without error and returns None."""
    # This method is expected to do nothing and return None
    result = await agent_mode.get_log_files()
    assert result is None


@pytest.mark.asyncio
async def test_cleanup_does_nothing(agent_mode: AgentModeBase) -> None:
    """Test that cleanup runs without error and returns None."""
    # This method is expected to do nothing and return None
    result = await agent_mode.cleanup()
    assert result is None
