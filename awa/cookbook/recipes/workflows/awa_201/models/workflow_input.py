from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic.json_schema import SkipJsonSchema
from pydantic_core.core_schema import ValidationInfo


class Awa201WorkflowInput(BaseModel):
    target_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Path to the local directory to analyze. Mutually exclusive with git_url.",
    )
    git_url: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Git repository URL to clone and analyze. Mutually exclusive with target_dir.",
    )
    git_branch: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Optional git branch to checkout. Only used with git_url.",
    )
    agent_provider: str = "claude"
    max_content_length: int = 100000  # ~25k tokens, triggers chunking if exceeded
    max_chunk_length: int = 40000  # ~10k tokens per chunk
    publish_command: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Optional shell command to publish the generated documentation site",
    )

    @field_validator("target_dir", "git_url")
    @classmethod
    def validate_source(cls, v: str | Path | None, info: ValidationInfo) -> str | Path | None:
        if info.field_name == "target_dir":
            git_url = info.data.get("git_url")
            if v is None and git_url is None:
                raise ValueError("Either target_dir or git_url must be provided")
            if v is not None and git_url is not None:
                raise ValueError("target_dir and git_url are mutually exclusive")
        return v
