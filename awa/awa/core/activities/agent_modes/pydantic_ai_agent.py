import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastmcp import Client
from pydantic_ai import Agent, RunContext
from pydantic_ai.durable_exec.temporal import TemporalAgent

from awa.core.activities.mcp_tool import invoke_mcp_tool
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.config_loader import ConfigLoader
from awa.core.utils.streaming_http_client import emit_streaming_event_via_http
from awa.sdk.models.agent_modes.agent_configuration import McpTool
from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase, CommandResult

logger = get_logger(LoggerComponent.ACTIVITY)


# Track emitted events count for each session (for reporting purposes)
_session_event_counts: dict[str, int] = defaultdict(int)

# Track actual streaming events for each session (for API retrieval)
_session_streaming_events: dict[str, list[dict[str, Any]]] = defaultdict(list)


class PydanticAIAgent(AgentModeBase):
    """PydanticAI agent implementation for executing AI agents with durable execution.

    This agent handles initialization and execution of PydanticAI agents through
    Temporal's durable execution framework, managing model configuration, tool setup,
    and execution with proper error handling.

    The agent automatically uses the default LLM configuration from config.yaml,
    following the same pattern as AWA's BAML transform activities.
    """

    def _get_pydantic_ai_model_string(self, model_name: str | None = None) -> str:
        """Convert AWA model configuration to PydanticAI model string format.

        Args:
            model_name: Optional specific model name, defaults to config default

        Returns:
            Model string in PydanticAI format (e.g., "azure:gpt-4", "openai:gpt-4")

        """
        try:
            app_config = ConfigLoader.get_config()

            # Use provided model name or fall back to default
            target_model = model_name or app_config.llm.default_model

            # Find the model configuration
            model_config = None
            for model in app_config.llm.models:
                if model.name == target_model:
                    model_config = model
                    break

            if not model_config:
                logger.warning(f"Model '{target_model}' not found in config, using default format")
                return f"openai:{target_model}"

            # Convert AWA provider format to PydanticAI format
            provider_mapping = {
                "AzureOpenAI": "azure",
                "OpenAI": "openai",
                "AnthropicAI": "anthropic",
                "GoogleVertex": "google-vertex",
                "AwsBedrock": "bedrock",
            }

            pydantic_provider = provider_mapping.get(model_config.provider, "openai")
            model_identifier = model_config.model

            pydantic_model_string = f"{pydantic_provider}:{model_identifier}"
            logger.info(f"Using PydanticAI model: {pydantic_model_string} (from AWA config: {target_model})")

            return pydantic_model_string

        except (OSError, ValueError, ImportError, AttributeError) as e:
            logger.warning(f"Failed to load AWA config, using fallback: {e}")
            return "openai:gpt-4"

    def supports_mcp(self) -> bool:
        """Indicate whether the agent supports Meta Command Prompt (MCP)."""
        return True

    @classmethod
    async def emit_streaming_event(cls, session_id: str, event_type: str, event_data: dict[str, Any]) -> None:
        """Emit a streaming event via HTTP to Socket.IO server and track the count.

        This method uses HTTP communication to bridge cross-process streaming
        between Temporal worker and API server processes.

        Args:
            session_id: The session identifier
            event_type: Type of the streaming event
            event_data: The event data to emit

        """
        if session_id:
            try:
                success = await emit_streaming_event_via_http(
                    session_id=session_id,
                    event_type=event_type,
                    event_data=event_data,
                    timestamp=datetime.now(UTC),
                )

                if success:
                    _session_event_counts[session_id] += 1
                    # Store the event for API retrieval
                    event_record = {
                        "type": event_type,
                        "data": event_data,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "session_id": session_id,
                    }
                    _session_streaming_events[session_id].append(event_record)
                    count = _session_event_counts[session_id]
                    logger.debug(f"Emitted {event_type} event for session {session_id} (count: {count})")
                else:
                    logger.warning(f"Failed to emit {event_type} event for session {session_id} via HTTP")

            except (OSError, ValueError, RuntimeError):
                logger.exception(f"Failed to emit {event_type} event for session {session_id}")

    @classmethod
    def get_session_event_count(cls, session_id: str) -> int:
        """Get the number of events emitted for a session.

        Args:
            session_id: The session identifier

        Returns:
            Number of events emitted for the session

        """
        return _session_event_counts.get(session_id, 0)

    @classmethod
    def get_streaming_events(cls, session_id: str) -> list[dict[str, Any]]:
        """Get all streaming events for a session.

        Args:
            session_id: The session identifier

        Returns:
            List of streaming events for the session

        """
        return _session_streaming_events.get(session_id, [])

    @classmethod
    def _store_streaming_event(cls, session_id: str, event_record: dict[str, Any]) -> None:
        """Store a streaming event for a session (used by API server).

        Args:
            session_id: The session identifier
            event_record: The event record to store

        """
        _session_streaming_events[session_id].append(event_record)

    @classmethod
    def clear_session_event_count(cls, session_id: str) -> None:
        """Clear the event count and streaming events for a session.

        Args:
            session_id: The session identifier

        """
        _session_event_counts.pop(session_id, None)
        _session_streaming_events.pop(session_id, None)
        logger.debug(f"Cleared event count and streaming events for session {session_id}")

    def get_result_file_name(self) -> str:
        """Return the filename where the PydanticAI agent's execution result is stored."""
        return "pydantic_ai_result.json"

    async def initialize(
        self,
        command: str,
        working_dir: str | None = None,  # noqa: ARG002
        session_id: str | None = None,
    ) -> CommandResult:
        """Initialize the PydanticAI agent.

        Args:
            command: Initialization command (typically the agent name)
            working_dir: Working directory for execution
            session_id: Session identifier

        Returns:
            CommandResult indicating initialization success

        """
        logger.info(f"Initializing PydanticAI agent: {command}")
        return CommandResult(
            status=True,
            result="PydanticAI agent initialized successfully",
            session_id=session_id,
        )

    async def execute_command(
        self,
        command: str,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        """Execute a command file with the PydanticAI agent.

        Args:
            command: Path to command file to execute
            working_dir: Working directory for execution
            mcp_tools: Available MCP tools
            session_id: Session identifier
            stream_enabled: Whether to enable streaming output

        Returns:
            CommandResult with execution results

        """
        # For command files, read the content and execute as prompt
        try:
            command_path = Path(working_dir) / command if working_dir else Path(command)
            prompt = command_path.read_text()

            return await self.execute_prompt(prompt, working_dir, mcp_tools, session_id)
        except (OSError, ValueError) as e:
            logger.exception(f"Failed to read command file: {command}")
            return CommandResult(
                status=False,
                result=f"Failed to read command file: {e}",
                session_id=session_id,
            )

    def _parse_prompt_config(self, prompt: str) -> dict[str, str | None]:
        """Parse optional configuration from prompt.

        Args:
            prompt: The prompt to parse

        Returns:
            Dict with parsed configuration values

        """
        # Default configuration
        agent_name = "default_agent"
        instructions = "You are a helpful assistant."
        custom_model = None
        actual_prompt = prompt

        # Check if prompt contains PydanticAI configuration at the start
        if prompt.strip().startswith("{"):
            try:
                config_data = json.loads(prompt)
                if isinstance(config_data, dict) and (
                    "agent_name" in config_data or "instructions" in config_data or "model" in config_data
                ):
                    # This is PydanticAI configuration
                    agent_name = config_data.get("agent_name", agent_name)
                    instructions = config_data.get("instructions", instructions)
                    actual_prompt = config_data.get("prompt", prompt)

                    # Handle custom model configuration (optional override)
                    model_config = config_data.get("model", {})
                    if model_config and isinstance(model_config, dict):
                        provider = model_config.get("provider", "openai")
                        model_name = model_config.get("model", "gpt-4")
                        custom_model = f"{provider}:{model_name}"
            except (json.JSONDecodeError, TypeError):
                # If not valid JSON or wrong format, use prompt as-is
                pass

        return {
            "agent_name": agent_name,
            "instructions": instructions,
            "actual_prompt": actual_prompt,
            "custom_model": custom_model,
        }

    def _create_success_result(
        self,
        result: Any,  # noqa: ANN401
        agent_name: str,
        execution_time: float,
        model_str: str,
        session_id: str | None,
    ) -> CommandResult:
        """Create a successful CommandResult from agent execution result.

        Args:
            result: The agent execution result
            agent_name: Name of the agent
            execution_time: Time taken for execution
            model_str: Model string used
            session_id: Session identifier

        Returns:
            CommandResult with success status

        """
        result_data = {
            "agent_name": agent_name,
            "output": result.output,
            "execution_time": execution_time,
            "model_str": model_str,
        }

        # Add usage stats if available
        if hasattr(result, "usage") and result.usage:
            try:
                # Convert usage to dict if it's not already serializable
                if hasattr(result.usage, "__dict__"):
                    result_data["usage_stats"] = result.usage.__dict__
                else:
                    result_data["usage_stats"] = str(result.usage)
            except (AttributeError, TypeError, ValueError):
                # If usage can't be serialized, skip it
                pass

        return CommandResult(
            status=True,
            result=json.dumps(result_data, indent=2),
            content=str(result.output),
            session_id=session_id,
        )

    async def _setup_agent_execution(
        self,
        agent: Any,  # noqa: ANN401
        mcp_tools: list[str] | None,
        session_id: str | None,
        agent_name: str,
        model_str: str,
        actual_prompt: str,
    ) -> None:
        """Set up MCP tools and emit initial execution events.

        Args:
            agent: The PydanticAI agent instance
            mcp_tools: Available MCP tools
            session_id: Session identifier
            agent_name: Name of the agent
            model_str: Model string used
            actual_prompt: The prompt to execute

        """
        # Set up MCP tools if provided
        if mcp_tools:
            logger.info(f"Registering {len(mcp_tools)} MCP tools with PydanticAI agent")
            await self._register_mcp_tools(agent, mcp_tools, session_id)
            logger.info("MCP tool registration completed")
        else:
            logger.debug("No MCP tools provided to execute_prompt")

        # Add initial execution event
        logger.info(f"Adding execution_start event for session: {session_id}")
        await self.emit_streaming_event(
            session_id,
            "execution_start",
            {
                "agent_name": agent_name,
                "model": model_str,
                "prompt_length": len(actual_prompt),
            },
        )
        current_events = self.get_session_event_count(session_id)
        logger.info(f"Current events count for {session_id}: {current_events}")

    async def _handle_execution_completion(
        self,
        result: Any,  # noqa: ANN401
        session_id: str | None,
        execution_time: float,
        agent_name: str,
        model_str: str,
    ) -> CommandResult:
        """Handle agent execution completion and create result.

        Args:
            result: The agent execution result
            session_id: Session identifier
            execution_time: Time taken for execution
            agent_name: Name of the agent
            model_str: Model string used

        Returns:
            CommandResult with success status

        """
        # Add completion event
        logger.info(f"Adding execution_complete event for session: {session_id}")
        await self.emit_streaming_event(
            session_id,
            "execution_complete",
            {
                "execution_time": execution_time,
                "status": "success",
            },
        )

        # Check events after completion
        final_events = self.get_session_event_count(session_id)
        logger.info(f"Total events after completion for {session_id}: {final_events}")

        # Create result
        return self._create_success_result(result, agent_name, execution_time, model_str, session_id)

    async def execute_prompt(
        self,
        prompt: str,
        working_dir: str | None = None,  # noqa: ARG002
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        stream_enabled: bool = False,  # noqa: ARG002
    ) -> CommandResult:
        """Execute a prompt with the PydanticAI agent.

        Args:
            prompt: The prompt to execute
            working_dir: Working directory for execution
            mcp_tools: Available MCP tools
            session_id: Session identifier
            stream_enabled: Whether to enable streaming output

        Returns:
            CommandResult with execution results

        """
        start_time = time.time()
        logger.info(f"Starting execute_prompt with session_id: {session_id}")
        logger.info("Executing PydanticAI agent prompt")

        # Add a test event to confirm this agent is being called
        await self.emit_streaming_event(
            session_id,
            "test_agent_execution",
            {
                "message": "PydanticAI agent is executing",
                "session_id": session_id,
            },
        )

        try:
            # Parse optional configuration from prompt
            config = self._parse_prompt_config(prompt)
            agent_name = config["agent_name"]
            instructions = config["instructions"]
            actual_prompt = config["actual_prompt"]
            custom_model = config["custom_model"]

            # Get model from AWA config (with optional override)
            if custom_model:
                model_str = custom_model
                logger.info(f"Using custom model from prompt: {model_str}")
            else:
                model_str = self._get_pydantic_ai_model_string()
                logger.info(f"Using model from AWA config: {model_str}")

            # Create PydanticAI agent
            agent = Agent(
                model=model_str,
                instructions=instructions,
                name=agent_name,
            )

            # Set up MCP tools and emit initial events
            await self._setup_agent_execution(agent, mcp_tools, session_id, agent_name, model_str, actual_prompt)

            # Create event stream handler to capture streaming events
            async def event_stream_handler(
                run_context: Any,  # noqa: ARG001, ANN401
                event_stream: Any,  # noqa: ANN401
            ) -> None:
                """Handle streaming events from PydanticAI agent execution."""
                logger.info(f"Event stream handler called for session: {session_id}")
                async for event in event_stream:
                    logger.debug(f"Received streaming event: {type(event).__name__}")
                    event_data = {
                        "type": type(event).__name__,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }

                    # Handle different event types
                    if hasattr(event, "part_kind"):
                        event_data["part_kind"] = event.part_kind
                    if hasattr(event, "content"):
                        event_data["content"] = str(event.content)
                    if hasattr(event, "delta"):
                        event_data["delta"] = str(event.delta)
                    if hasattr(event, "tool_name"):
                        event_data["tool_name"] = event.tool_name
                    if hasattr(event, "result"):
                        event_data["result"] = str(event.result)[:500]  # Limit size

                    # Store the event for streaming API
                    await self.emit_streaming_event(session_id, event_data.get("type", "unknown"), event_data)

            # Create TemporalAgent wrapper for durable execution
            temporal_agent = TemporalAgent(agent, event_stream_handler=event_stream_handler)

            # Execute the agent
            logger.info(f"Executing agent with prompt length: {len(actual_prompt)} characters")
            result = await temporal_agent.run(actual_prompt)

            execution_time = time.time() - start_time
            logger.info(f"Agent execution completed in {execution_time:.2f} seconds")

            # Handle completion and create result
            return await self._handle_execution_completion(
                result,
                session_id,
                execution_time,
                agent_name,
                model_str,
            )

        except (RuntimeError, ValueError, TypeError, OSError) as e:
            execution_time = time.time() - start_time
            error_msg = f"PydanticAI agent execution failed: {e!s}"
            logger.exception(error_msg)

            # Add error event
            await self.emit_streaming_event(
                session_id,
                "execution_error",
                {
                    "execution_time": execution_time,
                    "status": "failed",
                    "error": error_msg,
                    "error_type": type(e).__name__,
                },
            )

            error_data = {
                "error": error_msg,
                "execution_time": execution_time,
                "error_type": type(e).__name__,
            }

            return CommandResult(
                status=False,
                result=json.dumps(error_data, indent=2),
                session_id=session_id,
            )

    async def _discover_mcp_tools(self, mcp_config: dict[str, Any]) -> list[str]:
        """Discover available tools from MCP servers.

        Args:
            mcp_config: MCP configuration dictionary

        Returns:
            List of tool names in format "server_name__tool_name"

        """
        logger.debug("Discovering MCP tools from configuration")
        discovered_tools = []
        mcp_servers = mcp_config.get("mcpServers", {})
        logger.info(f"Found {len(mcp_servers)} MCP servers")

        for server_name, server_config in mcp_servers.items():
            try:
                logger.info(f"Discovering tools from MCP server: {server_name}")
                logger.debug(f"Server config: {server_config}")

                # For command-based MCP servers, we need to use the invoke_mcp_tool pattern
                # Since FastMCP Client expects a running server, we'll use a simpler approach
                # and just return the expected tool names for the filesystem server for now
                if "command" in server_config:
                    # This is a command-based server - connect and discover tools dynamically
                    try:
                        # Create a temporary client to connect to the command-based server
                        logger.info(f"Connecting to command-based MCP server: {server_name}")
                        client = Client(mcp_config)
                        async with client:
                            tools = await client.list_tools()
                            logger.info(f"Found {len(tools)} tools from command-based server {server_name}")
                            for tool in tools:
                                tool_name = f"{server_name}__{tool.name}"
                                discovered_tools.append(tool_name)
                                logger.info(f"Discovered {server_name} tool: {tool_name}")
                                logger.debug(f"Tool description: {tool.description}")
                    except (OSError, ValueError, RuntimeError, ConnectionError):
                        logger.exception(f"Failed to discover tools from command-based server {server_name}")
                        logger.exception("Full exception details:")
                elif "url" in server_config:
                    # URL-based server - try to connect and list tools
                    try:
                        client = Client(server_config)
                        async with client:
                            tools = await client.list_tools()
                            logger.info(f"Found {len(tools)} tools from server {server_name}")
                            for tool in tools:
                                tool_name = f"{server_name}__{tool.name}"
                                discovered_tools.append(tool_name)
                                logger.debug(f"Discovered tool: {tool_name} - {tool.description}")
                    except (OSError, ValueError, RuntimeError, ConnectionError) as e:
                        logger.warning(f"Failed to connect to URL-based server {server_name}: {e}")
                else:
                    logger.warning(f"Unknown server configuration format for {server_name}")

            except (OSError, ValueError, RuntimeError, ConnectionError) as e:
                logger.warning(f"Failed to discover tools from server {server_name}: {e}")
                continue

        logger.info(f"Total discovered MCP tools: {len(discovered_tools)}")
        return discovered_tools

    async def _register_mcp_tools(self, agent: Agent, mcp_tool_names: list[str], session_id: str | None) -> None:
        """Register MCP tools as PydanticAI tools.

        Args:
            agent: PydanticAI agent instance
            mcp_tool_names: List of MCP tool names in format "server_name__tool_name"
            session_id: Session ID for streaming events

        """
        logger.debug(f"Registering {len(mcp_tool_names)} MCP tools with PydanticAI agent")

        # Store MCP config for tool execution - we'll get it from the configured agent
        # For now, we'll need to pass it through the execution context
        mcp_config = getattr(self, "_current_mcp_config", None)
        logger.debug(f"MCP config available: {mcp_config is not None}")

        if not mcp_config:
            logger.warning("No MCP config available for tool registration")
            return

        for tool_name in mcp_tool_names:
            try:
                # Extract server name and tool name for proper MCP invocation
                server_name, actual_tool_name = tool_name.split("__", 1) if "__" in tool_name else ("", tool_name)

                # Create a tool wrapper function for this MCP tool
                def create_mcp_tool_wrapper(
                    server_name: str,
                    actual_tool_name: str,
                    full_tool_name: str,
                ) -> Any:  # noqa: ANN401
                    async def mcp_tool_function(
                        ctx: RunContext[None],  # noqa: ARG001
                        **kwargs: Any,  # noqa: ANN401
                    ) -> str:
                        """Execute MCP tool with provided arguments."""
                        try:
                            logger.info(
                                f"Executing MCP tool: {full_tool_name} (server: {server_name}, "
                                f"tool: {actual_tool_name}) with args: {kwargs}",
                            )

                            # Emit streaming event for tool call
                            if session_id:
                                await self.emit_streaming_event(
                                    session_id,
                                    "mcp_tool_call",
                                    {
                                        "tool_name": full_tool_name,
                                        "server_name": server_name,
                                        "actual_tool_name": actual_tool_name,
                                        "parameters": kwargs,
                                    },
                                )

                            # Call the MCP tool directly (we're already in an activity context)
                            # The invoke_mcp_tool expects the actual tool name, not the prefixed version
                            result = await invoke_mcp_tool(mcp_config, actual_tool_name, kwargs)

                            # Check if result is an error dictionary
                            if isinstance(result, dict) and "error" in result:
                                error_msg = result["error"]
                                logger.warning(f"MCP tool {full_tool_name} returned error: {error_msg}")

                                # Emit streaming event for tool error
                                if session_id:
                                    await self.emit_streaming_event(
                                        session_id,
                                        "mcp_tool_error",
                                        {
                                            "tool_name": full_tool_name,
                                            "error": error_msg,
                                        },
                                    )

                                # Return error message to agent for self-correction
                                return f"Error: {error_msg}"

                            # Emit streaming event for tool result
                            if session_id:
                                await self.emit_streaming_event(
                                    session_id,
                                    "mcp_tool_result",
                                    {
                                        "tool_name": full_tool_name,
                                        "result": str(result)[:500],  # Limit size for logging
                                    },
                                )

                            logger.info(f"MCP tool {full_tool_name} completed successfully")
                            return str(result)

                        except (OSError, ValueError, RuntimeError, ConnectionError) as e:
                            error_msg = f"MCP tool {full_tool_name} failed: {e}"
                            logger.exception(error_msg)

                            # Emit streaming event for tool error
                            if session_id:
                                await self.emit_streaming_event(
                                    session_id,
                                    "mcp_tool_error",
                                    {
                                        "tool_name": full_tool_name,
                                        "error": error_msg,
                                    },
                                )

                            # Return error message to agent instead of raising
                            # This allows the agent to see the error and self-correct
                            return f"Error executing tool: {error_msg}"

                    return mcp_tool_function

                # Register the tool with PydanticAI agent
                logger.debug(f"Creating tool wrapper for {tool_name}")
                tool_wrapper = create_mcp_tool_wrapper(server_name, actual_tool_name, tool_name)

                # Use the tool decorator to register it
                # The tool name should be the simple name without server prefix for PydanticAI
                simple_tool_name = actual_tool_name
                logger.debug(f"Registering tool '{simple_tool_name}' with agent")

                try:
                    agent.tool(name=simple_tool_name)(tool_wrapper)
                    logger.debug(f"Tool registration successful for '{simple_tool_name}'")
                except (TypeError, ValueError, AttributeError):
                    logger.exception(f"Tool registration failed for '{simple_tool_name}'")
                    raise

                logger.info(f"Registered MCP tool '{tool_name}' as PydanticAI tool '{simple_tool_name}'")

            except (TypeError, ValueError, AttributeError) as e:
                logger.warning(f"Failed to register MCP tool {tool_name}: {e}")
                continue

    async def configure_mcp(
        self,
        working_dir: str,  # noqa: ARG002
        mcp_json: str,
        mcp_allowed_tools: list[McpTool] | None = None,
    ) -> list[str] | None:
        """Configure MCP tools for the PydanticAI agent.

        Args:
            working_dir: Working directory
            mcp_json: MCP configuration JSON
            mcp_allowed_tools: Allowed MCP tools

        Returns:
            List of configured tool names

        """
        logger.info("Configuring MCP tools for PydanticAI agent")

        try:
            # Parse MCP configuration
            mcp_data = json.loads(mcp_json)
            logger.info(f"Parsed MCP configuration with {len(mcp_data.get('mcpServers', {}))} servers")

            # Store MCP config for later use during tool registration
            self._current_mcp_config = mcp_data

            # Discover available tools from MCP servers
            discovered_tools = await self._discover_mcp_tools(mcp_data)

            # Filter tools based on allowed tools if specified
            if mcp_allowed_tools:
                allowed_set = set()
                for tool_config in mcp_allowed_tools:
                    for tool_name in tool_config.tool_names:
                        full_tool_name = f"{tool_config.server_name}__{tool_name}"
                        allowed_set.add(full_tool_name)

                # Only return tools that are in the allowed set
                filtered_tools = [tool for tool in discovered_tools if tool in allowed_set]
                logger.info(f"Filtered to {len(filtered_tools)} allowed tools")
                return filtered_tools
            # Return all discovered tools
            return discovered_tools

        except (OSError, ValueError, RuntimeError, TypeError) as e:
            logger.exception("Failed to configure MCP tools")
            raise ValueError(f"Failed to configure MCP tools: {e}") from e

    async def stream_output(
        self,
        prompt: str | None = None,
        command_path: str | None = None,
        working_dir: str | None = None,
        mcp_tools: list[str] | None = None,
        session_id: str | None = None,
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> CommandResult:
        """Stream live output from PydanticAI agent execution.

        Args:
            prompt: The prompt to execute
            command_path: Path to command file (unused for PydanticAI)
            working_dir: Working directory for execution
            mcp_tools: Available MCP tools
            session_id: Session identifier
            **kwargs: Additional keyword arguments

        Returns:
            CommandResult with streaming execution results

        """
        # For PydanticAI, stream_output is equivalent to execute_prompt
        # since streaming is handled internally via event_stream_handler
        if prompt:
            return await self.execute_prompt(prompt, working_dir, mcp_tools, session_id)
        if command_path:
            return await self.execute_command(command_path, working_dir, mcp_tools, session_id)

        return CommandResult(
            status=False,
            result="Either prompt or command_path must be provided",
            session_id=session_id,
        )

    async def get_log_files(
        self,
        working_dir: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """Get log files for the agent execution."""
        # PydanticAI agents don't generate separate log files

    async def cleanup(self, session_id: str | None = None) -> None:
        """Clean up agent resources."""
        logger.info(f"Cleaning up PydanticAI agent session: {session_id}")
        # No specific cleanup needed for PydanticAI agents
