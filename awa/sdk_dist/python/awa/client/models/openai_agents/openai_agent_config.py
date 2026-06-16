from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from .enums import ResponseFormat


class AgentToolConfig(BaseModel):
    """Configuration for using an agent as a tool."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    target_agent: OpenAIAgentConfig = Field(
        ...,
        description="The agent to expose as a tool. Must be an OpenAIAgentConfig instance.",
    )

    tool_name_override: str | None = Field(
        None,
        description="Override the tool name. If not provided, uses the agent's name.",
    )

    tool_description_override: str | None = Field(
        None,
        description="Override the tool description. If not provided, uses the agent's description.",
    )

    is_enabled: bool = Field(
        default=True,
        description="Whether this agent tool is enabled.",
    )


class HandoffEvent(BaseModel):
    """Event representing a handoff between agents."""

    from_agent: str = Field(..., description="Name of the agent handing off control")
    to_agent: str = Field(..., description="Name of the agent receiving control")
    timestamp: float = Field(..., description="Unix timestamp when the handoff occurred")
    input_data: dict[str, Any] | None = Field(None, description="Data passed during the handoff")
    tools_removed: bool = Field(default=False, description="Whether tools were removed from conversation history")


class HandoffConfig(BaseModel):
    """Configuration for agent handoffs in the OpenAI agent system.

    This class defines how one agent can hand off control to another agent,
    including tool configuration, metadata, and execution parameters.
    """

    target_agent: str | OpenAIAgentConfig = Field(
        ...,
        description="The target agent to hand off to. Can be an agent name (str) or an OpenAIAgentConfig instance.",
    )

    tool_name_override: str | None = Field(
        None,
        description="Override the default tool name for this handoff. If not provided, uses the target agent's name.",
    )

    tool_description_override: str | None = Field(
        None,
        description=(
            "Override the default tool description for this handoff. "
            "If not provided, uses the target agent's description."
        ),
    )

    remove_tools_from_history: bool = Field(
        default=False,
        description="Whether to remove handoff tools from the conversation history when executing the handoff.",
    )

    is_enabled: bool = Field(
        default=True,
        description="Whether this handoff configuration is enabled. Disabled handoffs will not be available as tools.",
    )

    input_type: dict[str, Any] | None = Field(
        default=None,
        description=(
            "JSON Schema defining the expected structure of input data when handing off to the target agent. "
            "This schema is used to validate the data passed during handoff execution. "
            "If provided, the schema must include at least a 'type' field."
        ),
    )

    @field_validator("input_type")
    @classmethod
    def validate_input_type(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Ensure input_type follows JSON Schema format when provided."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("input_type must be a dictionary")
            if "type" not in v:
                raise ValueError("input_type must include a 'type' field to be a valid JSON Schema")
        return v

    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "target_agent": "data_analyst",
                "tool_name_override": "analyze_data",
                "tool_description_override": "Hand off to data analyst for comprehensive data analysis",
                "remove_tools_from_history": False,
                "is_enabled": True,
                "input_type": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    },
                    "required": ["query"],
                },
            },
        },
    }


class OpenAIAgentConfig(BaseModel):
    """Main configuration for OpenAI Agent execution in Temporal workflow."""

    model_config = ConfigDict(defer_build=True)

    # Core agent configuration
    name: str = Field(..., description="Name of the agent", min_length=1)
    instructions: str = Field(..., description="System instructions for the agent", min_length=1)
    input: str = Field(..., description="Input for the agent", min_length=1)

    # Model configuration - just a string reference to AWA config
    model: str = Field(
        ...,
        description="Name of model. Must be valid default LiteLLM model name.",
        min_length=1,
    )

    # MCP server configuration
    mcp_servers: list[str] | None = Field(
        default=None,
        description="List of MCP server names that match keys in the mcp.json servers object",
    )

    # Response configuration
    response_format: ResponseFormat = Field(
        default=ResponseFormat.TEXT,
        description="Response format: text or JSON schema",
    )
    response_schema: dict[str, Any] | None = Field(
        default=None,
        description="JSON schema for structured output (only used when response_format is JSON_SCHEMA)",
    )

    # Temporal-specific configuration
    workflow_id: str | None = Field(
        default=None,
        description="Optional workflow ID for tracking",
    )

    # Additional metadata
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata for the agent execution",
    )

    # Agent execution configuration
    max_turns: int | None = Field(
        default=None,
        description="Maximum number of turns for the agent execution. Defaults to 10 if not specified.",
    )

    # Agent tools configuration
    agent_tools: list[OpenAIAgentConfig | AgentToolConfig] | None = Field(
        default=None,
        description="List of agents to use as tools. These agents can be called as tools and return results.",
    )

    # Handoff configuration
    handoffs: list[str | HandoffConfig | OpenAIAgentConfig] | None = Field(
        default=None,
        description="List of possible handoff targets. Can be agent names, HandoffConfig objects, or OpenAIAgentConfig instances.",  # noqa: E501
    )
    handoff_description: str | None = Field(
        default=None,
        description="Description of how this agent handles handoffs or what types of handoffs it supports.",
    )

    @field_validator("response_schema")
    @classmethod
    def validate_response_schema(cls, v: dict[str, Any] | None, info: ValidationInfo) -> dict[str, Any] | None:
        """Ensure response_schema is only set when response_format is JSON_SCHEMA."""
        if v is not None and info.data.get("response_format") != ResponseFormat.JSON_SCHEMA:
            raise ValueError("response_schema can only be set when response_format is JSON_SCHEMA")
        return v


class OpenAIAgentResponse(BaseModel):
    """Response model for OpenAI Agent execution."""

    # Core response data
    content: str = Field(..., description="The agent's response content")

    # Execution metadata
    execution_id: str = Field(..., description="Unique execution ID")
    agent_name: str = Field(..., description="Name of the agent that executed")
    model_used: str = Field(..., description="Model that was used")

    # Performance metrics
    execution_time_seconds: float = Field(..., description="Total execution time")

    # Error information (if any)
    error: str | None = Field(default=None, description="Error message if execution failed")
    error_type: str | None = Field(default=None, description="Type of error if occurred")

    # Additional metadata
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata from the execution",
    )

    # Handoff tracking
    handoff_events: list[HandoffEvent] | None = Field(
        default=None,
        description="List of handoff events that occurred during execution",
    )
    final_agent: str | None = Field(
        default=None,
        description="Name of the final agent that completed the execution if handoffs occurred",
    )


# Rebuild the model to handle forward references
OpenAIAgentConfig.model_rebuild()
AgentToolConfig.model_rebuild()
