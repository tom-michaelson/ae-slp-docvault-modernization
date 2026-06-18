"""Unit tests for generate_embeddings activity."""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from awa.core.activities.generate_embeddings import (
    _generate_azure_openai_embeddings,
    _get_azure_openai_client_from_model_config,
    _validate_embedding_model,
    generate_embeddings_activity,
)
from awa.core.models.config.app_config import AppConfig
from awa.core.models.config.llm_config import LLMConfig
from awa.core.models.config.llm_providers_config import AzureOpenAiLlmProvider, LlmProvidersConfig
from awa.core.models.config.model_config import ModelConfig
from awa.core.models.vector_ingestion_output import ChunkInfo, EmbeddingResult


class TestAzureOpenAIEmbeddings:
    """Test Azure OpenAI embedding functionality."""

    def test_validate_embedding_model_azure_openai_models(self) -> None:
        """Test that Azure OpenAI embedding models are validated correctly."""
        # Test Azure OpenAI models
        _validate_embedding_model("azure-text-embedding-ada-002")  # Should not raise

        # Test invalid Azure OpenAI models
        with pytest.raises(ValueError):
            _validate_embedding_model("azure-text-embedding-3-small")
        with pytest.raises(ValueError):
            _validate_embedding_model("azure-text-embedding-3-large")

    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test-key"}, clear=False)
    @patch("awa.core.utils.config_loader.ConfigLoader.get_config")
    def test_get_azure_openai_client_success(self, mock_get_config: Mock) -> None:
        """Test successful Azure OpenAI client creation."""
        from awa.core.models.config.model_config import ModelConfig

        # Mock config loader to throw exception, forcing default domain
        mock_get_config.side_effect = ValueError("Config not available")

        model_config = ModelConfig(
            name="test-model",
            provider="azureopenai",
            model="text-embedding-ada-002",
            resource_name="test-resource",
            api_version="2024-02-15-preview",
        )

        client = _get_azure_openai_client_from_model_config(model_config)

        assert client.api_key == "test-key"
        assert "test-resource.openai.azure.com" in str(client.base_url)

    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test-key"}, clear=False)
    def test_get_azure_openai_client_custom_domain(self) -> None:
        """Test Azure OpenAI client creation with custom domain."""
        from awa.core.models.config.model_config import ModelConfig

        model_config = ModelConfig(
            name="test-model",
            provider="azureopenai",
            model="text-embedding-ada-002",
            resource_name="ai-skylercarlson5076ai534536736521",
            api_version="2024-02-15-preview",
            domain="cognitiveservices.azure.com",
        )

        client = _get_azure_openai_client_from_model_config(model_config)

        assert client.api_key == "test-key"
        assert "ai-skylercarlson5076ai534536736521.cognitiveservices.azure.com" in str(client.base_url)

    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test-key"}, clear=False)
    @patch("awa.core.utils.config_loader.ConfigLoader.get_config")
    def test_get_azure_openai_client_domain_precedence(self, mock_get_config: Mock) -> None:
        """Test domain precedence: model domain overrides provider domain."""
        # Mock config with provider-level domain
        provider_config = AzureOpenAiLlmProvider(
            resource_name="provider-resource",
            api_version="2024-02-15-preview",
            domain="cognitiveservices.azure.com",  # Provider wants cognitive services
            use_entra_auth=False,
        )
        llm_config = LLMConfig(
            default_model="test-model",
            providers=LlmProvidersConfig(azure_openai=provider_config),
            models=[],
        )
        app_config = AppConfig(llm=llm_config)
        mock_get_config.return_value = app_config

        # Model config with different domain (should override provider)
        model_config = ModelConfig(
            name="test-model",
            provider="azureopenai",
            model="text-embedding-ada-002",
            resource_name="model-resource",
            api_version="2024-02-15-preview",
            domain="openai.azure.com",  # Model wants openai domain (overrides provider)
        )

        client = _get_azure_openai_client_from_model_config(model_config)

        # Should use model domain, not provider domain
        assert "model-resource.openai.azure.com" in str(client.base_url)

    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test-key"}, clear=False)
    @patch("awa.core.utils.config_loader.ConfigLoader.get_config")
    def test_get_azure_openai_client_provider_domain_fallback(self, mock_get_config: Mock) -> None:
        """Test domain fallback: uses provider domain when model domain not specified."""
        # Mock config with provider-level domain
        provider_config = AzureOpenAiLlmProvider(
            resource_name="provider-resource",
            api_version="2024-02-15-preview",
            domain="cognitiveservices.azure.com",  # Provider domain
            use_entra_auth=False,
        )
        llm_config = LLMConfig(
            default_model="test-model",
            providers=LlmProvidersConfig(azure_openai=provider_config),
            models=[],
        )
        app_config = AppConfig(llm=llm_config)
        mock_get_config.return_value = app_config

        # Model config without domain (should use provider domain)
        model_config = ModelConfig(
            name="test-model",
            provider="azureopenai",
            model="text-embedding-ada-002",
            resource_name="model-resource",
            api_version="2024-02-15-preview",
            # domain not specified - should fallback to provider
        )

        client = _get_azure_openai_client_from_model_config(model_config)

        # Should use provider domain
        assert "model-resource.cognitiveservices.azure.com" in str(client.base_url)

    @patch.dict("os.environ", {}, clear=True)
    def test_get_azure_openai_client_no_api_key(self) -> None:
        """Test Azure OpenAI client creation fails without API key."""
        from awa.core.models.config.model_config import ModelConfig

        model_config = ModelConfig(
            name="test-model",
            provider="azureopenai",
            model="text-embedding-ada-002",
            resource_name="test-resource",
            api_version="2024-02-15-preview",
        )

        with pytest.raises(ValueError, match="Azure OpenAI API key not found"):
            _get_azure_openai_client_from_model_config(model_config)

    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test-key"}, clear=False)
    def test_get_azure_openai_client_missing_resource_name(self) -> None:
        """Test Azure OpenAI client creation fails without resource_name."""
        from awa.core.models.config.model_config import ModelConfig

        model_config = ModelConfig(
            name="test-model",
            provider="azureopenai",
            model="text-embedding-ada-002",
            # resource_name is None
            api_version="2024-02-15-preview",
        )

        with pytest.raises(ValueError, match="resource_name not found"):
            _get_azure_openai_client_from_model_config(model_config)

    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test-key"}, clear=False)
    def test_get_azure_openai_client_missing_api_version(self) -> None:
        """Test Azure OpenAI client creation fails without api_version."""
        from awa.core.models.config.model_config import ModelConfig

        model_config = ModelConfig(
            name="test-model",
            provider="azureopenai",
            model="text-embedding-ada-002",
            resource_name="test-resource",
            # api_version is None
        )

        with pytest.raises(ValueError, match="api_version not found"):
            _get_azure_openai_client_from_model_config(model_config)

    @patch("awa.core.activities.generate_embeddings._get_azure_openai_client_from_model_config")
    async def test_generate_azure_openai_embeddings_success(self, mock_get_client: Mock) -> None:
        """Test successful Azure OpenAI embedding generation."""
        # Mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_embedding = Mock()
        # Mock a 1536-dimensional embedding (typical for text-embedding-ada-002)
        mock_embedding.embedding = [0.1] * 1536
        # Create response data with 2 embeddings for 2 texts
        mock_response.data = [mock_embedding, mock_embedding]
        mock_client.embeddings.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        texts = ["Test text 1", "Test text 2"]
        embeddings = await _generate_azure_openai_embeddings(texts, "text-embedding-ada-002", 128, mock_client)

        assert embeddings.shape == (2, 128)  # Should be truncated to 128 dimensions
        mock_client.embeddings.create.assert_called_once()

    @patch("awa.core.activities.generate_embeddings._get_azure_openai_client_from_model_config")
    async def test_generate_azure_openai_embeddings_padding(self, mock_get_client: Mock) -> None:
        """Test Azure OpenAI embedding generation with padding."""
        # Mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_embedding = Mock()
        # Mock a 512-dimensional embedding (smaller than requested)
        mock_embedding.embedding = [0.1] * 512
        mock_response.data = [mock_embedding]
        mock_client.embeddings.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        texts = ["Test text"]
        embeddings = await _generate_azure_openai_embeddings(texts, "text-embedding-ada-002", 1024, mock_client)

        assert embeddings.shape == (1, 1024)  # Should be padded to 1024 dimensions
        # Check that the original embedding is preserved (after normalization)
        # The embeddings are normalized, so we need to check the relative values
        original_embedding = embeddings[0, :512]
        assert len(original_embedding) == 512
        # Check that padding is zeros
        padding = embeddings[0, 512:]
        assert np.allclose(padding, [0.0] * 512)

    @patch("awa.core.activities.generate_embeddings._get_azure_openai_client_from_model_config")
    async def test_generate_azure_openai_embeddings_batch_processing(self, mock_get_client: Mock) -> None:
        """Test Azure OpenAI embedding generation with batch processing."""
        # Mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_embedding = Mock()
        mock_embedding.embedding = [0.1] * 1536

        # Mock the client to return different responses for each batch
        def mock_create_response(*args: object, **kwargs: object) -> Mock:  # noqa: ARG001
            # Return response with embeddings matching the input text count
            input_texts = kwargs.get("input", [])
            mock_response.data = [mock_embedding] * len(input_texts)
            return mock_response

        mock_client.embeddings.create.side_effect = mock_create_response
        mock_get_client.return_value = mock_client

        # Create 250 texts to test batching
        texts = [f"Test text {i}" for i in range(250)]
        embeddings = await _generate_azure_openai_embeddings(texts, "text-embedding-ada-002", 128, mock_client)

        assert embeddings.shape == (250, 128)
        # Should have been called 3 times (250 texts / 100 batch size = 3 batches)
        assert mock_client.embeddings.create.call_count == 3

    @patch("awa.core.activities.generate_embeddings._get_azure_openai_client_from_model_config")
    async def test_generate_azure_openai_embeddings_api_error(self, mock_get_client: Mock) -> None:
        """Test Azure OpenAI embedding generation handles API errors."""
        mock_client = Mock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        texts = ["Test text"]

        with pytest.raises(RuntimeError, match="Azure OpenAI API error"):
            await _generate_azure_openai_embeddings(texts, "text-embedding-ada-002", 128, mock_client)

    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test-key"}, clear=False)
    @patch("awa.core.utils.config_loader.ConfigLoader.get_config")
    @patch("awa.core.activities.generate_embeddings._validate_embedding_model")
    @patch("awa.core.activities.generate_embeddings._get_azure_openai_client_from_model_config")
    @patch("awa.core.activities.generate_embeddings._get_embedding_model_config")
    async def test_generate_embeddings_activity_azure_openai_success(
        self,
        mock_get_config: Mock,
        mock_get_client: Mock,
        mock_validate: Mock,
        mock_config_loader: Mock,
    ) -> None:
        """Test that the activity successfully uses Azure OpenAI embeddings."""
        from awa.core.models.config.model_config import ModelConfig

        # Mock the embedding model config
        mock_model_config = ModelConfig(
            name="azure-text-embedding-ada-002",
            provider="azureopenai",
            model="text-embedding-ada-002",
            resource_name="test-resource",
            api_version="2024-02-15-preview",
        )

        # Configure mock to return config for the specific model name
        def get_config_side_effect(model_name: str | None = None) -> ModelConfig | None:
            if model_name == "azure-text-embedding-ada-002":
                return mock_model_config
            return None

        mock_get_config.side_effect = get_config_side_effect

        # Mock validation to not raise exceptions
        mock_validate.return_value = None

        # Mock config loader to avoid real config loading
        mock_config_loader.return_value = Mock()

        # Mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_embedding = Mock()
        mock_embedding.embedding = [0.1] * 1536
        mock_response.data = [mock_embedding]
        mock_client.embeddings.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        chunks = [ChunkInfo(chunk_id="chunk_1", text="Test content", token_count=3, start_index=0, end_index=12)]

        result = await generate_embeddings_activity(chunks, "azure-text-embedding-ada-002", 128)

        assert isinstance(result, EmbeddingResult)
        assert len(result.chunks) == 1
        assert len(result.chunks[0].embedding_vector) == 128
        assert result.actual_model == "text-embedding-ada-002"
        assert result.actual_provider == "azureopenai"
        mock_client.embeddings.create.assert_called_once()

    @patch.dict("os.environ", {}, clear=True)  # Clear all environment variables
    @patch("awa.core.activities.generate_embeddings._get_embedding_model_config")
    async def test_generate_embeddings_activity_azure_openai_configuration_error(self, mock_get_config: Mock) -> None:
        """Test that the activity fails gracefully when Azure OpenAI configuration is missing."""
        from awa.core.models.config.model_config import ModelConfig

        # Mock to return a config without API key environment variable
        mock_model_config = ModelConfig(
            name="azure-text-embedding-ada-002",
            provider="azureopenai",
            model="text-embedding-ada-002",
            resource_name="test-resource",
            api_version="2024-02-15-preview",
        )
        mock_get_config.return_value = mock_model_config

        chunks = [
            ChunkInfo(
                chunk_id="chunk_1",
                text="Test content",
                token_count=3,
                start_index=0,
                end_index=12,
            ),
        ]

        # This should raise RuntimeError with clear configuration guidance
        with pytest.raises(RuntimeError) as exc_info:
            await generate_embeddings_activity(chunks, "azure-text-embedding-ada-002", 64)

        # Verify the error message is helpful and mentions the model
        error_message = str(exc_info.value)
        assert "azure-text-embedding-ada-002" in error_message
        assert (
            "Failed to configure" in error_message
            or "config.yaml" in error_message
            or "API key not found" in error_message
        )

    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test-key"}, clear=False)
    @patch("awa.core.utils.config_loader.ConfigLoader.get_config")
    @patch("awa.core.activities.generate_embeddings._validate_embedding_model")
    @patch("awa.core.activities.generate_embeddings._get_azure_openai_client_from_model_config")
    @patch("awa.core.activities.generate_embeddings._get_embedding_model_config")
    async def test_generate_embeddings_activity_azure_openai_model_name_handling(
        self,
        mock_get_config: Mock,
        mock_get_client: Mock,
        mock_validate: Mock,
        mock_config_loader: Mock,
    ) -> None:
        """Test that Azure OpenAI model names are handled correctly (azure- prefix removal)."""
        from awa.core.models.config.model_config import ModelConfig

        # Mock the embedding model config
        mock_model_config = ModelConfig(
            name="azure-text-embedding-ada-002",
            provider="azureopenai",
            model="text-embedding-ada-002",
            resource_name="test-resource",
            api_version="2024-02-15-preview",
        )

        # Configure mock to return config for the specific model name
        def get_config_side_effect(model_name: str | None = None) -> ModelConfig | None:
            if model_name == "azure-text-embedding-ada-002":
                return mock_model_config
            return None

        mock_get_config.side_effect = get_config_side_effect

        # Mock validation to not raise exceptions
        mock_validate.return_value = None

        # Mock config loader to avoid real config loading
        mock_config_loader.return_value = Mock()

        # Mock Azure OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_embedding = Mock()
        mock_embedding.embedding = [0.1] * 1536
        mock_response.data = [mock_embedding]
        mock_client.embeddings.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        chunks = [ChunkInfo(chunk_id="chunk_1", text="Test content", token_count=3, start_index=0, end_index=12)]

        # Test with azure- prefix
        await generate_embeddings_activity(chunks, "azure-text-embedding-ada-002", 128)

        # Verify that the azure- prefix was removed for the API call
        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-ada-002",  # azure- prefix removed
            input=["Test content"],
        )

    def test_embedding_model_validation_comprehensive(self) -> None:
        """Test comprehensive embedding model validation."""
        # Test all supported models
        supported_models = [
            "tfidf-svd",
            "text-embedding-ada-002",
            "azure-text-embedding-ada-002",
        ]

        for model in supported_models:
            _validate_embedding_model(model)  # Should not raise

        # Test invalid models
        invalid_models = [
            "invalid-model",
            "text-embedding-invalid",
            "azure-text-embedding-invalid",
            "tfidf-invalid",
        ]

        for model in invalid_models:
            with pytest.raises(ValueError, match="Unsupported embedding model"):
                _validate_embedding_model(model)

    @patch("awa.core.activities.generate_embeddings.TfidfVectorizer")
    @patch("awa.core.activities.generate_embeddings.TruncatedSVD")
    @patch("awa.core.activities.generate_embeddings.np")
    async def test_generate_embeddings_activity_tfidf_success(
        self,
        mock_np: Mock,
        mock_svd: Mock,
        mock_tfidf: Mock,
    ) -> None:
        """Test successful TF-IDF embedding generation."""
        # Mock the TF-IDF and SVD components
        mock_vectorizer = Mock()
        mock_vectorizer.fit_transform.return_value = Mock(shape=(1, 100))
        mock_tfidf.return_value = mock_vectorizer

        mock_svd_instance = Mock()
        mock_svd.return_value = mock_svd_instance
        mock_svd_instance.fit_transform.return_value = np.array([[0.1, 0.2, 0.3]])

        # Mock numpy operations properly
        mock_np.linalg.norm.return_value = np.array([[1.0]])  # 2D array with shape (1, 1)
        mock_np.where.return_value = np.array([[1.0]])  # 2D array with shape (1, 1)
        mock_np.array.return_value = np.array([[0.1, 0.2, 0.3]])

        # Test data
        chunks = [
            ChunkInfo(
                chunk_id="chunk_1",
                text="Test content",
                token_count=3,
                start_index=0,
                end_index=12,
            ),
        ]

        # Test the activity
        result = await generate_embeddings_activity(chunks, "tfidf-svd", 128)

        assert isinstance(result, EmbeddingResult)
        assert len(result.chunks) == 1
        assert result.chunks[0].embedding_vector == [0.1, 0.2, 0.3]
        assert result.actual_model == "tfidf-svd"
        assert result.actual_provider == "tfidf"
        mock_tfidf.assert_called_once()
        mock_svd.assert_called_once()

    async def test_generate_embeddings_activity_requires_model(self) -> None:
        """Test that the activity requires an embedding model to be specified."""
        chunks = [
            ChunkInfo(
                chunk_id="chunk_1",
                text="Test content",
                token_count=3,
                start_index=0,
                end_index=12,
            ),
        ]

        # When no model is specified, should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await generate_embeddings_activity(chunks, "", 128)

        assert "Embedding model is required" in str(exc_info.value)

    async def test_generate_embeddings_activity_unsupported_model_error(self) -> None:
        """Test that unsupported embedding models raise proper error."""
        # Test data
        chunks = [
            ChunkInfo(
                chunk_id="chunk_1",
                text="Test content",
                token_count=3,
                start_index=0,
                end_index=12,
            ),
        ]

        # Test that unsupported models raise Exception (the function catches ValueError and re-raises as Exception)
        with pytest.raises(Exception, match="Unsupported embedding model"):
            await generate_embeddings_activity(chunks, "unsupported-model", 128)
