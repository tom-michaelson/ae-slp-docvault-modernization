from typing import Literal

from pydantic import BaseModel, Field, model_validator

from awa.core.models.config.llm_providers_config import LlmProviderEnum


class ModelConfig(BaseModel):
    """Configuration for an individual LLM model."""

    name: str = Field(
        description=(
            "User-defined model name. Used to refer to this model when executing LLM calls, or from `default_model`"
        ),
    )
    provider: LlmProviderEnum = Field(description="LLM provider")
    model: str = Field(description="LLM model name. Must match format expected by the specific `provider`")
    temperature: float = Field(default=0.0, description="Temperature, passed through to the LLM call")
    max_tokens: int | None = Field(
        default=None,
        description="Max tokens, passed through to the LLM call (legacy parameter)",
    )
    max_completion_tokens: int | None = Field(
        default=None,
        description="Max completion tokens for Chat Completions API (GPT-5 reasoning models)",
    )
    max_output_tokens: int | None = Field(
        default=None,
        description="Max output tokens for Responses API (GPT-5 models)",
    )
    reasoning_effort: int | str | None = Field(
        default=None,
        description="Reasoning effort. For GPT-5: 'minimal', 'low', 'medium', 'high'. For GPT-4: integer or string.",
    )
    use_cache: bool | None = Field(
        default=None,
        description=(
            "Whether to use the cache. If cache is used and a cached value is found, the LLM call will not be made."
        ),
    )
    # Azure OpenAI specific fields
    resource_name: str | None = Field(
        default=None,
        description="Azure OpenAI resource name (for azureopenai provider)",
    )
    api_version: str | None = Field(
        default=None,
        description="Azure OpenAI API version (for azureopenai provider)",
    )
    domain: str | None = Field(
        default=None,
        description="Azure domain for the service (for azureopenai provider). Use 'openai.azure.com' for Azure OpenAI"
        " Service or 'cognitiveservices.azure.com' for Cognitive Services multi-service. If not specified, falls back"
        "to provider-level domain.",
    )
    # GPT-5 specific fields
    is_gpt5_model: bool = Field(
        default=False,
        description="Whether this is a GPT-5 model. Enables GPT-5 specific parameters and features.",
    )
    use_responses_api: bool = Field(
        default=False,
        description="Whether to use the Responses API endpoint instead of Chat Completions API.",
    )
    verbosity: Literal["low", "medium", "high"] | None = Field(
        default=None,
        description="GPT-5 verbosity level. Controls output length and detail. Only applies to GPT-5 models.",
    )

    @model_validator(mode="after")
    def validate_gpt5_parameters(self) -> "ModelConfig":
        """Validate GPT-5 specific parameter combinations.

        Ensures correct token parameters are used with the appropriate API endpoint,
        and warns about parameters that will be ignored.
        """
        if not self.is_gpt5_model:
            return self

        # Validate token parameters based on API endpoint
        if self.use_responses_api:
            # Responses API should use max_output_tokens, not max_completion_tokens
            if self.max_completion_tokens is not None:
                raise ValueError(
                    f"Model '{self.name}': GPT-5 with Responses API (use_responses_api=true) requires "
                    "'max_output_tokens', not 'max_completion_tokens'. "
                    "Please set 'max_output_tokens' instead.",
                )
            if self.max_tokens is not None:
                raise ValueError(
                    f"Model '{self.name}': GPT-5 does not support 'max_tokens'. "
                    "Use 'max_output_tokens' with Responses API.",
                )
        else:
            # Chat Completions API should use max_completion_tokens, not max_output_tokens
            if self.max_output_tokens is not None:
                raise ValueError(
                    f"Model '{self.name}': GPT-5 with Chat Completions API (use_responses_api=false) requires "
                    "'max_completion_tokens', not 'max_output_tokens'. "
                    "Please set 'max_completion_tokens' instead.",
                )
            if self.max_tokens is not None:
                raise ValueError(
                    f"Model '{self.name}': GPT-5 does not support 'max_tokens'. "
                    "Use 'max_completion_tokens' with Chat Completions API.",
                )

        return self
