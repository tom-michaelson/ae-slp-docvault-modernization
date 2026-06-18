"""Unit tests for ClaudeAgent."""

import json
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.agent_modes.claude_agent import ClaudeAgent
from awa.sdk.models.agent_modes.agent_configuration import McpTool

# Constants
EXPECTED_SERVER_COUNT = 2
EXPECTED_JSON_OBJECTS = 2


@pytest.fixture
def claude_agent() -> ClaudeAgent:
    """Fixture to provide a ClaudeAgent instance."""
    return ClaudeAgent()


def test_get_init_file_name(claude_agent: ClaudeAgent) -> None:
    """Test get_init_file_name returns the correct constant."""
    assert claude_agent.get_init_file_name() == "CLAUDE.md"


def test_get_init_command(claude_agent: ClaudeAgent) -> None:
    """Test get_init_command returns the correct command string."""
    expected_command = (
        "claude -p /init --output-format stream-json --verbose "
        "--allowedTools Bash,Edit,MultiEdit,Write,Task,Agent,TodoRead,TodoWrite,"
        "Glob,Grep,Read,SlashCommand,WebFetch,WebSearch,Skills"
    )
    assert claude_agent.get_init_command() == expected_command


def test_get_result_file_name(claude_agent: ClaudeAgent) -> None:
    """Test get_result_file_name returns the correct filename."""
    assert claude_agent.get_result_file_name() == "claude_result.json"


def test_supports_mcp(claude_agent: ClaudeAgent) -> None:
    """Test supports_mcp returns True."""
    assert claude_agent.supports_mcp()


def test_get_mcp_file_name(claude_agent: ClaudeAgent) -> None:
    """Test get_mcp_file_name returns the correct constant."""
    assert claude_agent.get_mcp_file_name() == ".mcp.json"


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_initialize(mock_run_command: AsyncMock, claude_agent: ClaudeAgent) -> None:
    """Test initialize method calls run_command_async and processes output."""
    mock_run_command.return_value = (True, '{"result": "initialized"}')
    command = "claude init"
    result = await claude_agent.initialize(command, "/fake/dir")

    mock_run_command.assert_called_once_with(command, "/fake/dir", shell=False)
    assert result.status
    assert '"result": "initialized"' in result.result


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt(mock_run_command: AsyncMock, claude_agent: ClaudeAgent) -> None:
    """Test execute_prompt constructs command and calls run_command_async."""
    mock_run_command.return_value = (True, '{"result": "prompt executed"}')
    prompt = "do something"
    await claude_agent.execute_prompt(prompt, "/fake/dir")

    mock_run_command.assert_called_once()
    called_command = mock_run_command.call_args[0][0]
    assert prompt in called_command
    assert "claude" in called_command
    assert "stream-json" in called_command


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_command(mock_run_command: AsyncMock, claude_agent: ClaudeAgent) -> None:
    """Test execute_command calls execute_prompt with the correct prompt."""
    mock_run_command.return_value = (True, '{"result": "command executed"}')
    command_file = "my_command.txt"

    with patch.object(claude_agent, "execute_prompt", new_callable=AsyncMock) as mock_execute_prompt:
        await claude_agent.execute_command(command_file, "/fake/dir", ["tool1"])
        mock_execute_prompt.assert_called_once_with(
            f"Read the content from this file {command_file} and execute",
            "/fake/dir",
            ["tool1"],
            None,  # session_id
            False,  # stream_enabled
        )


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_configure_mcp(mock_run_command: AsyncMock, claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp parses JSON and registers servers."""
    mock_run_command.return_value = (True, '{"result": "server registered"}')
    mcp_json = json.dumps(
        {
            "mcpServers": {
                "server1": {"url": "http://localhost:8080"},
                "server2": {"url": "http://localhost:8081"},
            },
        },
    )
    mcp_tools = [McpTool(server="server1", tools=["toolA", "toolB"])]

    allowed_tools = await claude_agent.configure_mcp(
        "/fake/dir",
        mcp_json,
        mcp_tools,
    )

    assert mock_run_command.call_count == EXPECTED_SERVER_COUNT
    assert set(allowed_tools or []) == {"mcp__server1__toolA", "mcp__server1__toolB"}


@pytest.mark.asyncio
async def test_configure_mcp_invalid_json(claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp with invalid JSON."""
    with pytest.raises(ValueError, match="Failed to parse MCP JSON"):
        await claude_agent.configure_mcp("/fake/dir", "invalid json")


def test_process_claude_output_success(claude_agent: ClaudeAgent) -> None:
    """Test _process_claude_output with successful JSON output."""
    output = '{"event": "result", "result": "Success"}\n{"event": "final", "result": "Final message"}'
    result = claude_agent._process_claude_output(status=True, result=output)
    assert result.status
    assert result.content == "Final message"
    assert "Final message" in result.result


def test_process_claude_output_failure(claude_agent: ClaudeAgent) -> None:
    """Test _process_claude_output with an API error."""
    output = '{"event": "error", "result": "API Error: something went wrong"}'
    result = claude_agent._process_claude_output(status=True, result=output)
    assert not result.status
    assert "API Error" in result.result


def test_process_claude_output_invalid_json(claude_agent: ClaudeAgent) -> None:
    """Test _process_claude_output with invalid JSON."""
    output = "this is not json"
    result = claude_agent._process_claude_output(status=True, result=output)
    assert not result.status
    assert "Error parsing JSON" in result.result


def test_parse_newline_separated_json() -> None:
    """Test _parse_newline_separated_json with valid input."""
    json_string = '{"key1": "value1"}\n{"key2": "value2"}\n'
    result = ClaudeAgent._parse_newline_separated_json(json_string)
    assert len(result) == EXPECTED_JSON_OBJECTS
    assert result[0]["key1"] == "value1"
    assert result[1]["key2"] == "value2"


def test_parse_newline_separated_json_invalid_line() -> None:
    """Test _parse_newline_separated_json with an invalid JSON line."""
    json_string = '{"key1": "value1"}\nnot a json\n'
    with pytest.raises(ValueError, match="Could not decode JSON from Claude output"):
        ClaudeAgent._parse_newline_separated_json(json_string)


def test_parse_newline_separated_json_empty_string() -> None:
    """Test _parse_newline_separated_json with empty string."""
    result = ClaudeAgent._parse_newline_separated_json("")
    assert result == []


def test_parse_newline_separated_json_with_empty_lines() -> None:
    """Test _parse_newline_separated_json with empty lines between JSON objects."""
    json_string = '{"key1": "value1"}\n\n\n{"key2": "value2"}\n'
    result = ClaudeAgent._parse_newline_separated_json(json_string)
    assert len(result) == EXPECTED_JSON_OBJECTS
    assert result[0]["key1"] == "value1"
    assert result[1]["key2"] == "value2"


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_execute_prompt_with_mcp_tools(mock_run_command: AsyncMock, claude_agent: ClaudeAgent) -> None:
    """Test execute_prompt with MCP tools configured."""
    mock_run_command.return_value = (True, '{"result": "executed with tools"}')
    prompt = "do something"
    mcp_tools = ["mcp__server1__tool1", "mcp__server2__tool2"]

    await claude_agent.execute_prompt(prompt, "/fake/dir", mcp_tools)

    mock_run_command.assert_called_once()
    called_command = mock_run_command.call_args[0][0]
    assert "mcp__server1__tool1" in called_command
    assert "mcp__server2__tool2" in called_command


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
@patch("awa.core.utils.streaming_http_client.emit_streaming_event_multi")
async def test_execute_prompt_with_session_id(
    mock_emit: AsyncMock,
    mock_run_command: AsyncMock,
    claude_agent: ClaudeAgent,
) -> None:
    """Test execute_prompt with session_id for HTTP streaming."""
    mock_emit.return_value = [True]  # Successful emission
    mock_run_command.return_value = (True, '{"result": "executed"}')
    prompt = "test streaming"
    session_id = "test-session-123"

    with patch.object(
        claude_agent,
        "stream_output",
        return_value=AsyncMock(status=True, result='{"result": "streamed execution"}'),
    ):
        result = await claude_agent.execute_prompt(prompt, "/fake/dir", session_id=session_id)

    assert result.status


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
@patch("awa.core.utils.streaming_http_client.emit_streaming_event_multi")
async def test_execute_prompt_stream_start_failure(
    mock_emit: AsyncMock,
    mock_run_command: AsyncMock,
    claude_agent: ClaudeAgent,
) -> None:
    """Test execute_prompt handles stream emission failure gracefully."""
    mock_emit.side_effect = Exception("HTTP connection failed")
    mock_run_command.return_value = (True, '{"result": "executed"}')

    with patch.object(claude_agent, "stream_output", return_value=AsyncMock(status=True, result='{"result": "ok"}')):
        result = await claude_agent.execute_prompt("test", "/fake/dir", session_id="test-session")
        # Should continue execution despite emission failure
        assert result.status


@pytest.mark.asyncio
async def test_execute_with_streaming_success() -> None:
    """Test stream_output successfully processes stream output via HTTP."""
    claude_agent = ClaudeAgent()

    async def mock_stream_generator() -> AsyncGenerator:
        # First yield the process
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = 0
        yield mock_process
        # Then yield output lines
        yield '{"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}}\n'
        yield '{"type": "assistant", "message": {"content": [{"type": "text", "text": "World"}]}}\n'

    with (
        patch("awa.core.activities.agent_modes.claude_agent.emit_streaming_event_multi", return_value=[True]),
        patch("awa.core.utils.command_utils.CommandUtils.stream_command_async", return_value=mock_stream_generator()),
    ):
        result = await claude_agent.stream_output(
            prompt="test",
            working_dir="/fake/dir",
            session_id="test-session",
        )

    assert result.status
    # Content is extracted to the content field in streaming mode
    # Only the last text message is stored in content
    assert result.content is not None
    assert "World" in result.content


def test_extract_stream_content_text_type(claude_agent: ClaudeAgent) -> None:
    """Test _extract_streaming_content with text type."""
    json_line = '{"type": "assistant", "message": {"content": [{"type": "text", "text": "This is text content"}]}}'
    result = claude_agent._extract_streaming_content(json_line)
    assert len(result) == 1
    # Text content is prepended with newlines for formatting
    assert result[0] == "\n\nThis is text content"


def test_extract_stream_content_tool_use_type(claude_agent: ClaudeAgent) -> None:
    """Test _extract_streaming_content with tool_use type."""
    json_line = (
        '{"type": "assistant", "message": {"content": ['
        '{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}'
        "]}}"
    )
    result = claude_agent._extract_streaming_content(json_line)
    assert len(result) == 1
    assert "Bash" in result[0]


def test_extract_stream_content_tool_use_no_name(claude_agent: ClaudeAgent) -> None:
    """Test _extract_streaming_content with tool_use type but no name."""
    json_line = '{"type": "assistant", "message": {"content": [{"type": "tool_use", "input": {}}]}}'
    result = claude_agent._extract_streaming_content(json_line)
    assert len(result) == 1
    assert "unknown" in result[0]


def test_extract_stream_content_unknown_type(claude_agent: ClaudeAgent) -> None:
    """Test _extract_streaming_content with unknown type."""
    json_line = '{"type": "unknown", "data": "something"}'
    result = claude_agent._extract_streaming_content(json_line)
    assert len(result) == 0  # Unknown types return empty list


def test_extract_stream_content_no_type(claude_agent: ClaudeAgent) -> None:
    """Test _extract_streaming_content with no type field."""
    json_line = '{"content": "no type field"}'
    result = claude_agent._extract_streaming_content(json_line)
    assert len(result) == 0  # No type returns empty list


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_configure_mcp_with_allowed_tools(mock_run_command: AsyncMock, claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp returns correctly formatted tool names."""
    mock_run_command.return_value = (True, '{"result": "server registered"}')
    mcp_json = json.dumps({"mcpServers": {"myserver": {"url": "http://localhost:8080"}}})
    mcp_tools = [
        McpTool(server="myserver", tools=["tool1", "tool2"]),
    ]

    allowed_tools = await claude_agent.configure_mcp("/fake/dir", mcp_json, mcp_tools)

    assert allowed_tools is not None
    assert set(allowed_tools) == {"mcp__myserver__tool1", "mcp__myserver__tool2"}


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_configure_mcp_no_allowed_tools(mock_run_command: AsyncMock, claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp without allowed tools list."""
    mock_run_command.return_value = (True, '{"result": "server registered"}')
    mcp_json = json.dumps({"mcpServers": {"server1": {"url": "http://localhost:8080"}}})

    allowed_tools = await claude_agent.configure_mcp("/fake/dir", mcp_json, None)

    assert allowed_tools is None


@pytest.mark.asyncio
async def test_configure_mcp_invalid_server_config(claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp with invalid server configuration format."""
    mcp_json = json.dumps({"mcpServers": {"server1": "not a dict"}})

    with patch("awa.core.utils.command_utils.CommandUtils.run_command_async"):
        # Should log warning and skip invalid servers
        result = await claude_agent.configure_mcp("/fake/dir", mcp_json)
        # Returns None because no allowed tools were specified
        assert result is None


@pytest.mark.asyncio
async def test_configure_mcp_not_dict(claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp when mcpServers is not a dictionary."""
    mcp_json = json.dumps({"mcpServers": ["not", "a", "dict"]})

    result = await claude_agent.configure_mcp("/fake/dir", mcp_json)
    assert result is None


@pytest.mark.asyncio
async def test_configure_mcp_empty_servers(claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp with empty server list."""
    mcp_json = json.dumps({"mcpServers": {}})

    result = await claude_agent.configure_mcp("/fake/dir", mcp_json)
    assert result is None


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_configure_mcp_already_exists(mock_run_command: AsyncMock, claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp when server already exists."""
    mock_run_command.return_value = (True, '{"message": "server already exists"}')
    mcp_json = json.dumps({"mcpServers": {"existing_server": {"url": "http://localhost:8080"}}})

    result = await claude_agent.configure_mcp("/fake/dir", mcp_json)
    # Should skip without error
    assert result is None


@pytest.mark.asyncio
@patch("awa.core.utils.command_utils.CommandUtils.run_command_async")
async def test_configure_mcp_registration_failure(mock_run_command: AsyncMock, claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp when server registration fails."""
    mock_run_command.return_value = (False, '{"error": "registration failed"}')
    mcp_json = json.dumps({"mcpServers": {"server1": {"url": "http://localhost:8080"}}})

    # Should process without raising exception
    result = await claude_agent.configure_mcp("/fake/dir", mcp_json)
    assert result is None


@pytest.mark.asyncio
async def test_configure_mcp_unexpected_error(claude_agent: ClaudeAgent) -> None:
    """Test configure_mcp with unexpected error during processing."""
    mcp_json = json.dumps({"mcpServers": {"server1": {"url": "http://localhost:8080"}}})

    with (
        patch("awa.core.utils.command_utils.CommandUtils.run_command_async", side_effect=RuntimeError("Unexpected")),
        pytest.raises(ValueError, match="An unexpected error occurred during MCP configuration"),
    ):
        await claude_agent.configure_mcp("/fake/dir", mcp_json)


@pytest.mark.asyncio
async def test_stream_output_with_prompt() -> None:
    """Test stream_output with a direct prompt."""
    claude_agent = ClaudeAgent()

    with patch("awa.core.utils.command_utils.CommandUtils.stream_command_async") as mock_stream:

        async def mock_generator() -> AsyncGenerator:
            mock_process = AsyncMock()
            mock_process.pid = 12345
            mock_process.returncode = 0
            yield mock_process

        mock_stream.return_value = mock_generator()

        with (
            patch("awa.core.api.socketio_server.emit_agent_stream_start"),
            patch("awa.core.api.socketio_server.emit_agent_stream_complete"),
        ):
            result = await claude_agent.stream_output(
                prompt="test prompt",
                working_dir="/fake/dir",
                session_id="test-session",
            )

    assert result.status


@pytest.mark.asyncio
async def test_stream_output_with_command_path() -> None:
    """Test stream_output with a command file path."""
    claude_agent = ClaudeAgent()

    with patch("awa.core.utils.command_utils.CommandUtils.stream_command_async") as mock_stream:
        # Mock the async generator
        async def mock_generator() -> AsyncGenerator:
            # First yield: process object
            mock_process = AsyncMock()
            mock_process.pid = 12345
            mock_process.returncode = 0
            yield mock_process
            # Subsequent yields: output lines
            yield '{"type": "text", "content": "output"}\n'

        mock_stream.return_value = mock_generator()

        with (
            patch("awa.core.api.socketio_server.emit_agent_stream_start"),
            patch("awa.core.api.socketio_server.emit_agent_stream_output"),
            patch("awa.core.api.socketio_server.emit_agent_stream_complete"),
        ):
            result = await claude_agent.stream_output(
                command_path="/path/to/command.txt",
                working_dir="/fake/dir",
                session_id="test-session",
            )

    assert result.status
    assert result.result is not None


@pytest.mark.asyncio
async def test_stream_output_no_prompt_or_command() -> None:
    """Test stream_output with neither prompt nor command path."""
    claude_agent = ClaudeAgent()

    with patch("awa.core.utils.command_utils.CommandUtils.stream_command_async") as mock_stream:
        # Mock the async generator
        async def mock_generator() -> AsyncGenerator:
            mock_process = AsyncMock()
            mock_process.pid = 12345
            mock_process.returncode = 0
            yield mock_process

        mock_stream.return_value = mock_generator()

        with (
            patch("awa.core.api.socketio_server.emit_agent_stream_start"),
            patch("awa.core.api.socketio_server.emit_agent_stream_complete"),
        ):
            result = await claude_agent.stream_output(
                working_dir="/fake/dir",
                session_id="test-session",
            )

    # Should use default prompt
    assert result.status


@pytest.mark.asyncio
async def test_stream_output_with_mcp_tools() -> None:
    """Test stream_output with MCP tools configured."""
    claude_agent = ClaudeAgent()

    with patch("awa.core.utils.command_utils.CommandUtils.stream_command_async") as mock_stream:

        async def mock_generator() -> AsyncGenerator:
            mock_process = AsyncMock()
            mock_process.pid = 12345
            mock_process.returncode = 0
            yield mock_process

        mock_stream.return_value = mock_generator()

        with (
            patch("awa.core.api.socketio_server.emit_agent_stream_start"),
            patch("awa.core.api.socketio_server.emit_agent_stream_complete"),
        ):
            await claude_agent.stream_output(
                prompt="test",
                mcp_tools=["mcp__server__tool1"],
                session_id="test-session",
            )

        # Verify MCP tools were included in command
        called_command = mock_stream.call_args[0][0]
        assert "mcp__server__tool1" in called_command


@pytest.mark.asyncio
async def test_stream_output_process_creation_failure() -> None:
    """Test stream_output when process creation fails."""
    claude_agent = ClaudeAgent()

    with patch("awa.core.utils.command_utils.CommandUtils.stream_command_async") as mock_stream:
        # Mock generator that doesn't yield a process
        async def mock_generator() -> AsyncGenerator:
            yield "not a process object"

        mock_stream.return_value = mock_generator()

        with (
            patch("awa.core.api.socketio_server.emit_agent_stream_start"),
            patch("awa.core.api.socketio_server.emit_agent_stream_error"),
        ):
            result = await claude_agent.stream_output(
                prompt="test",
                session_id="test-session",
            )

        assert not result.status
        assert "Failed to create Claude CLI process" in result.result


@pytest.mark.asyncio
async def test_stream_output_execution_error() -> None:
    """Test stream_output handles execution errors gracefully."""
    claude_agent = ClaudeAgent()

    with (
        patch("awa.core.utils.command_utils.CommandUtils.stream_command_async", side_effect=Exception("Stream error")),
        patch("awa.core.utils.streaming_http_client.emit_streaming_event_multi", return_value=[True]),
    ):
        result = await claude_agent.stream_output(
            prompt="test",
            session_id="test-session",
        )

        assert not result.status
        assert "Stream error" in result.result


@pytest.mark.asyncio
async def test_stream_output_process_cleanup_on_error() -> None:
    """Test stream_output cleans up process on error."""
    from unittest.mock import Mock

    claude_agent = ClaudeAgent()

    with patch("awa.core.utils.command_utils.CommandUtils.stream_command_async") as mock_stream:
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = None  # Still running
        # Make terminate a regular mock method (not async) since it's called synchronously
        mock_process.terminate = Mock()
        mock_process.wait = AsyncMock()

        async def mock_generator() -> AsyncGenerator:
            yield mock_process
            raise Exception("Streaming error")  # noqa: TRY002

        mock_stream.return_value = mock_generator()

        with (
            patch("awa.core.api.socketio_server.emit_agent_stream_start"),
            patch("awa.core.api.socketio_server.emit_agent_stream_error"),
        ):
            result = await claude_agent.stream_output(
                prompt="test",
                session_id="test-session",
            )

        # Verify process.terminate was called
        mock_process.terminate.assert_called_once()
        assert not result.status


@pytest.mark.asyncio
async def test_get_log_files(claude_agent: ClaudeAgent) -> None:
    """Test get_log_files method (currently a pass-through)."""
    result = await claude_agent.get_log_files("/fake/dir", "test-session")
    assert result is None


@pytest.mark.asyncio
async def test_cleanup(claude_agent: ClaudeAgent) -> None:
    """Test cleanup method (currently a pass-through)."""
    result = await claude_agent.cleanup("test-session")
    assert result is None


@pytest.mark.asyncio
async def test_initialize_failure(claude_agent: ClaudeAgent) -> None:
    """Test initialize with command failure."""
    with patch(
        "awa.core.utils.command_utils.CommandUtils.run_command_async",
        return_value=(False, "Error initializing"),
    ):
        result = await claude_agent.initialize("claude init", "/fake/dir")
        assert not result.status
        assert "Error" in result.result


@pytest.mark.asyncio
async def test_execute_command_with_mcp_tools(claude_agent: ClaudeAgent) -> None:
    """Test execute_command passes mcp_tools to execute_prompt."""
    with patch.object(claude_agent, "execute_prompt", new_callable=AsyncMock) as mock_execute:
        mcp_tools = ["mcp__server__tool1"]
        await claude_agent.execute_command("command.txt", "/fake/dir", mcp_tools, "session-123")

        # Verify execute_prompt was called with correct args
        assert mock_execute.call_count == 1
        call_args = mock_execute.call_args
        assert call_args[0][1] == "/fake/dir"
        assert call_args[0][2] == mcp_tools


def test_process_claude_output_with_multiple_results(claude_agent: ClaudeAgent) -> None:
    """Test _process_claude_output extracts final result from multiple JSON objects."""
    output = '{"result": "intermediate"}\n{"result": "final result"}\n'
    result = claude_agent._process_claude_output(status=True, result=output)
    assert result.status
    assert result.content == "final result"


def test_process_claude_output_non_string_result(claude_agent: ClaudeAgent) -> None:
    """Test _process_claude_output when result is not a string."""
    output = '{"result": 123}\n'
    result = claude_agent._process_claude_output(status=True, result=output)
    # Should not extract content if result is not a string
    assert result.content is None


@pytest.mark.asyncio
@patch("awa.core.utils.streaming_http_client.emit_streaming_event_multi")
async def test_execute_with_streaming_non_zero_return_code(mock_emit: AsyncMock) -> None:
    """Test stream_output with non-zero return code."""
    mock_emit.return_value = [True]
    claude_agent = ClaudeAgent()

    async def mock_stream_generator() -> AsyncGenerator:
        # First yield the process
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = 1  # Non-zero return code
        yield mock_process
        # Then yield output
        yield '{"type": "assistant", "message": {"content": [{"type": "text", "text": "error"}]}}\n'

    with patch("awa.core.utils.command_utils.CommandUtils.stream_command_async", return_value=mock_stream_generator()):
        result = await claude_agent.stream_output(
            prompt="test",
            working_dir="/fake/dir",
            session_id="test-session",
        )

    assert not result.status  # Should fail with non-zero return code


@pytest.mark.asyncio
@patch("awa.core.utils.streaming_http_client.emit_streaming_event_multi")
async def test_execute_with_streaming_invalid_json_lines(mock_emit: AsyncMock) -> None:
    """Test stream_output handles invalid JSON lines gracefully."""
    mock_emit.return_value = [True]
    claude_agent = ClaudeAgent()

    async def mock_stream_generator() -> AsyncGenerator:
        # First yield the process
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.returncode = 0
        yield mock_process
        # Then yield invalid and valid JSON
        yield "not json\n"
        yield '{"type": "assistant", "message": {"content": [{"type": "text", "text": "valid"}]}}\n'

    with patch("awa.core.utils.command_utils.CommandUtils.stream_command_async", return_value=mock_stream_generator()):
        result = await claude_agent.stream_output(
            prompt="test",
            working_dir="/fake/dir",
            session_id="test-session",
        )

    # Should continue processing despite invalid JSON
    assert result.status


@pytest.mark.asyncio
async def test_stream_output_without_session_id() -> None:
    """Test stream_output without session_id (no Socket.IO emissions)."""
    claude_agent = ClaudeAgent()

    with patch("awa.core.utils.command_utils.CommandUtils.stream_command_async") as mock_stream:

        async def mock_generator() -> AsyncGenerator:
            mock_process = AsyncMock()
            mock_process.pid = 12345
            mock_process.returncode = 0
            yield mock_process

        mock_stream.return_value = mock_generator()

        result = await claude_agent.stream_output(prompt="test")

    # Should work without Socket.IO emissions
    assert result.status


@pytest.mark.asyncio
async def test_execute_prompt_without_session_id_no_streaming() -> None:
    """Test execute_prompt without session_id uses non-streaming path."""
    claude_agent = ClaudeAgent()

    with patch("awa.core.utils.command_utils.CommandUtils.run_command_async", return_value=(True, '{"result": "ok"}')):
        result = await claude_agent.execute_prompt("test", "/fake/dir")

    assert result.status
    assert "ok" in result.result
