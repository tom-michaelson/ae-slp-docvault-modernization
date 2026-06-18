import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from baml_py import Collector
from baml_py.errors import BamlClientFinishReasonError, BamlClientHttpError, BamlValidationError
from pydantic import BaseModel

from awa.core.models.config.app_config import AppConfig
from awa.core.models.config.llm_behavior_config import LlmBehaviorConfig
from awa.core.models.config.llm_config import LLMConfig
from awa.core.models.config.llm_providers_config import (
    AnthropicLlmProvider,
    AzureOpenAiLlmProvider,
    GoogleVertexLlmProvider,
    LiteLlmProvider,
    LlmProviderEnum,
    LlmProvidersConfig,
    OpenAiLlmProvider,
)
from awa.core.models.config.model_config import ModelConfig
from awa.core.models.config.retry_on_parse_error_config import RetryOnParseErrorConfig
from awa.core.utils.llm_invoker import LlmInvoker
from awa.sdk.models.exceptions import AwaLlmAuthError, AwaLlmResponseParsingError

# Constants
TEST_TEMPERATURE = 0.7
TEST_MAX_TOKENS = 1000
AZURE_TEST_TEMPERATURE = 0.5
AZURE_TEST_MAX_TOKENS = 2000
BEDROCK_TEMPERATURE = 0.5
BEDROCK_MAX_TOKENS = 1500
EXPECTED_MESSAGE_COUNT = 3
EXPECTED_TIMESTAMP_LENGTH = 19
RETRY_COUNT = 2


class MockRequest(BaseModel):
    """Mock request model for testing."""

    message: str
    value: int = 42


class MockResponse(BaseModel):
    """Mock response model for testing."""

    result: str
    success: bool = True


class TestLlmInvoker:
    """Test class for LlmInvoker."""

    @pytest.fixture
    @patch("awa.core.models.config.llm_providers_config.EnvConfig.get_env_config")
    def sample_config(self, mock_get_env_config: Mock) -> AppConfig:
        """Create a sample AppConfig for testing."""
        # Mock environment config to provide API keys
        mock_env_config = Mock()
        mock_env_config.azure_openai_api_key = "test-azure-key"
        mock_get_env_config.return_value = mock_env_config

        # Arrange
        return AppConfig(
            llm=LLMConfig(
                default_model="test-model",
                providers=LlmProvidersConfig(
                    openai=OpenAiLlmProvider(api_key="test-openai-key"),
                    azure_openai=AzureOpenAiLlmProvider(
                        resource_name="test-resource",
                        api_version="2023-05-15",
                        use_entra_auth=False,
                    ),
                    google_vertex=GoogleVertexLlmProvider(
                        location="us-central1",
                        project_id="test-project",
                        credentials_path="/path/to/credentials.json",
                    ),
                    lite_llm=LiteLlmProvider(
                        base_url="http://localhost:4000",
                        api_key="test-lite-llm-key",
                    ),
                    anthropic=AnthropicLlmProvider(
                        api_key="test-anthropic-key",
                    ),
                ),
                models=[
                    ModelConfig(
                        name="test-model",
                        provider=LlmProviderEnum.OPEN_AI,
                        model="gpt-4",
                        temperature=TEST_TEMPERATURE,
                        max_tokens=TEST_MAX_TOKENS,
                    ),
                    ModelConfig(
                        name="azure-model",
                        provider=LlmProviderEnum.AZURE_OPEN_AI,
                        model="gpt-4-deployment",
                        temperature=AZURE_TEST_TEMPERATURE,
                        max_tokens=AZURE_TEST_MAX_TOKENS,
                    ),
                ],
                behavior=LlmBehaviorConfig(
                    auto_retry_parse=RetryOnParseErrorConfig(
                        enabled=True,
                        max_attempts=3,
                        temperature_increment=0.1,
                    ),
                ),
            ),
        )

    @pytest.fixture
    def llm_invoker(self, sample_config: AppConfig) -> LlmInvoker:
        """Create an LlmInvoker instance for testing."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            baml_src_dir = Path(temp_dir) / "baml_src"
            baml_src_dir.mkdir()
            return LlmInvoker(sample_config, baml_src_dir)

    def test_init_default_baml_src_dir(self, sample_config: AppConfig) -> None:
        """Test LlmInvoker initialization with default baml_src_dir."""
        # Act
        invoker = LlmInvoker(sample_config)

        # Assert
        assert invoker._config == sample_config
        assert invoker._baml_src_dir.name == "baml_src"
        assert invoker._active_transforms == 0

    def test_init_custom_baml_src_dir(self, sample_config: AppConfig) -> None:
        """Test LlmInvoker initialization with custom baml_src_dir."""
        # Arrange
        custom_dir = Path("/custom/baml/src")

        # Act
        invoker = LlmInvoker(sample_config, custom_dir)

        # Assert
        assert invoker._config == sample_config
        assert invoker._baml_src_dir == custom_dir

    def test_get_cache_key_with_base_model(self, llm_invoker: LlmInvoker, sample_config: AppConfig) -> None:
        """Test cache key generation with BaseModel request."""
        # Arrange
        model_config = sample_config.llm.models[0]
        request = MockRequest(message="test", value=123)

        # Act
        cache_key = llm_invoker._get_cache_key(model_config, request)

        # Assert
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0

    def test_get_cache_key_with_dict(self, llm_invoker: LlmInvoker, sample_config: AppConfig) -> None:
        """Test cache key generation with dict request."""
        # Arrange
        model_config = sample_config.llm.models[0]
        request = {"message": "test", "value": 123}

        # Act
        cache_key = llm_invoker._get_cache_key(model_config, request)

        # Assert
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0

    def test_get_cache_key_invalid_request_type(self, llm_invoker: LlmInvoker, sample_config: AppConfig) -> None:
        """Test cache key generation with invalid request type raises TypeError."""
        # Arrange
        model_config = sample_config.llm.models[0]
        request = "invalid_request_type"

        # Act & Assert
        with pytest.raises(TypeError, match="Request is not a dict"):
            llm_invoker._get_cache_key(model_config, request)

    def test_get_cache_file_path(self, llm_invoker: LlmInvoker) -> None:
        """Test cache file path generation."""
        # Arrange
        cache_key = "test_cache_key"

        # Act
        cache_path = llm_invoker._get_cache_file_path(cache_key)

        # Assert
        assert cache_key in str(cache_path)
        assert str(cache_path).endswith(".cache")

    @patch("awa.core.utils.llm_invoker.FileSystemUtils.read")
    @patch("awa.core.utils.llm_invoker.Path.exists")
    async def test_load_from_cache_exists(self, mock_exists: Mock, mock_read: Mock, llm_invoker: LlmInvoker) -> None:
        """Test loading from cache when file exists."""
        # Arrange
        cache_key = "test_cache_key"
        expected_content = "cached_content"
        mock_exists.return_value = True
        mock_read.return_value = expected_content

        # Act
        result = await llm_invoker._load_from_cache(cache_key)

        # Assert
        assert result == expected_content
        mock_read.assert_called_once()

    @patch("awa.core.utils.llm_invoker.Path.exists")
    async def test_load_from_cache_not_exists(self, mock_exists: Mock, llm_invoker: LlmInvoker) -> None:
        """Test loading from cache when file doesn't exist."""
        # Arrange
        cache_key = "test_cache_key"
        mock_exists.return_value = False

        # Act
        result = await llm_invoker._load_from_cache(cache_key)

        # Assert
        assert result is None

    @patch("awa.core.utils.llm_invoker.FileSystemUtils.write")
    async def test_save_to_cache(self, mock_write: Mock, llm_invoker: LlmInvoker) -> None:
        """Test saving to cache."""
        # Arrange
        cache_key = "test_cache_key"
        cache_value = "test_value"

        # Act
        await llm_invoker._save_to_cache(cache_key, cache_value)

        # Assert
        mock_write.assert_called_once()

    @patch("awa.core.logger.logger.EnvConfig.get_env_config")
    def test_get_baml_client_options_openai(self, mock_get_env_config: Mock, sample_config: AppConfig) -> None:
        """Test BAML client options for OpenAI provider."""
        # Arrange
        mock_get_env_config().openai_api_key = "test-openai-key"
        invoker = LlmInvoker(sample_config)
        model_config = sample_config.llm.models[0]  # OpenAI model

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "openai"
        assert options["api_key"] == "test-openai-key"
        assert options["model"] == "gpt-4"
        assert options["temperature"] == TEST_TEMPERATURE
        assert options["max_tokens"] == TEST_MAX_TOKENS

    @patch("awa.core.logger.logger.EnvConfig.get_env_config")
    def test_get_baml_client_options_openai_with_base_url(
        self,
        mock_get_env_config: Mock,
        sample_config: AppConfig,
    ) -> None:
        """OpenAI options should include custom base URL when configured."""
        # Arrange
        mock_get_env_config().openai_api_key = "test-openai-key"
        sample_config.llm.providers.openai.base_url = "https://example.databricks"
        invoker = LlmInvoker(sample_config)
        model_config = sample_config.llm.models[0]

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "openai"
        assert options["base_url"] == "https://example.databricks"
        assert options["api_key"] == "test-openai-key"

    @patch("awa.core.logger.logger.EnvConfig.get_env_config")
    def test_get_baml_client_options_azure_openai(self, mock_get_env_config: Mock, sample_config: AppConfig) -> None:
        """Test BAML client options for Azure OpenAI provider."""
        # Arrange
        mock_get_env_config().azure_openai_api_key = "test-azure-key"
        invoker = LlmInvoker(sample_config)
        model_config = sample_config.llm.models[1]  # Azure OpenAI model

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "azure-openai"
        assert options["api_key"] == "test-azure-key"
        assert options["resource_name"] == "test-resource"
        assert options["deployment_id"] == "gpt-4-deployment"
        assert options["api_version"] == "2023-05-15"

    def test_get_baml_client_options_azure_openai_no_config(self, sample_config: AppConfig) -> None:
        """Test BAML client options for Azure OpenAI with missing config raises ValueError."""
        # Arrange
        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="test-azure",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-4",
        )
        invoker._config.llm.providers.azure_openai = None

        # Act & Assert
        with pytest.raises(ValueError, match="Azure OpenAI provider config not found"):
            invoker._get_baml_client_options(model_config)

    @patch("awa.core.utils.llm_invoker.AzureCliCredential")
    @patch("awa.core.utils.llm_invoker.AZURE_IDENTITY_AVAILABLE", new=True)
    def test_get_baml_client_options_azure_openai_entra_auth(
        self,
        mock_credential: Mock,
        sample_config: AppConfig,
    ) -> None:
        """Test BAML client options for Azure OpenAI with Entra authentication."""
        # Arrange
        mock_credential_instance = Mock()
        mock_token_instance = Mock()
        mock_token_instance.token = "mock_azure_token"
        mock_credential_instance.get_token.return_value = mock_token_instance
        mock_credential.return_value = mock_credential_instance

        # Create config with Entra auth enabled
        azure_config = AzureOpenAiLlmProvider(
            resource_name="test-resource",
            api_version="2023-05-15",
            use_entra_auth=True,
        )
        sample_config.llm.providers.azure_openai = azure_config

        invoker = LlmInvoker(sample_config)
        model_config = sample_config.llm.models[1]  # Azure OpenAI model

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "azure-openai"
        assert options["headers"]["Authorization"] == "Bearer mock_azure_token"
        assert options["resource_name"] == "test-resource"
        assert options["deployment_id"] == "gpt-4-deployment"
        assert options["api_version"] == "2023-05-15"

        # Verify Azure identity calls
        mock_credential.assert_called_once()
        mock_credential_instance.get_token.assert_called_once_with("https://cognitiveservices.azure.com/.default")

    @patch("awa.core.utils.llm_invoker.AZURE_IDENTITY_AVAILABLE", new=False)
    def test_get_baml_client_options_azure_openai_entra_auth_no_azure_identity(self, sample_config: AppConfig) -> None:
        """Test Azure OpenAI Entra auth fails when azure-identity package is not available."""
        # Arrange
        azure_config = AzureOpenAiLlmProvider(
            resource_name="test-resource",
            api_version="2023-05-15",
            use_entra_auth=True,
        )
        sample_config.llm.providers.azure_openai = azure_config

        invoker = LlmInvoker(sample_config)
        model_config = sample_config.llm.models[1]  # Azure OpenAI model

        # Act & Assert
        with pytest.raises(ValueError, match="Azure Identity package is required for Entra authentication"):
            invoker._get_baml_client_options(model_config)

    @patch("awa.core.utils.llm_invoker.AzureCliCredential")
    @patch("awa.core.utils.llm_invoker.AZURE_IDENTITY_AVAILABLE", new=True)
    def test_get_baml_client_options_azure_openai_entra_auth_credential_error(
        self,
        mock_credential: Mock,
        sample_config: AppConfig,
    ) -> None:
        """Test Azure OpenAI Entra auth handles credential errors gracefully."""
        # Arrange
        mock_credential.side_effect = Exception("Credential error")

        azure_config = AzureOpenAiLlmProvider(
            resource_name="test-resource",
            api_version="2023-05-15",
            use_entra_auth=True,
        )
        sample_config.llm.providers.azure_openai = azure_config

        invoker = LlmInvoker(sample_config)
        model_config = sample_config.llm.models[1]  # Azure OpenAI model

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to get Azure CLI credential token"):
            invoker._get_baml_client_options(model_config)

    @patch("awa.core.models.config.llm_providers_config.EnvConfig.get_env_config")
    def test_get_baml_client_options_azure_openai_api_key_missing(
        self,
        mock_get_env_config: Mock,
        sample_config: AppConfig,
    ) -> None:
        """Test Azure OpenAI gracefully handles missing API key (error deferred to BAML/OpenAI at runtime)."""
        # Arrange - Mock empty API key
        mock_env_config = Mock()
        mock_env_config.azure_openai_api_key = ""  # Empty API key
        mock_get_env_config.return_value = mock_env_config

        # Create Azure config with missing API key (should succeed at config time)
        azure_config = AzureOpenAiLlmProvider(
            resource_name="test-resource",
            api_version="2023-05-15",
            use_entra_auth=False,
        )
        sample_config.llm.providers.azure_openai = azure_config

        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="test-model",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-4",
        )

        # Act - Should succeed without raising error (error deferred to actual LLM call)
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert - Options should be generated but without api_key
        assert client_name == "azure-openai"
        assert "api_key" not in options  # Key not set when empty
        assert options["resource_name"] == "test-resource"
        assert options["deployment_id"] == "gpt-4"
        assert options["api_version"] == "2023-05-15"

    @patch("awa.core.utils.llm_invoker.AzureCliCredential")
    @patch("awa.core.utils.llm_invoker.AZURE_IDENTITY_AVAILABLE", new=True)
    @patch("awa.core.utils.llm_invoker.datetime")
    def test_azure_token_caching_success(
        self,
        mock_datetime: Mock,
        mock_credential: Mock,
        sample_config: AppConfig,
    ) -> None:
        """Test Azure token caching returns cached token when valid."""
        # Arrange
        mock_credential_instance = Mock()
        mock_token_instance = Mock()
        mock_token_instance.token = "cached_token"
        mock_credential_instance.get_token.return_value = mock_token_instance
        mock_credential.return_value = mock_credential_instance

        # Mock datetime to control cache expiration
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = fixed_time
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs) if args else fixed_time  # noqa: DTZ001

        azure_config = AzureOpenAiLlmProvider(
            resource_name="test-resource",
            api_version="2023-05-15",
            use_entra_auth=True,
        )
        sample_config.llm.providers.azure_openai = azure_config

        invoker = LlmInvoker(sample_config)
        model_config = sample_config.llm.models[1]  # Azure OpenAI model

        # Act - First call should acquire and cache token
        client_name1, options1 = invoker._get_baml_client_options(model_config)

        # Act - Second call should use cached token
        client_name2, options2 = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name1 == "azure-openai"
        assert client_name2 == "azure-openai"
        assert options1["headers"]["Authorization"] == "Bearer cached_token"
        assert options2["headers"]["Authorization"] == "Bearer cached_token"

        # Verify credential was only called once (cached on second call)
        mock_credential.assert_called_once()
        mock_credential_instance.get_token.assert_called_once()

    @patch("awa.core.utils.llm_invoker.AzureCliCredential")
    @patch("awa.core.utils.llm_invoker.AZURE_IDENTITY_AVAILABLE", new=True)
    def test_azure_token_caching_expiration(
        self,
        mock_credential: Mock,
        sample_config: AppConfig,
    ) -> None:
        """Test Azure token caching refreshes when token expires."""
        # Arrange
        mock_credential_instance = Mock()
        mock_token_instance1 = Mock()
        mock_token_instance1.token = "first_token"
        mock_token_instance2 = Mock()
        mock_token_instance2.token = "second_token"
        mock_credential_instance.get_token.side_effect = [mock_token_instance1, mock_token_instance2]
        mock_credential.return_value = mock_credential_instance

        azure_config = AzureOpenAiLlmProvider(
            resource_name="test-resource",
            api_version="2023-05-15",
            use_entra_auth=True,
        )
        sample_config.llm.providers.azure_openai = azure_config

        invoker = LlmInvoker(sample_config)
        model_config = sample_config.llm.models[1]  # Azure OpenAI model

        # Act - First call caches token
        _client_name1, options1 = invoker._get_baml_client_options(model_config)

        # Manually expire the cache entry by setting it to past time
        from awa.core.utils.llm_invoker import TokenCacheEntry

        expired_entry = TokenCacheEntry(
            token="first_token",  # noqa: S106
            expires_at=datetime.now(UTC) - timedelta(minutes=10),  # Expired 10 minutes ago
            resource_name="test-resource",
        )
        invoker._azure_credential_cache["test-resource"] = expired_entry

        # Act - Second call after expiration should get fresh token
        _client_name2, options2 = invoker._get_baml_client_options(model_config)

        # Assert
        assert options1["headers"]["Authorization"] == "Bearer first_token"
        assert options2["headers"]["Authorization"] == "Bearer second_token"

        # Verify credential was called twice (fresh token on expiration)
        assert mock_credential.call_count == 2
        assert mock_credential_instance.get_token.call_count == 2

    def test_clear_azure_token_cache(self, sample_config: AppConfig) -> None:
        """Test clearing Azure token cache."""
        # Arrange
        invoker = LlmInvoker(sample_config)

        # Manually add a cache entry
        from awa.core.utils.llm_invoker import TokenCacheEntry

        cache_entry = TokenCacheEntry(
            token="test_token",  # noqa: S106
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
            resource_name="test-resource",
        )
        invoker._azure_credential_cache["test-resource"] = cache_entry

        # Act
        invoker._clear_azure_token_cache("test-resource")

        # Assert
        assert "test-resource" not in invoker._azure_credential_cache

    @patch("awa.core.logger.logger.EnvConfig.get_env_config")
    def test_get_baml_client_options_lite_llm(self, mock_get_env_config: Mock, sample_config: AppConfig) -> None:
        """Test BAML client options for LiteLLM provider."""
        # Arrange
        mock_get_env_config().lite_llm_api_key = "test-lite-llm-key"
        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="lite-llm-model",
            provider=LlmProviderEnum.LITE_LLM,
            model="claude-3-sonnet",
            temperature=0.3,
        )

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "openai-generic"
        assert options["base_url"] == "http://localhost:4000"
        assert options["model"] == "claude-3-sonnet"
        assert options["api_key"] == "test-lite-llm-key"

    def test_get_baml_client_options_lite_llm_no_config(self, sample_config: AppConfig) -> None:
        """Test BAML client options for LiteLLM with missing config raises ValueError."""
        # Arrange
        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="lite-llm-model",
            provider=LlmProviderEnum.LITE_LLM,
            model="claude-3-sonnet",
        )
        invoker._config.llm.providers.lite_llm = None

        # Act & Assert
        with pytest.raises(ValueError, match="LiteLLM provider config not found"):
            invoker._get_baml_client_options(model_config)

    def test_get_baml_client_options_aws_bedrock(self, sample_config: AppConfig) -> None:
        """Test BAML client options for AWS Bedrock provider."""
        # Arrange
        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="bedrock-model",
            provider=LlmProviderEnum.AWS_BEDROCK,
            model="anthropic.claude-v2",
            temperature=BEDROCK_TEMPERATURE,
            max_tokens=BEDROCK_MAX_TOKENS,
            reasoning_effort="high",
        )

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "aws-bedrock"
        assert options["model"] == "anthropic.claude-v2"
        assert "reasoning_effort" not in options
        assert "max_tokens" not in options
        assert "temperature" not in options
        assert options["inference_configuration"]["temperature"] == BEDROCK_TEMPERATURE
        assert options["inference_configuration"]["max_tokens"] == BEDROCK_MAX_TOKENS

    def test_get_baml_client_options_google_vertex(self, sample_config: AppConfig) -> None:
        """Test BAML client options for Google Vertex provider."""
        # Arrange
        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="vertex-model",
            provider=LlmProviderEnum.GOOGLE_VERTEX,
            model="gemini-1.5-pro",
            temperature=0.3,
            max_tokens=1024,
        )

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "vertex-ai"
        assert options["model"] == "gemini-1.5-pro"
        assert options["location"] == "us-central1"
        assert options["project_id"] == "test-project"
        assert options["credentials"] == "/path/to/credentials.json"
        assert options["generationConfig"]["temperature"] == 0.3
        assert options["generationConfig"]["maxOutputTokens"] == 1024

    def test_get_baml_client_options_google_vertex_no_config(self, sample_config: AppConfig) -> None:
        """Test BAML client options for Google Vertex provider when config is missing."""
        # Arrange
        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="vertex-model",
            provider=LlmProviderEnum.GOOGLE_VERTEX,
            model="gemini-1.5-pro",
        )
        invoker._config.llm.providers.google_vertex = None

        # Act & Assert
        with pytest.raises(ValueError, match="Google Vertex provider config not found"):
            invoker._get_baml_client_options(model_config)

    @patch("awa.core.logger.logger.EnvConfig.get_env_config")
    def test_get_baml_client_options_anthropic(self, mock_get_env_config: Mock, sample_config: AppConfig) -> None:
        """Test BAML client options for Anthropic provider."""
        # Arrange
        mock_get_env_config().anthropic_api_key = "test-anthropic-key"
        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="anthropic-model",
            provider=LlmProviderEnum.ANTHROPIC,
            model="claude-3-sonnet-20240229",
            temperature=0.7,
            max_tokens=2048,
        )

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "anthropic"
        assert options["api_key"] == "test-anthropic-key"
        assert options["model"] == "claude-3-sonnet-20240229"
        assert options["temperature"] == 0.7
        assert options["max_tokens"] == 2048

    def test_get_baml_client_options_anthropic_with_base_url(self, sample_config: AppConfig) -> None:
        """Test BAML client options for Anthropic provider with custom base URL."""
        # Arrange
        invoker = LlmInvoker(sample_config)
        invoker._config.llm.providers.anthropic.base_url = "https://custom.anthropic.api"
        model_config = ModelConfig(
            name="anthropic-model",
            provider=LlmProviderEnum.ANTHROPIC,
            model="claude-3-sonnet-20240229",
        )

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "anthropic"
        assert options["base_url"] == "https://custom.anthropic.api"

    @patch("awa.core.logger.logger.EnvConfig.get_env_config")
    def test_get_baml_client_options_anthropic_no_config(
        self,
        mock_get_env_config: Mock,
        sample_config: AppConfig,
    ) -> None:
        """Test BAML client options for Anthropic with missing config uses default."""
        # Arrange
        mock_get_env_config().anthropic_api_key = "test-anthropic-key"
        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="anthropic-model",
            provider=LlmProviderEnum.ANTHROPIC,
            model="claude-3-sonnet-20240229",
        )
        invoker._config.llm.providers.anthropic = None

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "anthropic"
        assert options["api_key"] == "test-anthropic-key"
        assert options["model"] == "claude-3-sonnet-20240229"
        assert "base_url" not in options  # Default provider doesn't have base_url

    @patch("awa.core.auth.github_copilot.get_active_token")
    @patch("awa.core.logger.logger.EnvConfig.get_env_config")
    def test_get_baml_client_options_github_copilot(
        self,
        mock_get_env_config: Mock,
        mock_get_active_token: Mock,
        sample_config: AppConfig,
    ) -> None:
        """Test BAML client options for GitHub Copilot provider."""
        # Arrange
        mock_get_active_token.return_value = None  # Fall back to env var
        mock_get_env_config().github_copilot_api_key = "test-github-copilot-key"
        invoker = LlmInvoker(sample_config)
        model_config = ModelConfig(
            name="github-copilot-model",
            provider=LlmProviderEnum.GITHUB_COPILOT,
            model="claude-3-sonnet",
            temperature=0.5,
            max_tokens=1500,
        )

        # Act
        client_name, options = invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "openai-generic"
        assert options["api_key"] == "test-github-copilot-key"
        assert options["base_url"] == "https://api.githubcopilot.com"
        assert options["model"] == "claude-3-sonnet"
        assert options["temperature"] == 0.5
        assert options["max_tokens"] == 1500

    def test_utc_ms_to_sortable_timestamp(self) -> None:
        """Test UTC milliseconds to sortable timestamp conversion."""
        # Arrange
        timestamp_ms = 1704067200000  # 2024-01-01 00:00:00 UTC

        # Act
        result = LlmInvoker.utc_ms_to_sortable_timestamp(timestamp_ms)

        # Assert
        assert result.startswith("20240101_000000_")
        assert len(result) == EXPECTED_TIMESTAMP_LENGTH  # Format: YYYYMMDD_HHMMSS_SSS

    def test_map_model_name_bedrock_anthropic(self) -> None:
        """Test model name mapping for Bedrock Anthropic models."""
        # Arrange
        arn_model = "arn:aws:bedrock:us-west-2:123456789012:model/anthropic.claude-3-5-sonnet-20240620-v1:0"
        us_model = "us.anthropic.claude-3-5-sonnet-20240620-v1:0"

        # Act
        mapped_arn = LlmInvoker._map_model_name(arn_model)
        mapped_us = LlmInvoker._map_model_name(us_model)

        # Assert
        assert mapped_arn == "claude-3-5-sonnet-20240620"
        assert mapped_us == "claude-3-5-sonnet-20240620"

    def test_map_model_name_unchanged(self) -> None:
        """Test model name mapping for unknown models returns unchanged."""
        # Arrange
        model_name = "unknown-model-name"

        # Act
        result = LlmInvoker._map_model_name(model_name)

        # Assert
        assert result == model_name

    def test_convert_messages_for_cost_calculation(self) -> None:
        """Test message conversion for cost calculation."""
        # Arrange
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        # Act
        result = LlmInvoker._convert_messages_for_cost_calculation(messages)

        # Assert
        assert len(result) == EXPECTED_MESSAGE_COUNT
        for message in result:
            assert message["role"] == "user"
            assert "content" in message

    @patch("awa.core.utils.llm_invoker.LlmInvoker._load_baml_client_module")
    @patch("awa.core.utils.llm_invoker.set_log_level")
    async def test_get_baml_client(
        self,
        mock_set_log_level: Mock,
        mock_load_module: Mock,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test BAML client creation."""
        # Arrange
        model_config = sample_config.llm.models[0]
        mock_client = Mock()
        mock_b = Mock()
        mock_b.with_options.return_value = mock_client
        mock_load_module.return_value = mock_b

        # Act
        client, collector = await llm_invoker._get_baml_client(
            model_config=model_config,
            collector_name="test_collector",
            cache_key="test_key",
            baml_function_name="test_function",
        )

        # Assert
        assert client == mock_client
        assert isinstance(collector, Collector)
        mock_set_log_level.assert_called_once_with("INFO")

    def test_load_baml_client_module_missing_directory(self, llm_invoker: LlmInvoker) -> None:
        """Test loading BAML client module when directory doesn't exist."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            llm_invoker._baml_src_dir = Path(temp_dir) / "nonexistent_baml_src"

            # Act & Assert
            with pytest.raises(FileNotFoundError, match="BAML client directory not found"):
                llm_invoker._load_baml_client_module()

    async def test_run_baml_function_success_with_cache(
        self,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test successful BAML function execution with cache hit."""
        # Arrange
        model_config = sample_config.llm.models[0]
        request = MockRequest(message="test")
        cached_response = MockResponse(result="cached_result")
        activity_info = Mock()

        with (
            patch.object(llm_invoker, "_load_from_cache", return_value=cached_response.model_dump_json()),
            patch.object(llm_invoker, "_load_baml_client_module", return_value=Mock()),
            patch.object(llm_invoker, "_determine_response_type", return_value=MockResponse),
        ):
            # Act
            result = await llm_invoker._run_baml_function(
                top_level_workflow_type="test_workflow",
                top_level_workflow_id="test_id",
                activity_info=activity_info,
                model_config=model_config,
                request=request,
                baml_function_name="test_function",
                run_baml_function=AsyncMock(),
            )

            # Assert
            assert isinstance(result, MockResponse)
            assert result.result == "cached_result"

    async def test_run_baml_function_baml_validation_error_retry(
        self,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test BAML function execution with validation error triggering retry."""
        # Arrange
        model_config = sample_config.llm.models[0]
        request = MockRequest(message="test")
        activity_info = Mock()

        mock_run_function = AsyncMock()
        mock_run_function.side_effect = [
            BamlValidationError("Validation failed", [], "raw_output", "Detailed validation error message"),
            MockResponse(result="success_after_retry"),
        ]

        with (
            patch.object(llm_invoker, "_load_from_cache", return_value=None),
            patch.object(llm_invoker, "_get_baml_client", return_value=(Mock(), Mock())),
            patch.object(llm_invoker, "_log_baml_execution"),
            patch.object(llm_invoker, "_save_to_cache"),
            patch.object(llm_invoker, "_determine_response_type", return_value=MockResponse),
        ):
            # Act
            result = await llm_invoker._run_baml_function(
                top_level_workflow_type="test_workflow",
                top_level_workflow_id="test_id",
                activity_info=activity_info,
                model_config=model_config,
                request=request,
                baml_function_name="test_function",
                run_baml_function=mock_run_function,
            )

            # Assert
            assert isinstance(result, MockResponse)
            assert result.result == "success_after_retry"
            assert mock_run_function.call_count == RETRY_COUNT

    async def test_run_baml_function_baml_validation_error_max_retries(
        self,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test BAML function execution with validation error exceeding max retries."""
        # Arrange
        model_config = sample_config.llm.models[0]
        request = MockRequest(message="test")
        activity_info = Mock()

        mock_run_function = AsyncMock()
        mock_run_function.side_effect = BamlValidationError(
            "Validation failed",
            [],
            "raw_output",
            "Detailed validation error message",
        )

        with (
            patch.object(llm_invoker, "_load_from_cache", return_value=None),
            patch.object(llm_invoker, "_get_baml_client", return_value=(Mock(), Mock())),
            patch.object(llm_invoker, "_log_baml_execution"),
            patch.object(llm_invoker, "_determine_response_type", return_value=MockResponse),
            pytest.raises(AwaLlmResponseParsingError),
        ):
            # Act & Assert
            await llm_invoker._run_baml_function(
                top_level_workflow_type="test_workflow",
                top_level_workflow_id="test_id",
                activity_info=activity_info,
                model_config=model_config,
                request=request,
                baml_function_name="test_function",
                run_baml_function=mock_run_function,
            )

    async def test_run_baml_function_http_error_auth(self, llm_invoker: LlmInvoker, sample_config: AppConfig) -> None:
        """Test BAML function execution with HTTP authentication error."""
        # Arrange
        model_config = sample_config.llm.models[0]
        request = MockRequest(message="test")
        activity_info = Mock()

        # Mock the actual function execution to raise the exception before it gets to the LlmInvoker logic
        mock_run_function = AsyncMock()
        mock_run_function.side_effect = BamlClientHttpError(
            "test_client",
            "Unauthorized",
            401,
            "Detailed HTTP error message",
        )

        with (
            patch.object(llm_invoker, "_load_from_cache", return_value=None),
            patch.object(llm_invoker, "_get_baml_client", return_value=(Mock(), Mock())),
            patch.object(llm_invoker, "_log_baml_execution"),
            patch.object(llm_invoker, "_determine_response_type", return_value=MockResponse),
            pytest.raises(AwaLlmAuthError),
        ):
            # Act & Assert
            await llm_invoker._run_baml_function(
                top_level_workflow_type="test_workflow",
                top_level_workflow_id="test_id",
                activity_info=activity_info,
                model_config=model_config,
                request=request,
                baml_function_name="test_function",
                run_baml_function=mock_run_function,
            )

    async def test_run_baml_function_finish_reason_error(
        self,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test BAML function execution with finish reason error."""
        # Arrange
        model_config = sample_config.llm.models[0]
        request = MockRequest(message="test")
        activity_info = Mock()

        mock_run_function = AsyncMock()
        mock_run_function.side_effect = BamlClientFinishReasonError(
            "Invalid finish reason",
            "error_message",
            "raw_output",
            "stop",
            "Detailed finish reason error message",
        )

        with (
            patch.object(llm_invoker, "_load_from_cache", return_value=None),
            patch.object(llm_invoker, "_get_baml_client", return_value=(Mock(), Mock())),
            patch.object(llm_invoker, "_log_baml_execution"),
            patch.object(llm_invoker, "_determine_response_type", return_value=MockResponse),
            pytest.raises(BamlClientFinishReasonError),
        ):
            # Act & Assert
            await llm_invoker._run_baml_function(
                top_level_workflow_type="test_workflow",
                top_level_workflow_id="test_id",
                activity_info=activity_info,
                model_config=model_config,
                request=request,
                baml_function_name="test_function",
                run_baml_function=mock_run_function,
            )

    @patch("awa.core.utils.llm_invoker.ConfigUtils.get_model_config")
    async def test_execute_transform_success(
        self,
        mock_get_model_config: Mock,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test successful execute_transform."""
        # Arrange
        model_config = sample_config.llm.models[0]
        mock_get_model_config.return_value = model_config
        activity_info = Mock()

        request = MockRequest(message="test")
        expected_response = MockResponse(result="success")

        with patch.object(llm_invoker, "_run_baml_function", return_value=expected_response) as mock_run:
            # Act
            result = await llm_invoker.execute_transform(
                top_level_workflow_type="test_workflow",
                top_level_workflow_id="test_id",
                activity_info=activity_info,
                model_name="test-model",
                baml_function_name="test_function",
                request=request,
            )

            # Assert
            assert result == expected_response
            mock_get_model_config.assert_called_once_with(sample_config, "test-model")
            mock_run.assert_called_once()

    @patch("awa.core.utils.llm_invoker.ConfigUtils.get_model_config")
    async def test_execute_transform_function_not_found(
        self,
        mock_get_model_config: Mock,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test execute_transform with function not found error."""
        # Arrange
        model_config = sample_config.llm.models[0]
        mock_get_model_config.return_value = model_config
        activity_info = Mock()

        request = MockRequest(message="test")

        with patch.object(llm_invoker, "_run_baml_function") as mock_run:
            mock_run.side_effect = AttributeError("BAML function 'nonexistent_function' not found")

            # Act & Assert
            with pytest.raises(AttributeError, match=r"BAML function.*not found"):
                await llm_invoker.execute_transform(
                    top_level_workflow_type="test_workflow",
                    top_level_workflow_id="test_id",
                    activity_info=activity_info,
                    model_name="test-model",
                    baml_function_name="nonexistent_function",
                    request=request,
                )

    async def test_log_baml_execution_no_collector_last(self, llm_invoker: LlmInvoker) -> None:
        """Test BAML execution logging when collector.last is None."""
        # Arrange
        collector = Mock()
        collector.last = None

        # Mock activity_info with required properties
        activity_info = Mock()
        activity_info.task_queue = "test_queue"
        activity_info.workflow_type = "test_workflow_type"
        activity_info.workflow_id = "test_workflow_id"
        activity_info.workflow_run_id = "test_run_id"
        activity_info.activity_type = "test_activity"
        activity_info.activity_id = "test_activity_id"
        activity_info.attempt = 1

        request = {"message": "test"}
        response = {"result": "success"}
        exceptions = []
        cache_key = "test_cache_key"

        # Act
        await llm_invoker._log_baml_execution(
            top_level_workflow_type="test_workflow",
            top_level_workflow_id="test_id",
            activity_info=activity_info,
            collector=collector,
            request=request,
            response=response,
            success=True,
            exceptions=exceptions,
            cache_key=cache_key,
        )

        # Assert - Should complete without error
        # (The method primarily logs and doesn't return values to assert)

    def test_get_baml_client_options_gpt5_model(self, llm_invoker: LlmInvoker) -> None:
        """Test BAML client options generation for GPT-5 models."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            verbosity="high",
            reasoning_effort="medium",  # GPT-5 supports reasoning_effort with string values
            max_completion_tokens=4096,  # For Chat Completions API
            temperature=0.7,  # Should be ignored for GPT-5
        )

        # Act
        client_name, options = llm_invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "azure-openai"
        assert options["verbosity"] == "high"
        assert options["reasoning_effort"] == "medium"  # GPT-5 supports reasoning_effort
        assert options["max_completion_tokens"] == 4096
        assert "temperature" not in options  # Should not be present for GPT-5

    def test_get_baml_client_options_gpt5_default_verbosity(self, llm_invoker: LlmInvoker) -> None:
        """Test BAML client options generation for GPT-5 models with default verbosity."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            max_completion_tokens=2048,
        )

        # Act
        client_name, options = llm_invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "azure-openai"
        assert options["verbosity"] == "medium"  # Should default to medium
        assert "minimal_reasoning" not in options  # Should not be present when None
        assert options["max_completion_tokens"] == 2048

    def test_get_baml_client_options_gpt4_model_unchanged(
        self,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test BAML client options generation for GPT-4 models remains unchanged."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt4",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-4.1",
            is_gpt5_model=False,  # Explicitly not GPT-5
            temperature=0.7,
            reasoning_effort=3,
            max_tokens=32000,
        )

        # Mock the Azure OpenAI provider config
        with patch.object(llm_invoker, "_config", sample_config):
            # Act
            client_name, options = llm_invoker._get_baml_client_options(model_config)

            # Assert
            assert client_name == "azure-openai"
            assert options["temperature"] == 0.7
            assert options["reasoning_effort"] == 3
            assert options["max_tokens"] == 32000
            assert "verbosity" not in options  # Should not be present for GPT-4
            assert "minimal_reasoning" not in options  # Should not be present for GPT-4
            assert "resource_name" in options  # Should have standard Azure config for GPT-4
            assert "deployment_id" in options  # Should have standard Azure config for GPT-4
            assert "api_version" in options  # Should have standard Azure config for GPT-4
            assert "base_url" not in options  # Should not use base_url for standard Chat Completions

    def test_get_baml_client_options_responses_api_endpoint(
        self,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test BAML client options for Responses API endpoint configuration."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5-responses",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            use_responses_api=True,
            verbosity="low",
            max_output_tokens=3000,  # For Responses API
        )

        # Mock the Azure OpenAI provider config
        with patch.object(llm_invoker, "_config", sample_config):
            # Act
            client_name, options = llm_invoker._get_baml_client_options(model_config)

            # Assert
            assert client_name == "azure-openai"
            assert options["verbosity"] == "low"
            assert options["max_output_tokens"] == 3000  # Should use max_output_tokens for Responses API
            assert "base_url" in options  # Should contain custom base URL for Responses API
            assert "responses" in options["base_url"]  # Should contain 'responses' in the URL
            assert "api-version=" in options["base_url"]  # Should include API version in URL
            assert "max_completion_tokens" not in options  # Should not use Chat Completions API param
            assert "resource_name" not in options  # Should not have resource_name when using base_url
            assert "deployment_id" not in options  # Should not have deployment_id when using base_url
            assert "api_version" not in options  # Should not have separate api_version when using base_url

    def test_gpt5_validation_error_wrong_token_param_responses_api(self) -> None:
        """Test that GPT-5 with Responses API raises validation error if max_completion_tokens is used."""
        # Arrange - Try to create a config with wrong token parameter for Responses API
        with pytest.raises(ValueError, match="requires 'max_output_tokens', not 'max_completion_tokens'"):
            ModelConfig(
                name="test-gpt5-bad",
                provider=LlmProviderEnum.AZURE_OPEN_AI,
                model="gpt-5",
                is_gpt5_model=True,
                use_responses_api=True,  # Using Responses API
                max_completion_tokens=4096,  # Wrong! Should use max_output_tokens
            )

    def test_gpt5_validation_error_wrong_token_param_chat_completions(self) -> None:
        """Test that GPT-5 with Chat Completions API raises validation error if max_output_tokens is used."""
        # Arrange - Try to create a config with wrong token parameter for Chat Completions API
        with pytest.raises(ValueError, match="requires 'max_completion_tokens', not 'max_output_tokens'"):
            ModelConfig(
                name="test-gpt5-bad",
                provider=LlmProviderEnum.AZURE_OPEN_AI,
                model="gpt-5",
                is_gpt5_model=True,
                use_responses_api=False,  # Using Chat Completions API
                max_output_tokens=65536,  # Wrong! Should use max_completion_tokens
            )

    def test_gpt5_validation_error_max_tokens_not_supported(self) -> None:
        """Test that GPT-5 raises validation error if max_tokens is used (deprecated parameter)."""
        # Arrange - Try to create a config with deprecated max_tokens parameter
        with pytest.raises(ValueError, match="GPT-5 does not support 'max_tokens'"):
            ModelConfig(
                name="test-gpt5-bad",
                provider=LlmProviderEnum.AZURE_OPEN_AI,
                model="gpt-5",
                is_gpt5_model=True,
                use_responses_api=True,
                max_tokens=4096,  # Wrong! GPT-5 doesn't support this parameter
            )

    def test_gpt5_responses_api_parameter_routing(self, llm_invoker: LlmInvoker) -> None:
        """Test that GPT-5 with Responses API routes max_output_tokens correctly."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5-responses",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            use_responses_api=True,
            verbosity="medium",
            reasoning_effort="high",
            max_output_tokens=65536,
        )

        # Act
        client_name, options = llm_invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "azure-openai"
        assert options["verbosity"] == "medium"
        assert options["reasoning_effort"] == "high"
        assert options["max_output_tokens"] == 65536  # Correct parameter for Responses API
        assert "max_completion_tokens" not in options  # Should not have Chat Completions param
        assert "max_tokens" not in options  # Should not have deprecated param

    def test_gpt5_chat_completions_parameter_routing(self, llm_invoker: LlmInvoker) -> None:
        """Test that GPT-5 with Chat Completions API routes max_completion_tokens correctly."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5-chat",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5-mini",
            is_gpt5_model=True,
            use_responses_api=False,
            verbosity="low",
            reasoning_effort="minimal",
            max_completion_tokens=4096,
        )

        # Act
        client_name, options = llm_invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "azure-openai"
        assert options["verbosity"] == "low"
        assert options["reasoning_effort"] == "minimal"
        assert options["max_completion_tokens"] == 4096  # Correct parameter for Chat Completions API
        assert "max_output_tokens" not in options  # Should not have Responses API param
        assert "max_tokens" not in options  # Should not have deprecated param

    # ========== Helper Method Tests ==========

    def test_get_token_parameter_for_api_responses_api(self, llm_invoker: LlmInvoker) -> None:
        """Test _get_token_parameter_for_api returns max_output_tokens for Responses API."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            use_responses_api=True,
            max_output_tokens=65536,
        )

        # Act
        result = llm_invoker._get_token_parameter_for_api(model_config)

        # Assert
        assert result == {"max_output_tokens": 65536}

    def test_get_token_parameter_for_api_chat_completions(self, llm_invoker: LlmInvoker) -> None:
        """Test _get_token_parameter_for_api returns max_completion_tokens for Chat Completions API."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            use_responses_api=False,
            max_completion_tokens=32000,
        )

        # Act
        result = llm_invoker._get_token_parameter_for_api(model_config)

        # Assert
        assert result == {"max_completion_tokens": 32000}

    def test_get_token_parameter_for_api_empty(self, llm_invoker: LlmInvoker) -> None:
        """Test _get_token_parameter_for_api returns empty dict when no token params set."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            use_responses_api=False,
            # No token parameters set
        )

        # Act
        result = llm_invoker._get_token_parameter_for_api(model_config)

        # Assert
        assert result == {}

    def test_build_gpt5_parameters_default_verbosity(self, llm_invoker: LlmInvoker) -> None:
        """Test _build_gpt5_parameters defaults verbosity to 'medium' when not specified."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            use_responses_api=False,
            max_completion_tokens=4096,
            # verbosity not set - should default to 'medium'
        )

        # Act
        result = llm_invoker._build_gpt5_parameters(model_config)

        # Assert
        assert result["verbosity"] == "medium"
        assert result["max_completion_tokens"] == 4096

    def test_build_gpt5_parameters_all_verbosity_levels(self, llm_invoker: LlmInvoker) -> None:
        """Test _build_gpt5_parameters handles all verbosity levels correctly."""
        # Test each verbosity level
        for verbosity_level in ["low", "medium", "high"]:
            # Arrange
            model_config = ModelConfig(
                name="test-gpt5",
                provider=LlmProviderEnum.AZURE_OPEN_AI,
                model="gpt-5",
                is_gpt5_model=True,
                use_responses_api=False,
                verbosity=verbosity_level,
                max_completion_tokens=2048,
            )

            # Act
            result = llm_invoker._build_gpt5_parameters(model_config)

            # Assert
            assert result["verbosity"] == verbosity_level

    def test_build_gpt5_parameters_with_reasoning_effort(self, llm_invoker: LlmInvoker) -> None:
        """Test _build_gpt5_parameters includes reasoning_effort when specified."""
        # Test each reasoning effort level per Microsoft docs: minimal, low, medium, high
        for effort_level in ["minimal", "low", "medium", "high"]:
            # Arrange
            model_config = ModelConfig(
                name="test-gpt5",
                provider=LlmProviderEnum.AZURE_OPEN_AI,
                model="gpt-5",
                is_gpt5_model=True,
                use_responses_api=False,
                reasoning_effort=effort_level,
                max_completion_tokens=4096,
            )

            # Act
            result = llm_invoker._build_gpt5_parameters(model_config)

            # Assert
            assert result["reasoning_effort"] == effort_level
            assert result["verbosity"] == "medium"  # Default

    def test_build_gpt5_parameters_without_reasoning_effort(self, llm_invoker: LlmInvoker) -> None:
        """Test _build_gpt5_parameters excludes reasoning_effort when not specified."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            use_responses_api=False,
            max_completion_tokens=2048,
            # reasoning_effort not set
        )

        # Act
        result = llm_invoker._build_gpt5_parameters(model_config)

        # Assert
        assert "reasoning_effort" not in result
        assert result["verbosity"] == "medium"

    # ========== Azure GPT-5 Full Configuration Tests ==========

    def test_azure_gpt5_chat_completions_full_config(
        self,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test Azure GPT-5 with Chat Completions API has complete configuration."""
        # Arrange
        model_config = ModelConfig(
            name="test-gpt5-azure-chat",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5-deployment",
            is_gpt5_model=True,
            use_responses_api=False,  # Chat Completions API
            verbosity="high",
            reasoning_effort="high",
            max_completion_tokens=32000,
        )

        with patch.object(llm_invoker, "_config", sample_config):
            # Act
            client_name, options = llm_invoker._get_baml_client_options(model_config)

            # Assert - Azure config
            assert client_name == "azure-openai"
            assert options["resource_name"] == "test-resource"
            assert options["deployment_id"] == "gpt-5-deployment"
            assert options["api_version"] == "2023-05-15"

            # Assert - GPT-5 parameters
            assert options["verbosity"] == "high"
            assert options["reasoning_effort"] == "high"
            assert options["max_completion_tokens"] == 32000

            # Assert - Should NOT have Responses API params
            assert "base_url" not in options
            assert "max_output_tokens" not in options
            assert "temperature" not in options  # GPT-5 doesn't use temperature

    @patch("awa.core.utils.llm_invoker.AzureCliCredential")
    @patch("awa.core.utils.llm_invoker.AZURE_IDENTITY_AVAILABLE", new=True)
    def test_azure_gpt5_entra_auth_responses_api(
        self,
        mock_credential: Mock,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test Azure GPT-5 with Entra Auth + Responses API has correct configuration."""
        # Arrange
        mock_credential_instance = Mock()
        mock_token_instance = Mock()
        mock_token_instance.token = "entra_token_responses"
        mock_credential_instance.get_token.return_value = mock_token_instance
        mock_credential.return_value = mock_credential_instance

        # Create Azure config with Entra auth
        azure_config = AzureOpenAiLlmProvider(
            resource_name="gpt5-resource",
            api_version="2024-12-01",
            use_entra_auth=True,
        )
        sample_config.llm.providers.azure_openai = azure_config

        model_config = ModelConfig(
            name="gpt5-responses-entra",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5-deployment",
            is_gpt5_model=True,
            use_responses_api=True,  # Responses API
            verbosity="low",
            reasoning_effort="medium",
            max_output_tokens=65536,
        )

        with patch.object(llm_invoker, "_config", sample_config):
            # Act
            client_name, options = llm_invoker._get_baml_client_options(model_config)

            # Assert - Client and auth
            assert client_name == "azure-openai"
            assert options["headers"]["Authorization"] == "Bearer entra_token_responses"

            # Assert - Responses API uses base_url
            assert "base_url" in options
            assert "responses" in options["base_url"]
            assert "gpt5-resource" in options["base_url"]
            assert "2024-12-01" in options["base_url"]

            # Assert - GPT-5 Responses API parameters
            assert options["verbosity"] == "low"
            assert options["reasoning_effort"] == "medium"
            assert options["max_output_tokens"] == 65536

            # Assert - Should NOT have Chat Completions params
            assert "resource_name" not in options
            assert "deployment_id" not in options
            assert "api_version" not in options
            assert "max_completion_tokens" not in options

    @patch("awa.core.utils.llm_invoker.AzureCliCredential")
    @patch("awa.core.utils.llm_invoker.AZURE_IDENTITY_AVAILABLE", new=True)
    def test_azure_gpt5_entra_auth_chat_completions(
        self,
        mock_credential: Mock,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test Azure GPT-5 with Entra Auth + Chat Completions API has correct configuration."""
        # Arrange
        mock_credential_instance = Mock()
        mock_token_instance = Mock()
        mock_token_instance.token = "entra_token_chat"
        mock_credential_instance.get_token.return_value = mock_token_instance
        mock_credential.return_value = mock_credential_instance

        azure_config = AzureOpenAiLlmProvider(
            resource_name="gpt5-resource",
            api_version="2024-12-01",
            use_entra_auth=True,
        )
        sample_config.llm.providers.azure_openai = azure_config

        model_config = ModelConfig(
            name="gpt5-chat-entra",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5-deployment",
            is_gpt5_model=True,
            use_responses_api=False,  # Chat Completions API
            verbosity="medium",
            reasoning_effort="high",
            max_completion_tokens=32000,
        )

        with patch.object(llm_invoker, "_config", sample_config):
            # Act
            client_name, options = llm_invoker._get_baml_client_options(model_config)

            # Assert - Client and auth
            assert client_name == "azure-openai"
            assert options["headers"]["Authorization"] == "Bearer entra_token_chat"

            # Assert - Chat Completions API uses standard Azure config
            assert options["resource_name"] == "gpt5-resource"
            assert options["deployment_id"] == "gpt-5-deployment"
            assert options["api_version"] == "2024-12-01"

            # Assert - GPT-5 Chat Completions parameters
            assert options["verbosity"] == "medium"
            assert options["reasoning_effort"] == "high"
            assert options["max_completion_tokens"] == 32000

            # Assert - Should NOT have Responses API params
            assert "base_url" not in options
            assert "max_output_tokens" not in options

    @patch("awa.core.utils.llm_invoker.AzureCliCredential")
    @patch("awa.core.utils.llm_invoker.AZURE_IDENTITY_AVAILABLE", new=True)
    async def test_azure_auth_retry_with_gpt5_model(
        self,
        mock_credential: Mock,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test Azure Entra auth retry with GPT-5 model preserves GPT-5 parameters."""
        # Arrange
        mock_credential_instance = Mock()
        mock_first_token = Mock()
        mock_first_token.token = "expired_token"
        mock_fresh_token = Mock()
        mock_fresh_token.token = "fresh_token"
        # First call returns expired token, second call returns fresh token
        mock_credential_instance.get_token.side_effect = [mock_first_token, mock_fresh_token]
        mock_credential.return_value = mock_credential_instance

        azure_config = AzureOpenAiLlmProvider(
            resource_name="gpt5-resource",
            api_version="2024-12-01",
            use_entra_auth=True,
        )
        sample_config.llm.providers.azure_openai = azure_config

        model_config = ModelConfig(
            name="gpt5-auth-retry",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5-deployment",
            is_gpt5_model=True,
            use_responses_api=False,
            verbosity="high",
            reasoning_effort="high",
            max_completion_tokens=32000,
        )

        request = MockRequest(message="test")
        activity_info = Mock()

        # Mock run function to fail with 401 on first attempt, succeed on retry
        mock_run_function = AsyncMock()
        mock_run_function.side_effect = [
            BamlClientHttpError("test_client", "Unauthorized", 401, "Detailed HTTP error message"),
            MockResponse(result="success_after_auth_retry"),
        ]

        # Mock BAML client loading
        mock_b_client = Mock()
        mock_b_client.with_options.return_value = Mock()

        with (
            patch.object(llm_invoker, "_config", sample_config),
            patch.object(llm_invoker, "_load_from_cache", return_value=None),
            patch.object(llm_invoker, "_load_baml_client_module", return_value=mock_b_client),
            patch.object(llm_invoker, "_log_baml_execution"),
            patch.object(llm_invoker, "_save_to_cache"),
            patch.object(llm_invoker, "_determine_response_type", return_value=MockResponse),
        ):
            # Act
            result = await llm_invoker._run_baml_function(
                top_level_workflow_type="test_workflow",
                top_level_workflow_id="test_id",
                activity_info=activity_info,
                model_config=model_config,
                request=request,
                baml_function_name="test_function",
                run_baml_function=mock_run_function,
            )

            # Assert
            assert isinstance(result, MockResponse)
            assert result.result == "success_after_auth_retry"
            # Verify token was refreshed (called twice - once for initial attempt, once for retry)
            assert mock_credential_instance.get_token.call_count == 2

    # ========== Edge Case Tests ==========

    def test_gpt5_empty_token_parameters(
        self,
        llm_invoker: LlmInvoker,
        sample_config: AppConfig,
    ) -> None:
        """Test GPT-5 with no token parameters set doesn't error."""
        # Arrange
        model_config = ModelConfig(
            name="gpt5-no-tokens",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            use_responses_api=False,
            verbosity="medium",
            # No max_output_tokens or max_completion_tokens
        )

        with patch.object(llm_invoker, "_config", sample_config):
            # Act
            client_name, options = llm_invoker._get_baml_client_options(model_config)

            # Assert
            assert client_name == "azure-openai"
            assert options["verbosity"] == "medium"
            assert "max_output_tokens" not in options
            assert "max_completion_tokens" not in options
            assert "max_tokens" not in options

    def test_gpt5_verbosity_explicit_none(self, llm_invoker: LlmInvoker) -> None:
        """Test GPT-5 with explicit None verbosity defaults to 'medium'."""
        # Arrange
        model_config = ModelConfig(
            name="gpt5-none-verbosity",
            provider=LlmProviderEnum.AZURE_OPEN_AI,
            model="gpt-5",
            is_gpt5_model=True,
            use_responses_api=False,
            verbosity=None,  # Explicitly set to None
            max_completion_tokens=2048,
        )

        # Act
        result = llm_invoker._build_gpt5_parameters(model_config)

        # Assert
        assert result["verbosity"] == "medium"  # Should default to medium

    # ========== Non-Azure Provider Tests ==========

    @patch("awa.core.logger.logger.EnvConfig.get_env_config")
    def test_openai_provider_with_gpt5_model(
        self,
        mock_get_env_config: Mock,
        llm_invoker: LlmInvoker,
    ) -> None:
        """Test OpenAI (non-Azure) provider with GPT-5 model applies GPT-5 parameters correctly."""
        # Arrange
        mock_get_env_config().openai_api_key = "test-openai-key"

        model_config = ModelConfig(
            name="openai-gpt5",
            provider=LlmProviderEnum.OPEN_AI,
            model="gpt-5-preview",
            is_gpt5_model=True,
            use_responses_api=False,  # Chat Completions API
            verbosity="high",
            reasoning_effort="high",
            max_completion_tokens=16000,
        )

        # Act
        client_name, options = llm_invoker._get_baml_client_options(model_config)

        # Assert
        assert client_name == "openai"
        assert options["api_key"] == "test-openai-key"
        assert options["model"] == "gpt-5-preview"
        assert options["verbosity"] == "high"
        assert options["reasoning_effort"] == "high"
        assert options["max_completion_tokens"] == 16000
        assert "temperature" not in options  # GPT-5 doesn't use temperature
