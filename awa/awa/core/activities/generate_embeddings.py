"""Activity for generating embeddings from text chunks."""

import os

import numpy as np
from openai import AzureOpenAI, OpenAI
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from temporalio import activity

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.config.model_config import ModelConfig
from awa.core.models.vector_ingestion_output import ChunkInfo, EmbeddingResult
from awa.core.utils.config_loader import ConfigLoader
from awa.sdk import constants as sdk_constants

logger = get_logger(LoggerComponent.ACTIVITY)


def _get_openai_client() -> OpenAI:
    """Get OpenAI client with API key from environment or config.

    Returns:
        OpenAI: Configured OpenAI client

    Raises:
        ValueError: If OpenAI API key is not configured

    """
    # First try to get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        # Try to get from config
        try:
            config = ConfigLoader.get_config()
            if (
                hasattr(config, "llm")
                and hasattr(config.llm, "providers")
                and hasattr(config.llm.providers, "openai")
                and config.llm.providers.openai
            ):
                # For OpenAI, the API key is typically in environment, but we can check config
                api_key = os.getenv("OPENAI_API_KEY")
        except (ValueError, AttributeError, ImportError) as e:
            logger.warning(f"Could not load config for OpenAI API key: {e}")

    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please set OPENAI_API_KEY environment variable or configure in config.yaml",
        )

    return OpenAI(api_key=api_key)


def _get_azure_openai_client_from_model_config(model_config: ModelConfig) -> AzureOpenAI:
    """Get Azure OpenAI client using ModelConfig.

    Args:
        model_config: ModelConfig with Azure OpenAI settings

    Returns:
        AzureOpenAI: Configured Azure OpenAI client

    Raises:
        ValueError: If Azure OpenAI configuration is incomplete

    """
    # Get API key from environment
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "Azure OpenAI API key not found. Please set AZURE_OPENAI_API_KEY environment variable",
        )

    # Get required fields from model config
    if not model_config.resource_name:
        raise ValueError(
            f"Azure OpenAI resource_name not found in config for model {model_config.name}. "
            "Please add resource_name to your embedding model configuration.",
        )

    if not model_config.api_version:
        raise ValueError(
            f"Azure OpenAI api_version not found in config for model {model_config.name}. "
            "Please add api_version to your embedding model configuration.",
        )

    # Determine domain with proper precedence: model -> provider -> default
    domain = model_config.domain
    if not domain:
        # Fallback to provider-level domain if available
        try:
            config = ConfigLoader.get_config()
            if config.llm.providers.azure_openai:
                domain = config.llm.providers.azure_openai.domain
        except (ValueError, AttributeError, ImportError):
            # If config access fails, use default
            logger.warning("Could not load config for Azure OpenAI domain; defaulting to openai.azure.com")
    # Final fallback to default
    domain = domain or "openai.azure.com"

    # Create Azure OpenAI client
    return AzureOpenAI(
        api_key=api_key,
        base_url=f"https://{model_config.resource_name}.{domain}/openai/deployments/{model_config.model}",
        api_version=model_config.api_version,
    )


def _validate_chunk_format(chunk: ChunkInfo | dict) -> None:
    """Validate that a chunk has the expected format.

    Args:
        chunk: Chunk to validate

    Raises:
        ValueError: If chunk format is invalid

    """
    if not (hasattr(chunk, "text") or (isinstance(chunk, dict) and "text" in chunk)):
        raise ValueError(f"Invalid chunk format: {chunk}")


def _get_embedding_model_config(model_name: str | None = None) -> ModelConfig | None:
    """Get embedding model configuration from config.

    Args:
        model_name: Name of the embedding model to get config for.
                   If None, returns the first available embedding model.

    Returns:
        ModelConfig or None if no embedding models configured

    """
    try:
        config = ConfigLoader.get_config()
        if hasattr(config, "llm") and hasattr(config.llm, "embedding_models"):
            embedding_models = config.llm.embedding_models
            if embedding_models:
                if model_name:
                    # Find specific model by name
                    for model in embedding_models:
                        if model.name == model_name:
                            return model
                else:
                    # Return first available embedding model
                    return embedding_models[0]
    except (ValueError, AttributeError, ImportError) as e:
        logger.warning(f"Could not load embedding model config: {e}")
    return None


def _validate_embedding_model(embedding_model: str) -> None:
    """Validate that the embedding model is supported.

    Args:
        embedding_model: Name of the embedding model to validate

    Raises:
        ValueError: If the embedding model is not supported

    """
    # Check if model is configured in config.yaml
    model_config = _get_embedding_model_config(embedding_model)
    if model_config:
        return  # Model found in config

    # Fallback to hardcoded supported models
    supported_models = {
        "tfidf-svd",
        "text-embedding-ada-002",
        "text-embedding-3-small",
        "text-embedding-3-large",
        "azure-text-embedding-ada-002",
    }
    if embedding_model not in supported_models:
        raise ValueError(
            f"Unsupported embedding model: {embedding_model}. "
            f"Please configure the model in config.yaml under llm.embedding_models "
            f"or use one of the supported models: 'tfidf-svd' (default), 'text-embedding-ada-002', "
            f"'text-embedding-3-small', 'text-embedding-3-large', "
            f"'azure-text-embedding-ada-002'",
        )


async def _generate_openai_embeddings(
    texts: list[str],
    embedding_model: str,
    vector_dimension: int,
    client: OpenAI | None = None,
) -> np.ndarray:
    """Generate embeddings using OpenAI API.

    Args:
        texts: List of text chunks to embed
        embedding_model: OpenAI embedding model name
        vector_dimension: Target dimension for embeddings
        client: OpenAI client instance (if None, will create one)

    Returns:
        np.ndarray: Embedding vectors with shape (len(texts), vector_dimension)

    Raises:
        RuntimeError: If OpenAI API call fails

    """
    try:
        if client is None:
            client = _get_openai_client()

        # OpenAI embeddings are typically 1536 dimensions for text-embedding-ada-002
        # or 3072 for text-embedding-3-large, so we may need to truncate
        embeddings = []

        # Process texts in batches to avoid rate limits
        batch_size = 100  # OpenAI can handle up to 100 texts per request

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            try:
                response = client.embeddings.create(
                    model=embedding_model,
                    input=batch_texts,
                )

                batch_embeddings = [embedding.embedding for embedding in response.data]
                embeddings.extend(batch_embeddings)

                logger.info(
                    f"Generated embeddings for batch "
                    f"{i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}",
                )

            except Exception as e:
                logger.exception(f"Error generating embeddings for batch {i // batch_size + 1}")
                raise RuntimeError(f"OpenAI API error for batch {i // batch_size + 1}: {e}") from e

        # Convert to numpy array
        embeddings_array = np.array(embeddings)

        # Truncate or pad to match requested dimension
        if embeddings_array.shape[1] > vector_dimension:
            # Truncate to requested dimension
            embeddings_array = embeddings_array[:, :vector_dimension]
            logger.info(
                f"Truncated OpenAI embeddings from {embeddings_array.shape[1]} to {vector_dimension} dimensions",
            )
        elif embeddings_array.shape[1] < vector_dimension:
            # Pad with zeros to requested dimension
            padded_embeddings = np.zeros((embeddings_array.shape[0], vector_dimension))
            padded_embeddings[:, : embeddings_array.shape[1]] = embeddings_array
            embeddings_array = padded_embeddings
            logger.info(
                f"Padded OpenAI embeddings from {embeddings_array.shape[1]} to {vector_dimension} dimensions",
            )

        # Normalize embeddings to unit vectors
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        embeddings_array = embeddings_array / norms

        return embeddings_array

    except Exception as e:
        logger.exception("Error in OpenAI embeddings generation")
        raise RuntimeError(f"Failed to generate OpenAI embeddings: {e}") from e


async def _generate_azure_openai_embeddings(
    texts: list[str],
    embedding_model: str,
    vector_dimension: int,
    client: AzureOpenAI | None = None,
) -> np.ndarray:
    """Generate embeddings using Azure OpenAI API.

    Args:
        texts: List of text chunks to embed
        embedding_model: Azure OpenAI embedding model name
        vector_dimension: Target dimension for embeddings
        client: Azure OpenAI client instance (if None, will create one)

    Returns:
        np.ndarray: Embedding vectors with shape (len(texts), vector_dimension)

    Raises:
        RuntimeError: If Azure OpenAI API call fails

    """
    if client is None:
        raise ValueError("Azure OpenAI client is required but not provided")

    try:
        # Azure OpenAI embeddings are typically 1536 dimensions for text-embedding-ada-002
        # or 3072 for text-embedding-3-large, so we may need to truncate
        embeddings = []

        # Process texts in batches to avoid rate limits
        batch_size = 100  # Azure OpenAI can handle up to 100 texts per request

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            try:
                response = client.embeddings.create(
                    model=embedding_model,
                    input=batch_texts,
                )

                batch_embeddings = [embedding.embedding for embedding in response.data]
                embeddings.extend(batch_embeddings)

                logger.info(
                    f"Generated Azure OpenAI embeddings for batch "
                    f"{i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}",
                )

            except Exception as e:
                logger.exception(f"Error generating Azure OpenAI embeddings for batch {i // batch_size + 1}")
                raise RuntimeError(f"Azure OpenAI API error for batch {i // batch_size + 1}: {e}") from e

        # Convert to numpy array
        embeddings_array = np.array(embeddings)

        # Truncate or pad to match requested dimension
        if embeddings_array.shape[1] > vector_dimension:
            # Truncate to requested dimension
            embeddings_array = embeddings_array[:, :vector_dimension]
            logger.info(
                f"Truncated Azure OpenAI embeddings from {embeddings_array.shape[1]} to {vector_dimension} dimensions",
            )
        elif embeddings_array.shape[1] < vector_dimension:
            # Pad with zeros to requested dimension
            padded_embeddings = np.zeros((embeddings_array.shape[0], vector_dimension))
            padded_embeddings[:, : embeddings_array.shape[1]] = embeddings_array
            embeddings_array = padded_embeddings
            logger.info(
                f"Padded Azure OpenAI embeddings from {embeddings_array.shape[1]} to {vector_dimension} dimensions",
            )

        # Normalize embeddings to unit vectors
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        embeddings_array = embeddings_array / norms

        return embeddings_array

    except Exception as e:
        logger.exception("Error in Azure OpenAI embeddings generation")
        raise RuntimeError(f"Failed to generate Azure OpenAI embeddings: {e}") from e


def _extract_texts_from_chunks(chunks: list[ChunkInfo]) -> list[str]:
    """Extract text content from chunks for embedding."""
    texts = []
    for chunk in chunks:
        try:
            _validate_chunk_format(chunk)
            if hasattr(chunk, "text"):
                texts.append(chunk.text)
            elif isinstance(chunk, dict) and "text" in chunk:
                texts.append(chunk["text"])
        except ValueError as e:
            raise ValueError(f"Invalid chunk format: {chunk}") from e
    return texts


def _update_chunks_with_embeddings(chunks: list[ChunkInfo], embeddings: np.ndarray) -> None:
    """Update chunks with their corresponding embeddings."""
    for chunk, embedding in zip(chunks, embeddings, strict=False):
        if hasattr(chunk, "embedding_vector"):
            chunk.embedding_vector = embedding.tolist()
        elif isinstance(chunk, dict) and "embedding_vector" in chunk:
            chunk["embedding_vector"] = embedding.tolist()
        else:
            try:
                chunk.embedding_vector = embedding.tolist()
            except AttributeError:
                if isinstance(chunk, dict):
                    chunk["embedding_vector"] = embedding.tolist()
                else:
                    raise TypeError(f"Cannot set embedding_vector on chunk: {chunk}") from None


async def _generate_tfidf_svd_embeddings(texts: list[str], vector_dimension: int) -> np.ndarray:
    """Generate embeddings using TF-IDF + SVD approach."""
    activity.logger.info(f"Using TF-IDF + SVD with {vector_dimension} dimensions")

    vectorizer = TfidfVectorizer(
        max_features=min(1000, max(100, len(texts) * 5)),
        stop_words="english",
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_df=1.0,
        token_pattern=r"(?u)\b\w+\b",  # noqa: S106
    )

    tfidf_matrix = vectorizer.fit_transform(texts)
    activity.logger.info(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

    actual_dimension = min(tfidf_matrix.shape[1], vector_dimension)
    if tfidf_matrix.shape[1] < vector_dimension:
        activity.logger.warning(
            f"TF-IDF matrix has {tfidf_matrix.shape[1]} features, but requested "
            f"{vector_dimension} dimensions. Using {actual_dimension} dimensions instead.",
        )

    svd = TruncatedSVD(n_components=actual_dimension, random_state=42)
    embeddings = svd.fit_transform(tfidf_matrix)

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    embeddings = embeddings / norms

    activity.logger.info(f"Generated embeddings with shape: {embeddings.shape}")
    return embeddings


async def _get_embedding_provider(embedding_model: str) -> tuple[str, object | None, str]:
    """Determine embedding provider and get client if needed.

    Args:
        embedding_model: Name of the embedding model

    Returns:
        Tuple of (provider_type, client_or_none, actual_model_name) where provider_type is one of:
        - "openai": OpenAI embeddings
        - "azure": Azure OpenAI embeddings
        - "azureopenai": Azure OpenAI embeddings (from config)
        - "tfidf": Local TF-IDF embeddings (no client needed)

    Raises:
        RuntimeError: If the requested embedding model cannot be configured properly

    """
    if embedding_model == "tfidf-svd":
        return "tfidf", None, embedding_model

    # Check if model is configured in config.yaml
    model_config = _get_embedding_model_config(embedding_model)
    if model_config:
        provider = (
            model_config.provider.value if hasattr(model_config.provider, "value") else str(model_config.provider)
        )
        actual_model_name = model_config.model

        if provider.lower() == "azureopenai":
            try:
                # Use model config directly for Azure OpenAI
                client = _get_azure_openai_client_from_model_config(model_config)
                return "azureopenai", client, actual_model_name
            except ValueError as e:
                activity.logger.error(
                    f"Azure OpenAI configuration error for model '{embedding_model}': {e}. "
                    f"Please check your embedding model configuration in config.yaml and set AZURE_OPENAI_API_KEY.",
                )
                raise RuntimeError(
                    f"Failed to configure Azure OpenAI embedding model '{embedding_model}': {e}. "
                    f"Please verify your configuration and API key.",
                ) from e
        elif provider.lower() == "openai":
            try:
                client = _get_openai_client()
                return "openai", client, actual_model_name
            except ValueError as e:
                activity.logger.error(
                    f"OpenAI API key not found for model '{embedding_model}'. "
                    f"Set OPENAI_API_KEY environment variable to use {embedding_model}",
                )
                raise RuntimeError(
                    f"Failed to configure OpenAI embedding model '{embedding_model}': missing API key. "
                    f"Please set OPENAI_API_KEY environment variable.",
                ) from e

    # For legacy Azure model names without config, provide clear error
    if embedding_model.startswith("azure-text-embedding"):
        error_msg = (
            f"Azure model '{embedding_model}' is not configured in config.yaml. "
            f"Please add this model to the embedding_models section in your config.yaml file. "
            f"Example configuration:\n"
            f"embedding_models:\n"
            f"  - name: {embedding_model}\n"
            f"    provider: azureopenai\n"
            f"    resource_name: your-azure-resource-name\n"
            f'    api_version: "2023-05-15"\n'
            f"    model: {embedding_model.replace('azure-', '')}"
        )
        activity.logger.error(error_msg)
        raise RuntimeError(error_msg)

    if embedding_model.startswith("text-embedding"):
        try:
            client = _get_openai_client()
            return "openai", client, embedding_model
        except ValueError as e:
            activity.logger.error(
                f"OpenAI API key not found for model '{embedding_model}'. "
                f"Set OPENAI_API_KEY environment variable to use {embedding_model}",
            )
            raise RuntimeError(
                f"Failed to configure OpenAI embedding model '{embedding_model}': missing API key. "
                f"Please set OPENAI_API_KEY environment variable.",
            ) from e

    # If we reach here, the model is not supported
    error_msg = (
        f"Unsupported embedding model: '{embedding_model}'. "
        f"Supported models: 'tfidf-svd' (local), OpenAI models ('text-embedding-*'), "
        f"or Azure OpenAI models (configured in config.yaml under embedding_models)."
    )
    activity.logger.error(error_msg)
    raise RuntimeError(error_msg)


async def _generate_embeddings_by_provider(
    provider: str,
    client: object | None,
    texts: list[str],
    embedding_model: str,
    vector_dimension: int,
) -> np.ndarray:
    """Generate embeddings based on provider type.

    Args:
        provider: Provider type ("openai", "azure", "azureopenai", or "tfidf")
        client: API client for the provider (None for tfidf)
        texts: List of texts to embed
        embedding_model: Model name (actual model name, not the config name)
        vector_dimension: Target embedding dimension

    Returns:
        Numpy array of embeddings

    """
    if provider == "openai":
        activity.logger.info(f"Using OpenAI {embedding_model} with {vector_dimension} dimensions")
        return await _generate_openai_embeddings(texts, embedding_model, vector_dimension, client)

    if provider in ["azure", "azureopenai"]:
        activity.logger.info(f"Using Azure OpenAI {embedding_model} with {vector_dimension} dimensions")
        return await _generate_azure_openai_embeddings(texts, embedding_model, vector_dimension, client)

    if provider == "tfidf":
        return await _generate_tfidf_svd_embeddings(texts, vector_dimension)

    # If we reach here, provider is invalid
    raise RuntimeError(f"Unknown embedding provider: {provider}. This should not happen.")


@activity.defn(name=sdk_constants.ACTIVITY_GENERATE_EMBEDDINGS)
async def generate_embeddings_activity(
    chunks: list[ChunkInfo],
    embedding_model: str,  # Required parameter - no default
    vector_dimension: int = 128,
    model_cache_dir: str | None = None,  # noqa: ARG001
) -> EmbeddingResult:
    """Generate embeddings for text chunks using TF-IDF + SVD, OpenAI, or Azure OpenAI.

    This activity takes a list of text chunks and generates embeddings for each one
    using either TF-IDF vectorization followed by dimensionality reduction with SVD
    (default, runs locally), OpenAI's embedding API, or Azure OpenAI's embedding API.

    Args:
        chunks: List of ChunkInfo objects containing text to embed
        embedding_model: (REQUIRED) Name of the embedding model to use. Must be one of:
            - "tfidf-svd": Local TF-IDF + SVD approach
            - "text-embedding-ada-002": OpenAI's Ada embedding model
            - "text-embedding-3-small": OpenAI's 3-Small embedding model
            - "text-embedding-3-large": OpenAI's 3-Large embedding model
            - Azure OpenAI models configured in config.yaml under 'embedding_models'
        vector_dimension: Dimension of the final embedding vectors
        model_cache_dir: Directory to cache models (optional, not used for TF-IDF, OpenAI, or Azure OpenAI)

    Returns:
        EmbeddingResult containing chunks with embeddings and metadata about actual model used

    Raises:
        RuntimeError: If embedding generation fails

    """
    # Embedding model is now required - no defaults
    if not embedding_model:
        raise ValueError("Embedding model is required. Please specify an embedding model.")

    activity.logger.info(f"Generating embeddings for {len(chunks)} chunks using {embedding_model}")

    try:
        # Extract texts and validate model upfront
        texts = _extract_texts_from_chunks(chunks)
        _validate_embedding_model(embedding_model)

        # Determine provider and get client (will raise RuntimeError if configuration fails)
        provider, client, actual_model_name = await _get_embedding_provider(embedding_model)

        activity.logger.info(f"Using {provider} provider with model: {actual_model_name}")

        # Generate embeddings using the appropriate provider
        embeddings = await _generate_embeddings_by_provider(
            provider,
            client,
            texts,
            actual_model_name,  # Use the actual model name from provider
            vector_dimension,
        )

        # Update chunks with embeddings
        _update_chunks_with_embeddings(chunks, embeddings)
        activity.logger.info(
            f"Successfully generated embeddings for {len(chunks)} chunks using {provider}:{actual_model_name}",
        )

        return EmbeddingResult(
            chunks=chunks,
            actual_model=actual_model_name,
            actual_provider=provider,
        )

    except Exception as e:
        activity.logger.exception("Error generating embeddings")
        raise RuntimeError(f"Failed to generate embeddings: {e}") from e
