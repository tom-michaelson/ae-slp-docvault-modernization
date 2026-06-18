"""OpenAI Agent Workflow for executing OpenAI agents with AWA model configuration resolution."""

import json
import time
import uuid
from typing import Any

from agents import Agent, Runner, Tool
from agents.items import ItemHelpers
from temporalio import workflow
from temporalio.contrib.openai_agents.workflow import stateful_mcp_server, stateless_mcp_server

from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder
from awa.core.utils.openai_agents_tool_builder import AgentToolBuilder
from awa.sdk import constants as sdk_constants
from awa.sdk.models.openai_agents import OpenAIAgentConfig, OpenAIAgentResponse, ResponseFormat
from awa.sdk.models.openai_agents.openai_agent_config import AgentToolConfig, HandoffConfig, HandoffEvent


@workflow.defn(name=sdk_constants.WORKFLOW_OPENAI_AGENT)
class OpenAIAgentWorkflow:
    """Workflow for executing OpenAI agents with AWA model configuration resolution.

    This workflow integrates the OpenAI Agents SDK with AWA's configuration system,
    allowing agents to use AWA-configured models (OpenAI, Azure OpenAI, LiteLLM, etc.)
    while supporting MCP servers, structured outputs, and agent handoffs.
    """

    def __init__(self) -> None:
        """Initialize the workflow with handoff tracking."""
        self.handoff_events: list[HandoffEvent] = []
        self.agent_registry: dict[str, Agent] = {}

    @workflow.run
    async def run(self, agent_config: OpenAIAgentConfig) -> OpenAIAgentResponse:
        """Execute an OpenAI agent with AWA model configuration.

        Args:
            agent_config: Configuration for the OpenAI agent execution

        Returns:
            OpenAIAgentResponse with execution results or error information

        """
        # Build the starting agent with handoffs if configured
        starting_agent = self._build_agent_with_tools_and_handoffs(agent_config)

        # Execute the agent using the Runner pattern from temporalio.contrib.openai_agents
        result = await self._run_agent_with_handoffs(
            starting_agent=starting_agent,
            agent_input=agent_config.input,
            agent_config=agent_config,
        )

        return result

    def _create_agent_config(
        self,
        name: str,
        instructions: str,
        model: str,
        mcp_servers: list[str] | None,
        response_format: ResponseFormat,
        response_schema: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create the agent configuration dictionary.

        Note: max_turns is NOT passed here as it's a Runner parameter, not an Agent parameter.
        """
        # Configure response format
        agent_instructions = instructions
        if response_format == ResponseFormat.JSON_SCHEMA and response_schema:
            # Add schema validation instructions to the agent's instructions
            schema_str = json.dumps(response_schema, indent=2)
            schema_instruction = f"\n\nYou must respond with JSON that matches this schema:\n{schema_str}"
            agent_instructions = instructions + schema_instruction

        # Create agent configuration
        agent_config_dict = {
            "name": name,
            "instructions": agent_instructions,
            "model": model,
        }

        # Add MCP servers if provided
        mcp_server_instances = self._get_mcp_servers(mcp_servers)
        if mcp_server_instances:
            agent_config_dict["mcp_servers"] = mcp_server_instances

        return agent_config_dict

    def _extract_result_content(self, result: Any) -> str:  # noqa: ANN401
        """Extract content from the agent execution result."""
        # Try to get text from new_items first, then fall back to final_output
        if hasattr(result, "new_items") and result.new_items:
            return ItemHelpers.text_message_outputs(result.new_items)
        if hasattr(result, "final_output"):
            return str(result.final_output) if result.final_output else ""
        return str(result)

    def _get_mcp_servers(self, mcp_servers: list[str] | None) -> list[Any]:
        """Get MCP server instances for the agent.

        MCP (Model Context Protocol) servers provide tools to agents by name.
        The server names must match those configured in the worker's MCP configuration.

        Args:
            mcp_servers: List of MCP server names to configure

        Returns:
            List of MCPServer instances to pass to the Agent constructor

        Raises:
            ValueError: If a requested server name is not found in MCP configuration

        """
        if not mcp_servers:
            return []

        # Load AWA configuration to validate server names
        available_servers = set()

        mcp_server_instances = []
        for server_name in mcp_servers:
            # Validate that the server exists in configuration
            if available_servers and server_name not in available_servers:
                raise ValueError(
                    f"MCP server '{server_name}' not found in configuration. "
                    f"Available servers: {sorted(available_servers)}",
                )

            # Determine server type based on name pattern or default to stateless
            # For now, we'll default to stateless_mcp_server unless the name suggests otherwise
            if server_name.startswith("stateful_") or "_stateful" in server_name:
                # Use stateful MCP server for servers that maintain state
                server = stateful_mcp_server(
                    name=server_name,
                    cache_tools_list=True,  # Cache the tools list for better performance
                )
            else:
                # Use stateless MCP server by default
                server = stateless_mcp_server(
                    name=server_name,
                    cache_tools_list=True,  # Cache the tools list for better performance
                )

            mcp_server_instances.append(server)

        return mcp_server_instances

    def _build_agent_with_tools_and_handoffs(self, agent_config: OpenAIAgentConfig) -> Agent:
        """Build an agent with tools and handoffs recursively configured.

        Args:
            agent_config: Configuration for the agent

        Returns:
            Agent instance with tools and handoffs configured

        """
        # Create the base agent configuration
        agent_config_dict = self._create_agent_config(
            agent_config.name,
            agent_config.instructions,
            agent_config.model,
            agent_config.mcp_servers,
            agent_config.response_format,
            agent_config.response_schema,
        )

        # Build tools list (will contain both regular tools and agent tools)
        tools: list[Tool] = []

        # Process agent_tools if configured
        if agent_config.agent_tools:
            for agent_tool_item in agent_config.agent_tools:
                if isinstance(agent_tool_item, OpenAIAgentConfig):
                    # Build the agent if not in registry
                    if agent_tool_item.name not in self.agent_registry:
                        nested_agent = self._build_agent_with_tools_and_handoffs(agent_tool_item)
                        self.agent_registry[agent_tool_item.name] = nested_agent

                    # Create tool from agent
                    agent_instance = self.agent_registry[agent_tool_item.name]
                    tool = AgentToolBuilder.build_agent_tool(agent_tool_item, agent_instance)
                    tools.append(tool)

                elif isinstance(agent_tool_item, AgentToolConfig):
                    # Resolve target agent (always OpenAIAgentConfig)
                    target = agent_tool_item.target_agent
                    if target.name not in self.agent_registry:
                        nested_agent = self._build_agent_with_tools_and_handoffs(target)
                        self.agent_registry[target.name] = nested_agent
                    agent_instance = self.agent_registry[target.name]

                    # Create tool from agent
                    tool = AgentToolBuilder.build_agent_tool(agent_tool_item, agent_instance)
                    tools.append(tool)

        # Add tools to configuration if any
        if tools:
            agent_config_dict["tools"] = tools

        # Build handoffs if configured
        handoffs = []
        if agent_config.handoffs:
            # Build each handoff individually with explicit isolation
            for _idx, handoff_item in enumerate(agent_config.handoffs):
                if isinstance(handoff_item, HandoffConfig):
                    # Resolve the target agent
                    target = handoff_item.target_agent

                    # Build or retrieve the agent with explicit assignment
                    if isinstance(target, OpenAIAgentConfig):
                        if target.name not in self.agent_registry:
                            nested_agent = self._build_agent_with_tools_and_handoffs(target)
                            self.agent_registry[target.name] = nested_agent

                        # CRITICAL: Create explicit local reference to avoid any closure issues
                        specific_agent = self.agent_registry[target.name]

                        # Create handoff immediately with the explicit agent reference
                        # This ensures each handoff captures the correct agent
                        handoff_obj = HandoffBuilder.build_handoff(handoff_item, specific_agent)
                        handoffs.append(handoff_obj)

                    elif isinstance(target, str):
                        raise TypeError(
                            f"String references not supported for handoffs. "
                            f"Use OpenAIAgentConfig or Agent instances. "
                            f"Got string: '{target}'",
                        )
                    else:
                        # Direct agent reference
                        handoff_obj = HandoffBuilder.build_handoff(handoff_item, target)
                        handoffs.append(handoff_obj)

                elif isinstance(handoff_item, str):
                    # Simple string reference
                    handoffs.append(self.agent_registry.get(handoff_item, handoff_item))

                elif isinstance(handoff_item, OpenAIAgentConfig):
                    # Direct OpenAIAgentConfig
                    if handoff_item.name not in self.agent_registry:
                        nested_agent = self._build_agent_with_tools_and_handoffs(handoff_item)
                        self.agent_registry[handoff_item.name] = nested_agent
                    handoffs.append(self.agent_registry[handoff_item.name])

        # Add handoffs to agent configuration
        if handoffs:
            agent_config_dict["handoffs"] = handoffs

        # Create the agent
        agent = Agent(**agent_config_dict)

        # Register the agent
        self.agent_registry[agent_config.name] = agent

        return agent

    def _resolve_target_agent(self, target: str | OpenAIAgentConfig) -> Agent | str:
        """Resolve a target agent reference to an agent instance or name.

        Args:
            target: Agent name string or OpenAIAgentConfig

        Returns:
            Agent instance if found in registry, otherwise the target string/config

        """
        if isinstance(target, str):
            # Check if we have this agent in our registry
            return self.agent_registry.get(target, target)
        if isinstance(target, OpenAIAgentConfig):
            # Build the nested agent if not already built
            if target.name not in self.agent_registry:
                nested_agent = self._build_agent_with_tools_and_handoffs(target)
                self.agent_registry[target.name] = nested_agent
            return self.agent_registry[target.name]
        return target

    def _track_handoff(
        self,
        from_agent: str,
        to_agent: str,
        input_data: dict[str, Any] | None = None,
        tools_removed: bool = False,
    ) -> None:
        """Track a handoff event.

        Args:
            from_agent: Name of the agent handing off control
            to_agent: Name of the agent receiving control
            input_data: Optional data passed during the handoff
            tools_removed: Whether tools were removed from conversation history

        """
        event = HandoffEvent(
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=time.time(),
            input_data=input_data,
            tools_removed=tools_removed,
        )
        self.handoff_events.append(event)

    async def _run_agent_with_handoffs(
        self,
        starting_agent: Agent,
        agent_input: str,
        agent_config: OpenAIAgentConfig,
    ) -> OpenAIAgentResponse:
        """Run the OpenAI agent using the Temporal Runner pattern with handoff support.

        Args:
            starting_agent: The agent to start execution with (may have handoffs configured)
            agent_input: Input for the agent
            agent_config: Full agent configuration

        Returns:
            OpenAIAgentResponse with execution results and handoff tracking

        """
        start_time = time.time()
        execution_id = str(uuid.uuid4())

        # Build Runner.run() arguments
        runner_args = {
            "starting_agent": starting_agent,
            "input": agent_input,
        }

        # Add max_turns if specified in config
        if agent_config.max_turns is not None:
            runner_args["max_turns"] = agent_config.max_turns

        # Run the agent with handoff support
        result = await Runner.run(**runner_args)

        # Extract content from result
        content = self._extract_result_content(result)

        # Determine final agent name
        final_agent = None
        if self.handoff_events:
            final_agent = self.handoff_events[-1].to_agent

        return OpenAIAgentResponse(
            content=content,
            execution_id=execution_id,
            agent_name=agent_config.name,
            model_used=agent_config.model,
            execution_time_seconds=time.time() - start_time,
            metadata=agent_config.metadata,
            handoff_events=self.handoff_events if self.handoff_events else None,
            final_agent=final_agent,
        )
