import contextlib
import json
import shlex
from typing import Any

from temporalio import activity

from awa.core.activities import constants
from awa.core.utils.command_utils import CommandUtils
from awa.core.utils.streaming_http_client import emit_streaming_event_multi
from awa.sdk.models.agent_modes.agent_configuration import McpTool
from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase, CommandResult


class ClaudeAgent(AgentModeBase):
    """Claude agent implementation for executing Claude CLI commands.

    This agent handles initialization and command execution through the Claude CLI,
    managing subprocess execution and output handling.
    """

    allowed_tools = (
        "Bash,Edit,MultiEdit,Write,Task,Agent,TodoRead,TodoWrite,Glob,Grep,Read,SlashCommand,WebFetch,WebSearch,Skills"
    )

    def get_init_file_name(self) -> str:
        """Return the filename expected for Claude agent initialization."""
        return constants.CLAUDE_INIT_FILE

    def get_init_command(self) -> str:
        """Return the command string used to initialize the Claude agent."""
        return f"claude -p /init --output-format stream-json --verbose --allowedTools {self.allowed_tools}"

    def get_result_file_name(self) -> str:
        """Return the filename where the Claude agent's execution result is stored."""
        return "claude_result.json"

    def supports_mcp(self) -> bool:
        """Indicate whether the agent supports Meta Command Prompt (MCP)."""
        return True

    def get_mcp_file_name(self) -> str:
        """Return the filename used for the Meta Command Prompt (MCP) file."""
        return constants.CLAUDE_MCP_FILE

    async def initialize(
        self,
        command: str,
        working_dir: str | None = None,
    ) -> CommandResult:
        status, result = await CommandUtils.run_command_async(command, working_dir, shell=False)
        return self._process_claude_output(status, result)

    async def execute_command(
        self,
        command: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        stream_enabled: bool = False,
    ) -> CommandResult:
        prompt = f"Read the content from this file {command} and execute"
        return await self.execute_prompt(prompt, working_dir, mcp_tools, session_id, stream_enabled)

    async def execute_prompt(
        self,
        prompt: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        stream_enabled: bool = False,
    ) -> CommandResult:
        """Execute prompt with real-time streaming to Socket.IO."""
        command_list: list[str] = [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--verbose",
        ]
        allowed_tools = self.allowed_tools

        if mcp_tools:
            tool_list: str = f"{','.join(mcp_tools)}"
            allowed_tools += f",{tool_list}"
            activity.logger.info(f"Claude has been configured with MCP tools: {tool_list}")

        command_list.extend(["--allowedTools", allowed_tools])
        command_str = " ".join(shlex.quote(s) for s in command_list)

        # Execute with streaming if session_id provided
        if session_id and stream_enabled:
            # Delegate to stream_output for proper streaming implementation
            return await self.stream_output(
                prompt=prompt,
                working_dir=working_dir,
                mcp_tools=mcp_tools,
                session_id=session_id,
            )
        status, result = await CommandUtils.run_command_async(command_str, working_dir, shell=False)

        processed_result = self._process_claude_output(status, result)
        return processed_result

    async def configure_mcp(
        self,
        working_dir: str,
        mcp_json: str,
        mcp_allowed_tools: list[McpTool] | None = None,
    ) -> list[str] | None:
        try:
            mcp_data: dict[str, Any] = json.loads(mcp_json)
            server_configs: dict[str, Any] = mcp_data.get("mcpServers", {})

            if not isinstance(server_configs, dict):
                activity.logger.error(
                    f"Invalid MCP JSON format: Expected 'mcpServers' to be a dictionary, got {type(server_configs)}",
                )
                return None

            if not server_configs:
                activity.logger.warning("No servers found under 'mcpServers' key in MCP JSON.")
                return None

            # Iterate through the server names (keys) and their configurations (values)
            for server_name, server_config in server_configs.items():
                if not isinstance(server_config, dict):
                    activity.logger.warning(
                        "Skipping server '%s' due to invalid configuration format (expected dict, got %s).",
                        server_name,
                        type(server_config),
                    )
                    continue

                # Convert the server config dict back to a JSON string for the command argument
                server_config_json_str: str = json.dumps(server_config)

                # Construct the command
                mcp_command: str = (
                    f"claude mcp add-json {server_name} -s local '{server_config_json_str}' --output-format stream-json"
                )
                activity.logger.info(f"Registering MCP server: {server_name}")
                activity.logger.debug(f"MCP command: {mcp_command}")

                status, result = await CommandUtils.run_command_async(  # noqa: S604
                    mcp_command,
                    working_dir=working_dir,
                    shell=True,
                )
                activity.logger.debug(f"Raw output from claude mcp add-json for server '{server_name}': {result!r}")
                if "already exists" in result:
                    activity.logger.debug(f"MCP server '{server_name}' already registered, skipping.")
                    continue

                processed_result = self._process_claude_output(status, result)

                if not processed_result.status:
                    activity.logger.error(f"Failed to register MCP server '{server_name}': {processed_result.result}")
                else:
                    activity.logger.debug(
                        f"Successfully registered MCP server '{server_name}': {processed_result.result}",
                    )

        except json.JSONDecodeError as e:
            activity.logger.exception("Failed to parse MCP JSON")
            raise ValueError(f"Failed to parse MCP JSON: {e}") from e
        except Exception as e:
            activity.logger.exception("An unexpected error occurred during MCP configuration")
            raise ValueError(f"An unexpected error occurred during MCP configuration: {e}") from e

        if mcp_allowed_tools:
            allowed_set = set()
            for allowed_tool_config in mcp_allowed_tools:
                for tool_name in allowed_tool_config.tool_names:
                    allowed_set.add(f"mcp__{allowed_tool_config.server_name}__{tool_name}")
            return list(allowed_set)
        return None

    async def stream_output(  # noqa: PLR0915
        self,
        prompt: str | None = None,
        command_path: str | None = None,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        parent_session_id: str | None = None,
    ) -> CommandResult:
        """Stream output from Claude CLI process in real-time via Socket.IO.

        This method captures and streams Claude CLI process output in real-time while
        also storing the complete output for historical retrieval.

        Args:
            prompt: The prompt to send to Claude
            command_path: Path to a command file to execute
            working_dir: Working directory for the command
            mcp_tools: List of MCP tools to enable
            session_id: Session ID for Socket.IO streaming coordination
            parent_session_id: Optional parent session ID to also stream to

        Returns:
            CommandResult with final parsed result maintaining existing interface

        """
        # Determine the prompt to use
        if prompt:
            actual_prompt = prompt
        elif command_path:
            actual_prompt = f"Read the content from this file {command_path} and execute"
        else:
            actual_prompt = "Please provide a simple response to test streaming functionality."

        # Build command exactly like execute_prompt()
        command_list: list[str] = [
            "claude",
            "-p",
            actual_prompt,
            "--output-format",
            "stream-json",
            "--verbose",
        ]
        allowed_tools = self.allowed_tools

        if mcp_tools:
            tool_list: str = f"{','.join(mcp_tools)}"
            allowed_tools += f",{tool_list}"
            activity.logger.info(f"Claude has been configured with MCP tools: {tool_list}")

        command_list.extend(["--allowedTools", allowed_tools])
        command_str = " ".join(shlex.quote(s) for s in command_list)

        # Initialize output storage and process variables
        complete_output = []
        process = None
        stream_started = False

        # Build list of session IDs to emit to (child and optionally parent)
        session_ids = [sid for sid in [session_id, parent_session_id] if sid]

        try:
            # Emit stream start event to all session IDs via HTTP
            if session_ids:
                try:
                    await emit_streaming_event_multi(
                        session_ids=session_ids,
                        event_type="agent_stream_start",
                        event_data={"agent_type": "claude", "status": "started"},
                    )
                    activity.logger.debug(f"Emitted stream start for sessions: {session_ids}")
                except Exception as e:  # noqa: BLE001
                    activity.logger.warning(f"Failed to emit stream start: {e}")
            stream_started = True

            # Use CommandUtils.stream_command_async() for real-time output capture
            async for item in CommandUtils.stream_command_async(command_str, working_dir, shell=False):
                # First yielded item is the process handle
                if not process:
                    if hasattr(item, "pid"):  # Check if it's a process object
                        process = item
                        activity.logger.debug(f"Process created with PID: {process.pid}")
                        continue
                    # If first item isn't a process, treat it as output
                    activity.logger.warning(f"Expected process object but got: {type(item)}")
                    complete_output.append(str(item))
                    continue

                # Subsequent items are output lines
                if isinstance(item, str):
                    # Store output for historical retrieval
                    complete_output.append(item)

                    # Extract and stream meaningful content via HTTP
                    if session_ids:
                        try:
                            content_items = self._extract_streaming_content(item)

                            if content_items:  # Only emit if we extracted meaningful content
                                # Emit each piece of content separately to all sessions via HTTP
                                for content_text in content_items:
                                    await emit_streaming_event_multi(
                                        session_ids=session_ids,
                                        event_type="agent_stream_output",
                                        event_data={
                                            "content": content_text,
                                            "chunk_index": len(complete_output) - 1,
                                            "is_final": False,
                                            "agent_type": "claude",
                                        },
                                    )
                        except Exception:  # noqa: BLE001
                            activity.logger.exception("Stream emit failed")

            # Process completed, check return code
            if process:
                return_code = process.returncode
                status = return_code == 0

                # Join all output for final processing
                final_output = "".join(complete_output)

                # Emit successful stream end to all sessions via HTTP
                if session_ids:
                    try:
                        await emit_streaming_event_multi(
                            session_ids=session_ids,
                            event_type="agent_stream_complete",
                            event_data={
                                "final_result": {"final_output": final_output},
                                "execution_time": None,
                                "agent_type": "claude",
                                "status": "completed",
                            },
                        )
                        activity.logger.debug(f"Emitted stream complete for sessions {session_ids}")
                    except Exception as e:  # noqa: BLE001
                        activity.logger.warning(f"Failed to emit stream complete: {e}")

                # Use lenient parsing for streaming mode to avoid failures on malformed JSON
                # We've already extracted and emitted the meaningful content during streaming
                return self._process_claude_output_streaming(status, final_output)
            # No process was created
            if session_ids:
                try:
                    await emit_streaming_event_multi(
                        session_ids=session_ids,
                        event_type="agent_stream_error",
                        event_data={
                            "error": "Failed to create process",
                            "error_code": "PROCESS_ERROR",
                            "agent_type": "claude",
                            "status": "error",
                        },
                    )
                except Exception as e:  # noqa: BLE001
                    activity.logger.warning(f"Failed to emit stream error: {e}")
            return CommandResult(
                status=False,
                result="Error: Failed to create Claude CLI process",
                content=None,
            )

        except Exception as e:  # noqa: BLE001
            activity.logger.exception("Error during Claude CLI streaming")

            # Emit error stream end if we started streaming via HTTP
            if stream_started and session_ids:
                try:
                    await emit_streaming_event_multi(
                        session_ids=session_ids,
                        event_type="agent_stream_error",
                        event_data={
                            "error": str(e),
                            "error_code": "EXECUTION_ERROR",
                            "agent_type": "claude",
                            "status": "error",
                        },
                    )
                except Exception as emit_error:  # noqa: BLE001
                    activity.logger.warning(f"Failed to emit stream error: {emit_error}")

            # Handle cleanup
            if process:
                try:
                    if process.returncode is None:
                        process.terminate()
                        # Give process time to terminate gracefully
                        with contextlib.suppress(Exception):
                            await process.wait()
                except Exception as cleanup_error:  # noqa: BLE001
                    activity.logger.warning(f"Error during process cleanup: {cleanup_error}")

            # Return error result maintaining existing interface
            return CommandResult(
                status=False,
                result=f"Error during Claude CLI execution: {e}",
                content=None,
            )

    def _process_claude_output(self, status: bool, result: str) -> CommandResult:
        activity.logger.debug(f"Raw output from Claude agent: {result}")
        content: str | None = None
        try:
            result_items = self._parse_newline_separated_json(json_string=result)
            if result_items:
                final_result = result_items[-1]
                if "result" in final_result and isinstance(final_result["result"], str):
                    content = final_result["result"]
                if final_result.get("result", "").startswith("API Error:"):
                    status = False
                result = json.dumps(result_items, indent=2)
        except Exception as e:  # noqa: BLE001
            # Ignore
            status = False
            result = f"Error parsing JSON result from Claude. Error: \n{e}\n\nResult:\n{result}"

        return CommandResult(status=status, result=result, content=content)

    def _process_claude_output_streaming(self, status: bool, result: str) -> CommandResult:
        """Process Claude output from streaming mode with lenient parsing.

        In streaming mode, we've already emitted the meaningful content in real-time.
        This method extracts a summary for the final result without failing on parse errors.
        """
        activity.logger.debug(f"Processing streaming output, length: {len(result)}")
        content: str | None = None

        try:
            # Use lenient parsing to skip any malformed JSON lines
            result_items = self._parse_newline_separated_json(json_string=result, lenient=True)

            if result_items:
                # Extract all assistant text messages
                text_messages = []
                for item in result_items:
                    if item.get("type") == "assistant" and "message" in item:
                        message = item["message"]
                        if "content" in message:
                            text_messages.extend(
                                content_block.get("text", "")
                                for content_block in message["content"]
                                if content_block.get("type") == "text"
                            )

                # Last text message is the final result
                activity.logger.debug(f"Text messages: {text_messages}")  # TODO RH: Remove this
                if text_messages:
                    content = text_messages[-1]

                # Check for errors in the final result
                if result_items[-1].get("type") == "result":
                    final_result = result_items[-1]
                    if final_result.get("result", "").startswith("API Error:"):
                        status = False

                # For the result field, provide a compact summary
                result = json.dumps({"status": "success" if status else "failed", "messages": len(text_messages)})

        except Exception as e:  # noqa: BLE001
            activity.logger.warning(f"Error processing streaming output: {e}")
            # Don't fail - just return what we have
            if not content:
                content = "Streaming completed"

        return CommandResult(status=status, result=result, content=content)

    @staticmethod
    def _parse_newline_separated_json(json_string: str, lenient: bool = False) -> list[dict[str, Any]]:
        """Parse newline-separated JSON from Claude CLI output.

        Args:
            json_string: The raw output string containing JSON lines
            lenient: If True, skip invalid lines instead of raising errors

        Returns:
            List of parsed JSON objects

        Raises:
            ValueError: If parsing fails and lenient=False

        """
        json_objects: list[dict[str, Any]] = []
        lines = json_string.strip().split("\n")
        for line_item in lines:
            line = line_item.strip()
            if line:  # Ensure the line is not empty
                try:
                    json_obj = json.loads(line)
                    json_objects.append(json_obj)
                except json.JSONDecodeError as e:
                    if lenient:
                        activity.logger.debug(f"Skipping invalid JSON line in lenient mode: {line[:100]}...")
                        continue
                    raise ValueError(
                        f"Could not decode JSON from Claude output, line: {line[:100]}...",
                    ) from e
        return json_objects

    @staticmethod
    def _extract_streaming_content(json_line: str) -> list[str]:
        """Extract meaningful content from a Claude CLI stream-json event.

        Args:
            json_line: A single line of JSON output from Claude CLI

        Returns:
            List of extracted text content to display (may be empty if event should be skipped)

        """
        try:
            event_data = json.loads(json_line.strip())
            results = []

            # Assistant message - can contain multiple content blocks
            if event_data.get("type") == "assistant" and "message" in event_data:
                message = event_data["message"]
                if "content" in message:
                    for content_block in message["content"]:
                        block_type = content_block.get("type")

                        # Text content
                        if block_type == "text":
                            text = content_block.get("text", "")
                            if text:
                                results.append(f"\n\n{text}")

                        # Tool use within message
                        elif block_type == "tool_use":
                            tool_name = content_block.get("name", "unknown")
                            tool_input = content_block.get("input", {})
                            # Create a readable tool use message
                            if tool_input:
                                # Show all parameters
                                params_list = []
                                for param_name, param_value in tool_input.items():
                                    # Truncate long values
                                    param_str = str(param_value)[:5000]
                                    params_list.append(f"{param_name}={param_str}")
                                params_formatted = ", ".join(params_list)
                                results.append(f"\n\n🔧 Using {tool_name}: {params_formatted}")
                            else:
                                results.append(f"\n\n🔧 Using {tool_name}")

            # User messages (tool results)
            elif event_data.get("type") == "user":
                message = event_data.get("message", {})
                if "content" in message:
                    tool_results = [
                        "\n✓ Tool completed"
                        for content_block in message["content"]
                        if content_block.get("type") == "tool_result"
                    ]
                    results.extend(tool_results)

            # Thinking events (extended thinking)
            elif event_data.get("type") == "thinking":
                thinking_text = event_data.get("content", "")
                if thinking_text:
                    max_thinking_length = 100
                    if len(thinking_text) > max_thinking_length:
                        results.append(f"\n\n💭 {thinking_text[:max_thinking_length]}...")
                    else:
                        results.append(f"\n\n💭 {thinking_text}")

            # System events (skip these, they're just metadata)
            elif event_data.get("type") == "system":
                pass  # Skip system events

            return results

        except json.JSONDecodeError:
            # If not valid JSON, skip it
            activity.logger.debug(f"Skipping non-JSON line: {json_line[:100]}...")
            return []
        except Exception as e:  # noqa: BLE001
            activity.logger.warning(f"Error extracting streaming content: {e}")
            return []

    async def get_log_files(
        self,
        working_dir: str | None = None,
        session_id: str | None = None,
    ) -> None:
        pass

    async def cleanup(self, session_id: str | None = None) -> None:
        pass
