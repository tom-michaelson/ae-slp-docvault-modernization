"""Unit tests for the agent activity."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from awa.core.activities.agent import (
    _cleanup,
    _configure_mcp,
    _initialize,
    _initialize_and_run,
    _initialize_and_run_streaming,
    _run_command,
    execute_agent_activity,
    execute_agent_activity_streaming,
)
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration, McpServer, McpTool
from awa.sdk.models.agent_modes.agent_mode_base import CommandResult
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum


@pytest.fixture
def mock_agent_mode() -> MagicMock:
    """Fixture for a mocked AgentModeBase."""
    mock = MagicMock()

    # Synchronous methods (should return values directly)
    mock.get_init_file_name.return_value = "init.file"
    mock.get_init_command.return_value = "init command"
    mock.supports_mcp.return_value = True
    mock.get_result_file_name.return_value = "result.txt"
    mock.get_mcp_file_name.return_value = "mcp.json"

    # Asynchronous methods (should be AsyncMock)
    mock.configure_mcp = AsyncMock(return_value=["mcp_tool"])
    mock.initialize = AsyncMock(return_value=CommandResult(status=True, result="initialized"))
    mock.execute_command = AsyncMock(return_value=CommandResult(status=True, result="command executed"))
    mock.execute_prompt = AsyncMock(return_value=CommandResult(status=True, result="prompt executed"))
    mock.stream_output = AsyncMock(return_value=CommandResult(status=True, result="streamed output"))
    mock.get_log_files = AsyncMock(return_value=None)
    mock.cleanup = AsyncMock(return_value=None)

    return mock


@pytest.fixture
def agent_config() -> AgentConfiguration:
    """Fixture for a basic AgentConfiguration."""
    return AgentConfiguration(
        provider=AgentProviderEnum.CLAUDE,
        mode=AgentModeEnum.ACT,
        working_directory="/fake/dir",
        prompt="do something",
    )


# Tests for execute_agent_activity


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent")
@patch("awa.core.activities.agent._initialize_and_run")
@patch("awa.core.activities.agent._cleanup")
@patch("awa.core.activities.agent.uuid.uuid4")
async def test_execute_agent_success(
    mock_uuid: MagicMock,
    mock_cleanup: AsyncMock,
    mock_init_run: AsyncMock,
    mock_create_agent: MagicMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test the successful execution path of the agent activity."""
    mock_create_agent.return_value = mock_agent_mode
    mock_init_run.return_value = "Test output"
    mock_uuid.return_value = "fake-uuid"
    config = AgentConfiguration(provider=AgentProviderEnum.CLAUDE, mode=AgentModeEnum.ACT)

    result = await execute_agent_activity(config)

    assert result.status == "completed"
    assert result.output == "Test output"
    mock_cleanup.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent")
@patch("awa.core.activities.agent._initialize_and_run")
@patch("awa.core.activities.agent._cleanup")
@patch("awa.core.activities.agent.uuid.uuid4")
async def test_execute_agent_with_no_output_content(
    mock_uuid: MagicMock,
    mock_cleanup: AsyncMock,
    mock_init_run: AsyncMock,
    mock_create_agent: MagicMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that 'No output content' is returned when output_content is None."""
    mock_create_agent.return_value = mock_agent_mode
    mock_init_run.return_value = None
    mock_uuid.return_value = "fake-uuid"
    config = AgentConfiguration(provider=AgentProviderEnum.CLAUDE, mode=AgentModeEnum.ACT)

    result = await execute_agent_activity(config)

    assert result.status == "completed"
    assert result.output == "No output content"
    mock_cleanup.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent", side_effect=ValueError("Invalid provider"))
async def test_execute_agent_creation_fails(mock_create_agent: MagicMock) -> None:  # noqa: ARG001
    """Test that agent execution fails if agent creation fails."""
    config = AgentConfiguration(provider="invalid", mode=AgentModeEnum.ACT)
    result = await execute_agent_activity(config)
    assert result.status == "failed"
    assert "Invalid provider" in result.reason
    assert "Invalid provider" in (result.exception or "")


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent")
@patch("awa.core.activities.agent._initialize_and_run", side_effect=ValueError("Init failed"))
@patch("awa.core.activities.agent._cleanup")
async def test_execute_agent_init_run_fails(
    mock_cleanup: AsyncMock,
    mock_init_run: AsyncMock,  # noqa: ARG001
    mock_create_agent: MagicMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that agent execution fails if initialization or run fails."""
    mock_create_agent.return_value = mock_agent_mode
    config = AgentConfiguration(provider=AgentProviderEnum.CLAUDE, mode=AgentModeEnum.ACT)

    result = await execute_agent_activity(config)

    assert result.status == "failed"
    assert "Init failed" in result.reason
    mock_cleanup.assert_called_once()


# Tests for execute_agent_activity_streaming


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent")
@patch("awa.core.activities.agent._initialize_and_run_streaming")
@patch("awa.core.activities.agent._cleanup")
@patch("awa.core.activities.agent.uuid.uuid4")
async def test_execute_agent_streaming_success(
    mock_uuid: MagicMock,
    mock_cleanup: AsyncMock,
    mock_init_run_streaming: AsyncMock,
    mock_create_agent: MagicMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test the successful execution path of the streaming agent activity."""
    mock_create_agent.return_value = mock_agent_mode
    mock_init_run_streaming.return_value = "Streaming output"
    mock_uuid.return_value = "fake-uuid"
    config = AgentConfiguration(provider=AgentProviderEnum.CLAUDE, mode=AgentModeEnum.ACT)

    result = await execute_agent_activity_streaming(config)

    assert result.status == "completed"
    assert result.output == "Streaming output"
    assert result.session_id is not None
    mock_cleanup.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent")
@patch("awa.core.activities.agent._initialize_and_run_streaming")
@patch("awa.core.activities.agent._cleanup")
@patch("awa.core.activities.agent.uuid.uuid4")
async def test_execute_agent_streaming_with_no_output_content(
    mock_uuid: MagicMock,
    mock_cleanup: AsyncMock,
    mock_init_run_streaming: AsyncMock,
    mock_create_agent: MagicMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that 'No output content' is returned when output_content is None in streaming."""
    mock_create_agent.return_value = mock_agent_mode
    mock_init_run_streaming.return_value = None
    mock_uuid.return_value = "fake-uuid"
    config = AgentConfiguration(provider=AgentProviderEnum.CLAUDE, mode=AgentModeEnum.ACT)

    result = await execute_agent_activity_streaming(config)

    assert result.status == "completed"
    assert result.output == "No output content"
    assert result.session_id is not None
    mock_cleanup.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent")
@patch("awa.core.activities.agent._initialize_and_run_streaming")
@patch("awa.core.activities.agent._cleanup")
async def test_execute_agent_streaming_with_custom_session_id(
    mock_cleanup: AsyncMock,
    mock_init_run_streaming: AsyncMock,
    mock_create_agent: MagicMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that custom stream_session_id is used in streaming when provided."""
    mock_create_agent.return_value = mock_agent_mode
    mock_init_run_streaming.return_value = "Streaming output"
    config = AgentConfiguration(
        provider=AgentProviderEnum.CLAUDE,
        mode=AgentModeEnum.ACT,
        stream_session_id="custom-streaming-session",
    )

    result = await execute_agent_activity_streaming(config)

    assert result.status == "completed"
    assert result.session_id == "custom-streaming-session"
    mock_cleanup.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent", side_effect=RuntimeError("Streaming error"))
async def test_execute_agent_streaming_creation_fails(mock_create_agent: MagicMock) -> None:  # noqa: ARG001
    """Test that streaming agent execution fails if agent creation fails."""
    config = AgentConfiguration(provider=AgentProviderEnum.CLAUDE, mode=AgentModeEnum.ACT)
    result = await execute_agent_activity_streaming(config)
    assert result.status == "failed"
    assert "Streaming error" in result.reason
    assert "Streaming error" in (result.exception or "")
    assert result.session_id == ""


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent")
@patch("awa.core.activities.agent._initialize_and_run_streaming", side_effect=ValueError("Streaming failed"))
@patch("awa.core.activities.agent._cleanup")
async def test_execute_agent_streaming_init_run_fails(
    mock_cleanup: AsyncMock,
    mock_init_run_streaming: AsyncMock,  # noqa: ARG001
    mock_create_agent: MagicMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that streaming agent execution fails if initialization or streaming fails."""
    mock_create_agent.return_value = mock_agent_mode
    config = AgentConfiguration(provider=AgentProviderEnum.CLAUDE, mode=AgentModeEnum.ACT)

    result = await execute_agent_activity_streaming(config)

    assert result.status == "failed"
    assert "Streaming failed" in result.reason
    assert result.session_id is not None
    mock_cleanup.assert_called_once()


# Tests for _initialize_and_run


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize", return_value=CommandResult(status=True, result=""))
@patch("awa.core.activities.agent._configure_mcp", return_value=["mcp_tool"])
@patch(
    "awa.core.activities.agent._run_command",
    return_value=CommandResult(status=True, result="", content="final output"),
)
async def test_initialize_and_run_success(
    mock_run: AsyncMock,
    mock_mcp: AsyncMock,
    mock_init: AsyncMock,
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test successful path for _initialize_and_run."""
    agent_config.mcp = McpServer(mcp_json="{}")
    output = await _initialize_and_run(agent_config, mock_agent_mode, "sid")

    assert output == "final output"
    mock_init.assert_called_once()
    mock_mcp.assert_called_once()
    mock_run.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize", return_value=CommandResult(status=False, result="Init failed"))
async def test_initialize_and_run_init_fails(
    mock_init: AsyncMock,
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that _initialize_and_run raises ValueError when initialization fails."""
    with pytest.raises(ValueError, match="Agent initialization failed: Init failed"):
        await _initialize_and_run(agent_config, mock_agent_mode, "sid")
    mock_init.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize", return_value=CommandResult(status=True, result=""))
@patch("awa.core.activities.agent._run_command", return_value=CommandResult(status=False, result="Command failed"))
async def test_initialize_and_run_command_fails(
    mock_run: AsyncMock,
    mock_init: AsyncMock,
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that _initialize_and_run raises ValueError when command execution fails."""
    with pytest.raises(ValueError, match="Agent command failed: Command failed"):
        await _initialize_and_run(agent_config, mock_agent_mode, "sid")
    mock_init.assert_called_once()
    mock_run.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize", return_value=CommandResult(status=True, result="initialized"))
@patch(
    "awa.core.activities.agent._run_command",
    return_value=CommandResult(status=True, result="fallback result", content=None),
)
async def test_initialize_and_run_uses_result_when_no_content(
    mock_run: AsyncMock,  # noqa: ARG001
    mock_init: AsyncMock,  # noqa: ARG001
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that _initialize_and_run uses result when content is None."""
    output = await _initialize_and_run(agent_config, mock_agent_mode, "sid")
    assert output == "fallback result"


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize", return_value=CommandResult(status=True, result="initialized"))
@patch(
    "awa.core.activities.agent._run_command",
    return_value=CommandResult(status=True, result="result", content="content"),
)
async def test_initialize_and_run_prefers_content_over_result(
    mock_run: AsyncMock,  # noqa: ARG001
    mock_init: AsyncMock,  # noqa: ARG001
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that _initialize_and_run prefers content over result when both exist."""
    output = await _initialize_and_run(agent_config, mock_agent_mode, "sid")
    assert output == "content"


@pytest.mark.asyncio
async def test_initialize_and_run_skips_mcp_when_not_configured(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that MCP configuration is skipped when not configured."""
    agent_config.mcp = None
    await _initialize_and_run(agent_config, mock_agent_mode, "sid")
    mock_agent_mode.configure_mcp.assert_not_called()


@pytest.mark.asyncio
async def test_initialize_and_run_skips_mcp_when_not_supported(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that MCP configuration is skipped when agent doesn't support it."""
    agent_config.mcp = McpServer(mcp_json="{}")
    mock_agent_mode.supports_mcp.return_value = False
    await _initialize_and_run(agent_config, mock_agent_mode, "sid")
    mock_agent_mode.configure_mcp.assert_not_called()


# Tests for _initialize_and_run_streaming


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize", return_value=CommandResult(status=True, result=""))
@patch("awa.core.activities.agent._configure_mcp", return_value=["mcp_tool"])
async def test_initialize_and_run_streaming_success(
    mock_mcp: AsyncMock,
    mock_init: AsyncMock,
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test successful path for _initialize_and_run_streaming."""
    agent_config.mcp = McpServer(mcp_json="{}")
    mock_agent_mode.stream_output = AsyncMock(
        return_value=CommandResult(status=True, result="", content="streamed data"),
    )

    output = await _initialize_and_run_streaming(agent_config, mock_agent_mode, "sid")

    assert output == "streamed data"
    mock_init.assert_called_once()
    mock_mcp.assert_called_once()
    mock_agent_mode.stream_output.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize", return_value=CommandResult(status=False, result="Init failed"))
async def test_initialize_and_run_streaming_init_fails(
    mock_init: AsyncMock,
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that _initialize_and_run_streaming raises ValueError when initialization fails."""
    with pytest.raises(ValueError, match="Agent initialization failed: Init failed"):
        await _initialize_and_run_streaming(agent_config, mock_agent_mode, "sid")
    mock_init.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize", return_value=CommandResult(status=True, result=""))
async def test_initialize_and_run_streaming_streaming_fails(
    mock_init: AsyncMock,
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that _initialize_and_run_streaming raises ValueError when streaming fails."""
    mock_agent_mode.stream_output = AsyncMock(return_value=CommandResult(status=False, result="Streaming failed"))

    with pytest.raises(ValueError, match="Agent streaming failed: Streaming failed"):
        await _initialize_and_run_streaming(agent_config, mock_agent_mode, "sid")

    mock_init.assert_called_once()
    mock_agent_mode.stream_output.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize", return_value=CommandResult(status=True, result=""))
async def test_initialize_and_run_streaming_uses_result_when_no_content(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that _initialize_and_run_streaming uses result when content is None."""
    mock_agent_mode.stream_output = AsyncMock(return_value=CommandResult(status=True, result="fallback result"))

    output = await _initialize_and_run_streaming(agent_config, mock_agent_mode, "sid")
    assert output == "fallback result"


@pytest.mark.asyncio
async def test_initialize_and_run_streaming_passes_correct_params(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that _initialize_and_run_streaming passes correct parameters to stream_output."""
    agent_config.prompt = "test prompt"
    agent_config.command_file_path = "/path/to/command"
    agent_config.working_directory = "/working/dir"
    mock_agent_mode.stream_output = AsyncMock(return_value=CommandResult(status=True, result="success"))

    await _initialize_and_run_streaming(agent_config, mock_agent_mode, "test-sid")

    # Check that the main parameters are passed correctly
    # parent_session_id may be passed as a kwarg for agents that support it
    call_kwargs = mock_agent_mode.stream_output.call_args.kwargs
    assert call_kwargs["prompt"] == "test prompt"
    assert call_kwargs["command_path"] == "/path/to/command"
    assert call_kwargs["working_dir"] == "/working/dir"
    assert call_kwargs["mcp_tools"] is None
    assert call_kwargs["session_id"] == "test-sid"


# Tests for _initialize


@pytest.mark.asyncio
@patch("awa.core.activities.agent.Path")
async def test_initialize_skip_if_file_exists(
    mock_path: MagicMock,
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that initialization is skipped if the init file already exists."""
    mock_path.return_value.__truediv__.return_value.exists.return_value = True
    result = await _initialize(agent_config, mock_agent_mode, "sid")
    assert result.status
    assert "Skipping agent initialization" in result.result
    mock_agent_mode.initialize.assert_not_called()


@pytest.mark.asyncio
async def test_initialize_skip_when_initialize_false(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that initialization is skipped when initialize is False."""
    agent_config.initialize = False
    result = await _initialize(agent_config, mock_agent_mode, "sid")
    assert result.status
    assert "Skipping agent initialization" in result.result
    mock_agent_mode.initialize.assert_not_called()


@pytest.mark.asyncio
async def test_initialize_skip_when_no_init_file_or_command(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that initialization is skipped when no init file or command exists."""
    mock_agent_mode.get_init_file_name.return_value = None
    mock_agent_mode.get_init_command.return_value = None
    result = await _initialize(agent_config, mock_agent_mode, "sid")
    assert result.status
    assert "No initialization file found" in result.result
    mock_agent_mode.initialize.assert_not_called()


@pytest.mark.asyncio
@patch("awa.core.activities.agent.Path")
async def test_initialize_calls_initialize_when_file_does_not_exist(
    mock_path: MagicMock,
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that initialization is called when file does not exist."""
    mock_path.return_value.__truediv__.return_value.exists.return_value = False
    result = await _initialize(agent_config, mock_agent_mode, "sid")
    assert result.status
    mock_agent_mode.initialize.assert_called_once_with(
        command="init command",
        working_dir=agent_config.working_directory,
        session_id="sid",
    )


@pytest.mark.asyncio
async def test_initialize_when_no_working_directory(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test initialization when working_directory is None."""
    agent_config.working_directory = None
    await _initialize(agent_config, mock_agent_mode, "sid")
    # Should still call initialize without checking file existence
    mock_agent_mode.initialize.assert_called_once_with(
        command="init command",
        working_dir=None,
        session_id="sid",
    )


# Tests for _run_command


@pytest.mark.asyncio
async def test_run_command_with_prompt(agent_config: AgentConfiguration, mock_agent_mode: MagicMock) -> None:
    """Test that execute_prompt is called when a prompt is provided."""
    agent_config.command_file_path = None
    agent_config.prompt = "a new prompt"
    await _run_command(agent_config, mock_agent_mode, "sid")
    mock_agent_mode.execute_prompt.assert_called_once_with(
        prompt="a new prompt",
        session_id="sid",
        working_dir=agent_config.working_directory,
        mcp_tools=None,
        stream_enabled=False,
    )


@pytest.mark.asyncio
async def test_run_command_with_file(agent_config: AgentConfiguration, mock_agent_mode: MagicMock) -> None:
    """Test that execute_command is called when a command file is provided."""
    agent_config.command_file_path = "/fake/file.txt"
    agent_config.prompt = None
    await _run_command(agent_config, mock_agent_mode, "sid")
    mock_agent_mode.execute_command.assert_called_once_with(
        command="/fake/file.txt",
        session_id="sid",
        working_dir=agent_config.working_directory,
        mcp_tools=None,
        stream_enabled=False,
    )


@pytest.mark.asyncio
async def test_run_command_with_mcp_tools(agent_config: AgentConfiguration, mock_agent_mode: MagicMock) -> None:
    """Test that mcp_tools are passed when provided."""
    agent_config.command_file_path = None
    agent_config.prompt = "test prompt"
    mcp_tools = ["tool1", "tool2"]
    await _run_command(agent_config, mock_agent_mode, "sid", mcp_tools=mcp_tools)
    mock_agent_mode.execute_prompt.assert_called_once_with(
        prompt="test prompt",
        session_id="sid",
        working_dir=agent_config.working_directory,
        mcp_tools=mcp_tools,
        stream_enabled=False,
    )


@pytest.mark.asyncio
async def test_run_command_prefers_command_file_over_prompt(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that command file takes precedence over prompt when both are provided."""
    agent_config.command_file_path = "/fake/file.txt"
    agent_config.prompt = "this should be ignored"
    await _run_command(agent_config, mock_agent_mode, "sid")
    mock_agent_mode.execute_command.assert_called_once()
    mock_agent_mode.execute_prompt.assert_not_called()


@pytest.mark.asyncio
async def test_run_command_with_neither_file_nor_prompt(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that proper result is returned when neither command file nor prompt is provided."""
    agent_config.command_file_path = None
    agent_config.prompt = None
    result = await _run_command(agent_config, mock_agent_mode, "sid")
    assert not result.status
    assert result.result == "No command file path or prompt provided"
    mock_agent_mode.execute_command.assert_not_called()
    mock_agent_mode.execute_prompt.assert_not_called()


# Tests for _configure_mcp


@pytest.mark.asyncio
async def test_configure_mcp_success(agent_config: AgentConfiguration, mock_agent_mode: MagicMock) -> None:
    """Test successful MCP configuration."""
    agent_config.mcp = McpServer(mcp_json='{"key": "value"}', allowed=[McpTool(server="s", tools=["t"])])
    await _configure_mcp(agent_config, mock_agent_mode)
    mock_agent_mode.configure_mcp.assert_called_once_with(
        working_dir=agent_config.working_directory,
        mcp_json=agent_config.mcp.mcp_json,
        mcp_allowed_tools=agent_config.mcp.allowed,
    )


@pytest.mark.asyncio
async def test_configure_mcp_when_mcp_is_none(agent_config: AgentConfiguration, mock_agent_mode: MagicMock) -> None:
    """Test that None is returned when mcp is not configured."""
    agent_config.mcp = None
    result = await _configure_mcp(agent_config, mock_agent_mode)
    assert result is None
    mock_agent_mode.configure_mcp.assert_not_called()


@pytest.mark.asyncio
async def test_configure_mcp_when_working_directory_is_none(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that None is returned when working_directory is None."""
    agent_config.working_directory = None
    agent_config.mcp = McpServer(mcp_json='{"key": "value"}')
    result = await _configure_mcp(agent_config, mock_agent_mode)
    assert result is None
    mock_agent_mode.configure_mcp.assert_not_called()


@pytest.mark.asyncio
async def test_configure_mcp_when_mcp_json_is_none(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that None is returned when mcp_json is None."""
    agent_config.mcp = McpServer(mcp_json=None)
    result = await _configure_mcp(agent_config, mock_agent_mode)
    assert result is None
    mock_agent_mode.configure_mcp.assert_not_called()


# Tests for _cleanup


@pytest.mark.asyncio
async def test_cleanup(agent_config: AgentConfiguration, mock_agent_mode: MagicMock) -> None:
    """Test that cleanup and get_log_files are called."""
    await _cleanup(agent_config, mock_agent_mode, "sid")
    mock_agent_mode.get_log_files.assert_called_once_with(
        working_dir=agent_config.working_directory,
        session_id="sid",
    )
    mock_agent_mode.cleanup.assert_called_once_with("sid")


@pytest.mark.asyncio
async def test_cleanup_with_none_working_directory(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test cleanup when working_directory is None."""
    agent_config.working_directory = None
    await _cleanup(agent_config, mock_agent_mode, "sid")
    mock_agent_mode.get_log_files.assert_called_once_with(
        working_dir=None,
        session_id="sid",
    )
    mock_agent_mode.cleanup.assert_called_once_with("sid")


# Tests for execute_agent_activity_streaming


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent")
@patch("awa.core.activities.agent._initialize_and_run_streaming")
@patch("awa.core.activities.agent.uuid.uuid4")
async def test_execute_agent_streaming_generates_session_id(
    mock_uuid: MagicMock,
    mock_init_run_streaming: AsyncMock,
    mock_create_agent: MagicMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that session ID is generated when not provided."""
    mock_create_agent.return_value = mock_agent_mode
    mock_init_run_streaming.return_value = "Output"
    mock_uuid.return_value = "generated-uuid"

    config = AgentConfiguration(
        provider=AgentProviderEnum.CLAUDE,
        mode=AgentModeEnum.ACT,
        # No stream_session_id provided
    )

    result = await execute_agent_activity_streaming(config)

    assert result.status == "completed"
    # Session ID should be in format: YYYYMMDDHHMMSS-uuid
    assert "-generated-uuid" in result.session_id
    mock_uuid.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent")
@patch("awa.core.activities.agent._initialize_and_run_streaming")
async def test_execute_agent_streaming_with_no_output(
    mock_init_run_streaming: AsyncMock,
    mock_create_agent: MagicMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test streaming activity with no output content."""
    mock_create_agent.return_value = mock_agent_mode
    mock_init_run_streaming.return_value = None

    config = AgentConfiguration(
        provider=AgentProviderEnum.CLAUDE,
        mode=AgentModeEnum.ACT,
        stream_session_id="test-session",
    )

    result = await execute_agent_activity_streaming(config)

    assert result.status == "completed"
    assert result.output == "No output content"


@pytest.mark.asyncio
@patch("awa.core.activities.agent.create_agent", side_effect=Exception("Streaming failed"))
async def test_execute_agent_streaming_handles_error(
    mock_create_agent: MagicMock,  # noqa: ARG001
) -> None:
    """Test that streaming activity handles errors gracefully."""
    config = AgentConfiguration(
        provider=AgentProviderEnum.CLAUDE,
        mode=AgentModeEnum.ACT,
        stream_session_id="test-session",
    )

    result = await execute_agent_activity_streaming(config)

    assert result.status == "failed"
    assert result.exception is not None
    assert "Streaming failed" in result.exception
    # Session ID should be empty string when error occurs before session is created
    assert result.session_id == ""


# Tests for _initialize_and_run_streaming


@pytest.mark.asyncio
@patch("awa.core.activities.agent._initialize")
async def test_initialize_and_run_streaming_with_prompt(
    mock_init: AsyncMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test streaming initialization with prompt."""
    mock_init.return_value = CommandResult(status=True, result="")

    config = AgentConfiguration(
        provider=AgentProviderEnum.CLAUDE,
        mode=AgentModeEnum.ACT,
        prompt="Test streaming prompt",
        working_directory="/test/dir",
    )

    mock_agent_mode.stream_output = AsyncMock(
        return_value=CommandResult(status=True, result="Streamed result", content="Content"),
    )

    result = await _initialize_and_run_streaming(
        agent_config=config,
        agent_mode=mock_agent_mode,
        session_id="session-123",
    )

    assert result == "Content"
    # Check that the main parameters are passed correctly
    call_kwargs = mock_agent_mode.stream_output.call_args.kwargs
    assert call_kwargs["prompt"] == "Test streaming prompt"
    assert call_kwargs["command_path"] is None
    assert call_kwargs["working_dir"] == "/test/dir"
    assert call_kwargs["mcp_tools"] is None
    assert call_kwargs["session_id"] == "session-123"


@pytest.mark.asyncio
@patch("awa.core.activities.agent._configure_mcp")
async def test_initialize_and_run_streaming_with_command_file(
    mock_configure_mcp: AsyncMock,
    mock_agent_mode: MagicMock,
) -> None:
    """Test streaming initialization with command file."""
    mock_configure_mcp.return_value = None

    config = AgentConfiguration(
        provider=AgentProviderEnum.CLAUDE,
        mode=AgentModeEnum.ACT,
        command_file_path="/path/to/command.txt",
        working_directory="/test/dir",
    )

    mock_agent_mode.stream_output = AsyncMock(
        return_value=CommandResult(status=True, result="Result", content="File content"),
    )

    result = await _initialize_and_run_streaming(
        agent_config=config,
        agent_mode=mock_agent_mode,
        session_id="session-456",
    )

    assert result == "File content"
    # Prompt comes from build_prompt_params fallback logic
    call_kwargs = mock_agent_mode.stream_output.call_args.kwargs
    assert call_kwargs["command_path"] == "/path/to/command.txt"
    assert call_kwargs["working_dir"] == "/test/dir"
    assert call_kwargs["mcp_tools"] is None
    assert call_kwargs["session_id"] == "session-456"


@pytest.mark.asyncio
@patch("awa.core.activities.agent._configure_mcp")
async def test_initialize_and_run_streaming_returns_result_on_no_content(
    mock_configure_mcp: AsyncMock,
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test that result is returned when content is None."""
    mock_configure_mcp.return_value = None
    agent_config.prompt = "Test"

    mock_agent_mode.stream_output = AsyncMock(
        return_value=CommandResult(status=True, result="Fallback result", content=None),
    )

    result = await _initialize_and_run_streaming(
        agent_config=agent_config,
        agent_mode=mock_agent_mode,
        session_id="session-789",
    )

    assert result == "Fallback result"


@pytest.mark.asyncio
async def test_initialize_and_run_streaming_with_mcp_tools(
    agent_config: AgentConfiguration,
    mock_agent_mode: MagicMock,
) -> None:
    """Test streaming with MCP tools configuration."""
    agent_config.prompt = "Use MCP tools"
    agent_config.working_directory = "/workspace"
    agent_config.mcp = McpServer(
        mcp_json='{"servers": {"test": {}}}',
        allowed_tools=[
            McpTool(server_name="test", tool_names=["tool1", "tool2"]),
        ],
    )

    mock_agent_mode.configure_mcp = AsyncMock(return_value=["mcp__test__tool1", "mcp__test__tool2"])
    mock_agent_mode.stream_output = AsyncMock(
        return_value=CommandResult(status=True, result="MCP result", content="MCP content"),
    )

    result = await _initialize_and_run_streaming(
        agent_config=agent_config,
        agent_mode=mock_agent_mode,
        session_id="mcp-session",
    )

    assert result == "MCP content"
    mock_agent_mode.configure_mcp.assert_called_once()
    # Verify stream_output was called with MCP tools
    call_kwargs = mock_agent_mode.stream_output.call_args.kwargs
    assert call_kwargs["mcp_tools"] == ["mcp__test__tool1", "mcp__test__tool2"]
    assert call_kwargs["session_id"] == "mcp-session"
