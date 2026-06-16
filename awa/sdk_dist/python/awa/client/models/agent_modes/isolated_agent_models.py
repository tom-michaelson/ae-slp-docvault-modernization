from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic.json_schema import SkipJsonSchema

from awa.client.models.agent_modes.agent_configuration import AgentConfiguration


class IsolatedAgentParams(BaseModel):
    """Parameters for the isolated agent child workflow."""

    source_directory: str = Field(description="Source directory path (can be Git repo or regular directory)")
    source_branch: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Source branch name (only used for Git repositories in ACT mode)",
    )
    agent_config: AgentConfiguration = Field(description="Agent configuration for execution")
    agent_execution_timeout_minutes: int = Field(
        default=10,
        description="Timeout in minutes for agent execution. Defaults to 10 minutes.",
        gt=0,
    )
    output_directory: str = Field(
        default="awa-agent-output",
        description="Directory name for agent outputs in analyze mode. Defaults to 'awa-agent-output'.",
    )


class IsolatedAgentEnvironmentInfo(BaseModel):
    """Information about an isolated agent environment."""

    environment_path: str = Field(
        description=(
            "Absolute path to the worktree/temporary directory. "
            "Must be an absolute path for reliable file system and git operations."
        ),
    )
    source_directory_path: str = Field(description="Path to the source directory")
    source_branch: str | None = Field(
        description="Source branch name to merge back to (only used for Git repositories in ACT mode)",
    )

    @field_validator("environment_path")
    @classmethod
    def validate_environment_path_is_absolute(cls, v: str) -> str:
        """Validate that environment_path is an absolute path."""
        if not Path(v).is_absolute():
            raise ValueError(f"environment_path must be an absolute path, got: {v}")
        return v


class IsolatedAgentEnvironmentResult(BaseModel):
    """Result of isolated agent environment operations."""

    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Result message or error description")
    environment_info: IsolatedAgentEnvironmentInfo | None = Field(
        default=None,
        description="Environment information if operation was successful",
    )
