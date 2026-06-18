from pydantic import BaseModel, Field


class RetryOnParseErrorConfig(BaseModel):
    """Settings for retrying LLM calls when a BAML parsing error occurs."""

    enabled: bool = Field(
        default=True,
        description=(
            "Whether to enable auto retry on parse error. If true, the LLM call will be retried "
            "up to `max_attempts` times."
        ),
    )
    max_attempts: int = Field(
        default=3,
        description="Maximum number of attempts to retry the LLM call.",
    )
    temperature_increment: float = Field(
        default=0.1,
        description="Temperature increment to use for each retry.",
    )
