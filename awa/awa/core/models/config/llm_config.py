from pydantic import BaseModel, Field, field_validator

from awa.core.models.config.llm_behavior_config import LlmBehaviorConfig
from awa.core.models.config.llm_providers_config import LlmProvidersConfig
from awa.core.models.config.model_config import ModelConfig


class LLMConfig(BaseModel):
    """Configuration for LLM settings."""

    default_model: str = Field(
        description="Default model name to use for LLM calls. Must match name in the `models` configuration.",
    )
    providers: LlmProvidersConfig = Field(
        default_factory=LlmProvidersConfig,
        description="LLM providers configuration",
    )
    models: list[ModelConfig] = Field(description="LLM models configuration")
    embedding_models: list[ModelConfig] | None = Field(
        default=None,
        description="Embedding models configuration",
    )
    behavior: LlmBehaviorConfig = Field(
        default_factory=LlmBehaviorConfig,
        description="LLM call behavior configurations",
    )

    @field_validator("providers", mode="before")
    @classmethod
    def ensure_providers_object(cls, v: LlmProvidersConfig | None) -> LlmProvidersConfig:
        """Ensure providers is always a LlmProvidersConfig object, even if null is passed."""
        if v is None:
            return LlmProvidersConfig()
        return v
