from enum import StrEnum

from pydantic import BaseModel, Field

from awa.core.auth import github_copilot
from awa.core.models.config.env_config import EnvConfig


class LlmProviderEnum(StrEnum):
    """Supported LLM providers."""

    OPEN_AI = "OpenAI"
    AZURE_OPEN_AI = "AzureOpenAI"
    AWS_BEDROCK = "AwsBedrock"
    GOOGLE_VERTEX = "GoogleVertex"
    LITE_LLM = "LiteLLM"
    GITHUB_COPILOT = "GithubCopilot"
    ANTHROPIC = "Anthropic"

    @classmethod
    def _missing_(cls, value: str) -> "LlmProviderEnum":
        """Handle alternative formats for enum values when reading from YAML.

        Supports:
        - Case-insensitive matching: "openai", "OPENAI"
        - Underscore variations: "open_ai", "azure_open_ai"
        - Hyphen variations: "azure-openai", "aws-bedrock"
        """
        if isinstance(value, str):
            # Try case-insensitive match
            for member in cls:
                if member.value.lower() == value.lower():
                    return member

            # Try normalized matching (remove underscores, hyphens, and case)
            normalized_value = value.lower().replace("_", "").replace("-", "")
            for member in cls:
                normalized_member = member.value.lower().replace("_", "").replace("-", "")
                if normalized_member == normalized_value:
                    return member

        # Return None to raise ValueError with the original value
        return None


class OpenAiLlmProvider(BaseModel):
    """Configuration for OpenAI-compatible LLM provider."""

    base_url: str | None = Field(
        default=None,
        description="Optional base URL for the OpenAI-compatible API endpoint.",
    )

    @property
    def api_key(self) -> str:
        return EnvConfig.get_env_config().openai_api_key


class AzureOpenAiLlmProvider(BaseModel):
    """Configuration for Azure OpenAI LLM provider."""

    resource_name: str = Field(description="The name of the Azure OpenAI resource.")
    api_version: str = Field(description="The API version to use for the Azure OpenAI resource.")
    domain: str = Field(
        default="openai.azure.com",
        description="Azure domain for the service. Use 'openai.azure.com' for Azure OpenAI Service or "
        "'cognitiveservices.azure.com' for Cognitive Services multi-service.",
    )
    use_entra_auth: bool = Field(
        default=False,
        description="Use Entra ID (DefaultAzureCredential) authentication instead of API key.",
    )

    @property
    def api_key(self) -> str | None:
        """Get API key if not using Entra authentication. Returns None if using Entra auth or if API key is not set."""
        if self.use_entra_auth:
            return None
        return EnvConfig.get_env_config().azure_openai_api_key

    @property
    def azure_endpoint(self) -> str:
        """Get the Azure OpenAI endpoint URL."""
        return f"https://{self.resource_name}.{self.domain}/"


class LiteLlmProvider(BaseModel):
    """Configuration for LiteLLM proxy LLM provider."""

    base_url: str = Field(
        description="The base URL for the LiteLLM proxy API.",
    )

    @property
    def api_key(self) -> str:
        return EnvConfig.get_env_config().lite_llm_api_key


class GoogleVertexLlmProvider(BaseModel):
    """Configuration for Google Vertex AI LLM provider."""

    location: str = Field(
        default="us-central1",
        description="The GCP region/location for Vertex AI (e.g., us-central1).",
    )
    project_id: str | None = Field(
        default=None,
        description="The GCP project ID. If not specified, will use default from GCP authentication.",
    )
    credentials_path: str | None = Field(
        default=None,
        description="Path to service account credentials JSON file. If not specified, "
        "will use default GCP authentication.",
    )

    @property
    def google_application_credentials(self) -> str | None:
        """Get Google Application Credentials from environment or config."""
        if self.credentials_path:
            return self.credentials_path

        return EnvConfig.get_env_config().google_application_credentials


class GithubCopilotLlmProvider(BaseModel):
    """Configuration for GitHub Copilot LLM provider."""

    base_url: str = Field(
        default="https://api.githubcopilot.com",
        description="The base URL for the GitHub Copilot API.",
    )

    @property
    def api_key(self) -> str:
        return self.get_api_key()

    def get_api_key(self) -> str:
        active_token = github_copilot.get_active_token()
        if active_token:
            return active_token
        return EnvConfig.get_env_config().github_copilot_api_key


class AnthropicLlmProvider(BaseModel):
    """Configuration for Anthropic LLM provider."""

    base_url: str | None = Field(
        default=None,
        description="Optional base URL for Anthropic API. If not specified, uses the default Anthropic API endpoint.",
    )

    @property
    def api_key(self) -> str:
        return EnvConfig.get_env_config().anthropic_api_key


class LlmProvidersConfig(BaseModel):
    """Configuration for LLM providers."""

    azure_openai: AzureOpenAiLlmProvider | None = Field(default=None, description="Configuration for Azure OpenAI")
    openai: OpenAiLlmProvider | None = Field(default_factory=OpenAiLlmProvider, description="Configuration for OpenAI")
    google_vertex: GoogleVertexLlmProvider | None = Field(
        default=None,
        description="Configuration for Google Vertex AI",
    )
    lite_llm: LiteLlmProvider | None = Field(default=None, description="Configuration for LiteLLM proxy")
    github_copilot: GithubCopilotLlmProvider | None = Field(
        default=None,
        description="Configuration for GitHub Copilot",
    )
    anthropic: AnthropicLlmProvider | None = Field(
        default=None,
        description="Configuration for Anthropic",
    )
