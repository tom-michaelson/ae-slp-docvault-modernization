from pydantic import BaseModel, Field

from awa.core.models.config.retry_on_parse_error_config import RetryOnParseErrorConfig


class LlmBehaviorConfig(BaseModel):
    use_cache: bool = Field(
        default=True,
        description=(
            "Whether to use the cache globally. If cache is used and a cached value is found, "
            "the LLM call will not be made. Can be overridden from `llm.models[*].use_cache`"
        ),
    )
    auto_retry_parse: RetryOnParseErrorConfig = Field(
        default_factory=RetryOnParseErrorConfig,
        description="Auto retry configuration",
    )
