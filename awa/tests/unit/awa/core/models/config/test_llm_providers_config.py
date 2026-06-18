from unittest.mock import Mock, patch

import pytest

from awa.core.models.config.llm_providers_config import (
    AnthropicLlmProvider,
    AzureOpenAiLlmProvider,
    LlmProviderEnum,
    LlmProvidersConfig,
    OpenAiLlmProvider,
)


class TestLlmProviderEnum:
    """Test cases for LlmProviderEnum enum variations support."""

    def test_exact_enum_values(self) -> None:
        """Test that exact enum values work correctly."""
        assert LlmProviderEnum("OpenAI") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("AzureOpenAI") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("AwsBedrock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("GoogleVertex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("LiteLLM") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("Anthropic") == LlmProviderEnum.ANTHROPIC

    def test_case_insensitive_matching(self) -> None:
        """Test case-insensitive matching for enum values."""
        # Lowercase variations
        assert LlmProviderEnum("openai") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("azureopenai") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("awsbedrock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("googlevertex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("litellm") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("anthropic") == LlmProviderEnum.ANTHROPIC

        # Uppercase variations
        assert LlmProviderEnum("OPENAI") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("AZUREOPENAI") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("AWSBEDROCK") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("GOOGLEVERTEX") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("LITELLM") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("ANTHROPIC") == LlmProviderEnum.ANTHROPIC

        # Mixed case variations
        assert LlmProviderEnum("OpenAi") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("AzureOpenAi") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("AwsBedRock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("GoogleVertex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("LiteLlm") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("Anthropic") == LlmProviderEnum.ANTHROPIC

    def test_underscore_variations(self) -> None:
        """Test underscore variations for enum values."""
        assert LlmProviderEnum("open_ai") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("azure_open_ai") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("aws_bedrock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("google_vertex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("lite_llm") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("anthropic") == LlmProviderEnum.ANTHROPIC

        # Mixed case with underscores
        assert LlmProviderEnum("Open_AI") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("Azure_Open_AI") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("AWS_BEDROCK") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("Google_Vertex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("Lite_LLM") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("Anthropic") == LlmProviderEnum.ANTHROPIC

    def test_hyphen_variations(self) -> None:
        """Test hyphen variations for enum values."""
        assert LlmProviderEnum("open-ai") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("azure-openai") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("aws-bedrock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("google-vertex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("lite-llm") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("anthropic") == LlmProviderEnum.ANTHROPIC

        # Mixed case with hyphens
        assert LlmProviderEnum("Open-AI") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("Azure-OpenAI") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("AWS-Bedrock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("Google-Vertex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("Lite-LLM") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("Anthropic") == LlmProviderEnum.ANTHROPIC

    def test_mixed_separator_variations(self) -> None:
        """Test combinations of different separators and cases."""
        assert LlmProviderEnum("open_ai") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("azure-open_ai") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("aws_bed-rock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("google-ver_tex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("lite-l_l_m") == LlmProviderEnum.LITE_LLM

        # Complex mixed variations
        assert LlmProviderEnum("OPEN_ai") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("azure-OpenAI") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("Aws-BedRock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("Google_vertex") == LlmProviderEnum.GOOGLE_VERTEX

    def test_whitespace_handling(self) -> None:
        """Test that whitespace in enum values is not supported (should raise ValueError)."""
        with pytest.raises(ValueError):
            LlmProviderEnum("open ai")

        with pytest.raises(ValueError):
            LlmProviderEnum("azure open ai")

        with pytest.raises(ValueError):
            LlmProviderEnum(" openai")

        with pytest.raises(ValueError):
            LlmProviderEnum("openai ")

    def test_invalid_values(self) -> None:
        """Test that invalid enum values raise ValueError."""
        with pytest.raises(ValueError):
            LlmProviderEnum("invalid_provider")

        with pytest.raises(ValueError):
            LlmProviderEnum("vertex")

        with pytest.raises(ValueError):
            LlmProviderEnum("invalid_anthropic_provider")

        with pytest.raises(ValueError):
            LlmProviderEnum("")

        with pytest.raises(ValueError):
            LlmProviderEnum("123")

    def test_non_string_values(self) -> None:
        """Test that non-string values raise appropriate errors."""
        with pytest.raises((ValueError, TypeError)):
            LlmProviderEnum(123)

        with pytest.raises((ValueError, TypeError)):
            LlmProviderEnum(None)

        with pytest.raises((ValueError, TypeError)):
            LlmProviderEnum([])

    def test_common_yaml_variations(self) -> None:
        """Test common variations that might appear in YAML configuration files."""
        # Common lowercase variations
        assert LlmProviderEnum("openai") == LlmProviderEnum.OPEN_AI
        assert LlmProviderEnum("azure_openai") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("awsbedrock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("googlevertex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("litellm") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("anthropic") == LlmProviderEnum.ANTHROPIC

        # Underscore and hyphen variations
        assert LlmProviderEnum("aws_bedrock") == LlmProviderEnum.AWS_BEDROCK
        assert LlmProviderEnum("google_vertex") == LlmProviderEnum.GOOGLE_VERTEX
        assert LlmProviderEnum("lite_llm") == LlmProviderEnum.LITE_LLM
        assert LlmProviderEnum("anthropic") == LlmProviderEnum.ANTHROPIC
        assert LlmProviderEnum("azure-openai") == LlmProviderEnum.AZURE_OPEN_AI
        assert LlmProviderEnum("google-vertex") == LlmProviderEnum.GOOGLE_VERTEX

    def test_enum_string_representation(self) -> None:
        """Test that enum members return their proper string values."""
        assert str(LlmProviderEnum.OPEN_AI) == "OpenAI"
        assert str(LlmProviderEnum.AZURE_OPEN_AI) == "AzureOpenAI"
        assert str(LlmProviderEnum.AWS_BEDROCK) == "AwsBedrock"
        assert str(LlmProviderEnum.GOOGLE_VERTEX) == "GoogleVertex"
        assert str(LlmProviderEnum.LITE_LLM) == "LiteLLM"
        assert str(LlmProviderEnum.ANTHROPIC) == "Anthropic"

    def test_enum_value_property(self) -> None:
        """Test that enum members have the correct value property."""
        assert LlmProviderEnum.OPEN_AI.value == "OpenAI"
        assert LlmProviderEnum.AZURE_OPEN_AI.value == "AzureOpenAI"
        assert LlmProviderEnum.AWS_BEDROCK.value == "AwsBedrock"
        assert LlmProviderEnum.GOOGLE_VERTEX.value == "GoogleVertex"
        assert LlmProviderEnum.LITE_LLM.value == "LiteLLM"
        assert LlmProviderEnum.ANTHROPIC.value == "Anthropic"

    def test_all_enum_members_accessible(self) -> None:
        """Test that all enum members are accessible and correct."""
        expected_members = {
            "OPEN_AI": "OpenAI",
            "AZURE_OPEN_AI": "AzureOpenAI",
            "AWS_BEDROCK": "AwsBedrock",
            "GOOGLE_VERTEX": "GoogleVertex",
            "LITE_LLM": "LiteLLM",
            "ANTHROPIC": "Anthropic",
            "GITHUB_COPILOT": "GithubCopilot",
        }

        for member_name, member_value in expected_members.items():
            enum_member = getattr(LlmProviderEnum, member_name)
            assert enum_member.value == member_value
            assert str(enum_member) == member_value


class TestOpenAiLlmProvider:
    """Test cases for OpenAiLlmProvider configuration."""

    def test_default_openai_provider(self) -> None:
        """OpenAI provider defaults should be unset."""
        provider = OpenAiLlmProvider()
        assert provider.base_url is None

    def test_openai_provider_with_base_url(self) -> None:
        """OpenAI provider stores custom base URL."""
        provider = OpenAiLlmProvider(base_url="https://example.databricks")
        assert provider.base_url == "https://example.databricks"

    @patch("awa.core.models.config.llm_providers_config.EnvConfig.get_env_config")
    def test_openai_provider_api_key(self, mock_get_env_config: Mock) -> None:
        """API key is sourced from the standard OPENAI_API_KEY setting."""
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-openai-key"
        mock_get_env_config.return_value = mock_settings

        provider = OpenAiLlmProvider()

        assert provider.api_key == "test-openai-key"
        mock_get_env_config.assert_called_once()


class TestAnthropicLlmProvider:
    """Test cases for AnthropicLlmProvider configuration."""

    def test_default_anthropic_provider(self) -> None:
        """Test AnthropicLlmProvider with default values."""
        # Act
        provider = AnthropicLlmProvider()

        # Assert
        assert provider.base_url is None

    def test_anthropic_provider_with_base_url(self) -> None:
        """Test AnthropicLlmProvider with custom base URL."""
        # Arrange
        custom_base_url = "https://custom.anthropic.api"

        # Act
        provider = AnthropicLlmProvider(base_url=custom_base_url)

        # Assert
        assert provider.base_url == custom_base_url

    @patch("awa.core.models.config.llm_providers_config.EnvConfig.get_env_config")
    def test_anthropic_provider_api_key(self, mock_get_env_config: Mock) -> None:
        """Test AnthropicLlmProvider API key property."""
        # Arrange
        mock_env_config = Mock()
        mock_env_config.anthropic_api_key = "test-anthropic-key"
        mock_get_env_config.return_value = mock_env_config

        provider = AnthropicLlmProvider()

        # Act
        api_key = provider.api_key

        # Assert
        assert api_key == "test-anthropic-key"
        mock_get_env_config.assert_called_once()

    def test_anthropic_provider_in_llm_providers_config(self) -> None:
        """Test AnthropicLlmProvider integration in LlmProvidersConfig."""
        # Arrange
        anthropic_config = AnthropicLlmProvider(base_url="https://custom.api")

        # Act
        config = LlmProvidersConfig(anthropic=anthropic_config)

        # Assert
        assert config.anthropic is not None
        assert config.anthropic.base_url == "https://custom.api"

    def test_anthropic_provider_none_in_llm_providers_config(self) -> None:
        """Test LlmProvidersConfig with None anthropic provider."""
        # Act
        config = LlmProvidersConfig()

        # Assert
        assert config.anthropic is None


class TestAzureOpenAiLlmProvider:
    """Test cases for AzureOpenAiLlmProvider configuration."""

    @patch("awa.core.models.config.llm_providers_config.EnvConfig.get_env_config")
    def test_default_azure_openai_provider(self, mock_get_env_config: Mock) -> None:
        """Test AzureOpenAiLlmProvider with default values and no API key."""
        # Arrange - Mock empty API key
        mock_env_config = Mock()
        mock_env_config.azure_openai_api_key = ""  # Empty API key
        mock_get_env_config.return_value = mock_env_config

        # Act - Should create provider successfully (no validation at config time)
        provider = AzureOpenAiLlmProvider(resource_name="test-resource", api_version="2024-10-21")

        # Assert
        assert provider.resource_name == "test-resource"
        assert provider.api_version == "2024-10-21"
        assert provider.use_entra_auth is False
        assert provider.api_key == ""  # Empty string from env config

    def test_azure_openai_provider_with_entra_auth(self) -> None:
        """Test AzureOpenAiLlmProvider with Entra authentication."""
        # Act
        provider = AzureOpenAiLlmProvider(resource_name="test-resource", api_version="2024-10-21", use_entra_auth=True)

        # Assert
        assert provider.resource_name == "test-resource"
        assert provider.api_version == "2024-10-21"
        assert provider.use_entra_auth is True
        assert provider.api_key is None

    @patch("awa.core.models.config.llm_providers_config.EnvConfig.get_env_config")
    def test_azure_openai_provider_with_api_key(self, mock_get_env_config: Mock) -> None:
        """Test AzureOpenAiLlmProvider with API key authentication."""
        # Arrange
        mock_env_config = Mock()
        mock_env_config.azure_openai_api_key = "test-azure-key"
        mock_get_env_config.return_value = mock_env_config

        # Act
        provider = AzureOpenAiLlmProvider(resource_name="test-resource", api_version="2024-10-21", use_entra_auth=False)

        # Assert
        assert provider.resource_name == "test-resource"
        assert provider.api_version == "2024-10-21"
        assert provider.use_entra_auth is False
        assert provider.api_key == "test-azure-key"

    @patch("awa.core.models.config.llm_providers_config.EnvConfig.get_env_config")
    def test_azure_openai_provider_no_api_key_with_key_auth(self, mock_get_env_config: Mock) -> None:
        """Test AzureOpenAiLlmProvider allows creation when API key is missing and use_entra_auth=False."""
        # Arrange
        mock_env_config = Mock()
        mock_env_config.azure_openai_api_key = ""  # Empty API key
        mock_get_env_config.return_value = mock_env_config

        # Act - Should create provider successfully (validation moved to runtime)
        provider = AzureOpenAiLlmProvider(resource_name="test-resource", api_version="2024-10-21", use_entra_auth=False)

        # Assert
        assert provider.resource_name == "test-resource"
        assert provider.api_version == "2024-10-21"
        assert provider.use_entra_auth is False
        assert provider.api_key == ""  # Empty string from env config

    @patch("awa.core.models.config.llm_providers_config.EnvConfig.get_env_config")
    def test_azure_openai_provider_default_use_entra_auth_false(self, mock_get_env_config: Mock) -> None:
        """Test AzureOpenAiLlmProvider defaults to use_entra_auth=False."""
        # Arrange
        mock_env_config = Mock()
        mock_env_config.azure_openai_api_key = "test-key"
        mock_get_env_config.return_value = mock_env_config

        # Act
        provider = AzureOpenAiLlmProvider(resource_name="test-resource", api_version="2024-10-21")

        # Assert
        assert provider.use_entra_auth is False
        assert provider.api_key == "test-key"

    def test_azure_openai_provider_in_llm_providers_config(self) -> None:
        """Test AzureOpenAiLlmProvider integration in LlmProvidersConfig."""
        # Arrange
        azure_config = AzureOpenAiLlmProvider(
            resource_name="test-resource",
            api_version="2024-10-21",
            use_entra_auth=True,
        )

        # Act
        config = LlmProvidersConfig(azure_openai=azure_config)

        # Assert
        assert config.azure_openai is not None
        assert config.azure_openai.resource_name == "test-resource"
        assert config.azure_openai.api_version == "2024-10-21"
        assert config.azure_openai.use_entra_auth is True

    def test_azure_openai_provider_default_domain(self) -> None:
        """Test AzureOpenAiLlmProvider uses default domain."""
        # Act
        provider = AzureOpenAiLlmProvider(
            resource_name="test-resource",
            api_version="2024-10-21",
            use_entra_auth=True,
        )

        # Assert
        assert provider.domain == "openai.azure.com"
        assert provider.azure_endpoint == "https://test-resource.openai.azure.com/"

    def test_azure_openai_provider_custom_domain(self) -> None:
        """Test AzureOpenAiLlmProvider with custom domain."""
        # Act
        provider = AzureOpenAiLlmProvider(
            resource_name="ai-skylercarlson5076ai534536736521",
            api_version="2024-10-21",
            domain="cognitiveservices.azure.com",
            use_entra_auth=True,
        )

        # Assert
        assert provider.domain == "cognitiveservices.azure.com"
        assert provider.azure_endpoint == "https://ai-skylercarlson5076ai534536736521.cognitiveservices.azure.com/"
