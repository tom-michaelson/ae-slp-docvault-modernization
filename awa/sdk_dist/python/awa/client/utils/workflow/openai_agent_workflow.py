"""Utility function for executing OpenAI Agent workflows."""

from temporalio import workflow

from awa.client import constants
from awa.client.models.openai_agents import OpenAIAgentConfig, OpenAIAgentResponse


async def openai_agent_workflow(
    config: OpenAIAgentConfig,
    workflow_id: str | None = None,
) -> OpenAIAgentResponse:
    """Execute an OpenAI agent with the specified configuration.

    This workflow integrates the OpenAI Agents SDK with AWA's configuration system,
    allowing agents to use AWA-configured models (OpenAI, Azure OpenAI, LiteLLM, etc.)
    while supporting MCP servers, structured outputs, and agent handoffs.

    Args:
        config: Configuration for the OpenAI agent execution including:
            - name: Agent name
            - instructions: System instructions for the agent
            - model: Model to use (e.g., "gpt-4", configured via AWA)
            - input: User input/prompt for the agent
            - mcp_servers: Optional list of MCP server names
            - agent_tools: Optional list of agent tools/nested agents
            - handoffs: Optional list of agent handoffs
            - response_format: Optional response format (text/json_schema)
            - response_schema: Optional JSON schema for structured outputs
            - metadata: Optional metadata dict
        workflow_id: Optional workflow ID for the child workflow.
            If not provided, a default ID will be generated.

    Returns:
        OpenAIAgentResponse: The result of the agent execution including:
            - content: The agent's response content
            - execution_id: Unique execution identifier
            - agent_name: Name of the agent that executed
            - model_used: The model that was used
            - execution_time_seconds: Time taken for execution
            - metadata: Optional metadata from the config
            - handoff_events: List of handoff events if handoffs occurred
            - final_agent: Name of the final agent if handoffs occurred

    Example:
        >>> from awa.client.models.openai_agents import OpenAIAgentConfig
        >>> from awa.client.utils.workflow import openai_agent_workflow
        >>>
        >>> config = OpenAIAgentConfig(
        ...     name="research-agent",
        ...     instructions="You are a helpful research assistant.",
        ...     model="gpt-4",
        ...     input="What are the benefits of Temporal workflows?",
        ...     mcp_servers=["wikipedia", "arxiv"]
        ... )
        >>> response = await openai_agent_workflow(config)
        >>> print(response.content)

    """
    return OpenAIAgentResponse.model_validate(
        await workflow.execute_child_workflow(
            workflow=constants.WORKFLOW_OPENAI_AGENT,
            arg=config,
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            id=workflow_id or f"openai-agent-{config.name}-{workflow.info().workflow_id}",
        ),
    )
