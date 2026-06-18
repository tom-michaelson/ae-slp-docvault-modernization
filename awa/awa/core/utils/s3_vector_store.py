"""S3 Vector Store utilities for managing vector indices and embeddings."""

from datetime import UTC, datetime
from typing import Any, Literal

import boto3
from botocore.exceptions import ClientError

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.config.s3_vector_config import S3VectorConfig
from awa.core.utils.config_loader import ConfigLoader

logger = get_logger(LoggerComponent.ACTIVITY)

# Embedding model dimensions
EMBEDDING_DIMENSIONS = {
    "openai": {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    },
    "azure_openai": {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    },
    "tfidf": None,  # Variable dimension based on vocabulary
}


class S3VectorStore:
    """Manage S3 Vector Store operations including index creation and vector insertion."""

    def __init__(self, config: S3VectorConfig | None = None) -> None:
        """Initialize S3 Vector Store client.

        Args:
            config: S3 Vector configuration. If None, loads from config.yaml

        """
        if config is None:
            app_config = ConfigLoader.load_config()
            config = app_config.s3_vector
            if config is None or not config.enabled:
                raise ValueError("S3 Vector Store is not enabled in configuration")

        self.config = config
        self.s3vectors = boto3.client("s3vectors", region_name=config.region_name)

    def get_embedding_dimension(self, embedding_source: str, model_name: str | None = None) -> int:
        """Get the dimension for the embedding model.

        Args:
            embedding_source: Source of embeddings (openai, azure_openai, tfidf)
            model_name: Specific model name

        Returns:
            Embedding dimension

        Raises:
            ValueError: If dimension cannot be determined

        """
        if embedding_source == "tfidf":
            # TF-IDF dimension is determined at runtime
            raise ValueError("TF-IDF dimension must be provided explicitly")

        if embedding_source in EMBEDDING_DIMENSIONS:
            models = EMBEDDING_DIMENSIONS[embedding_source]
            if isinstance(models, dict):
                if model_name and model_name in models:
                    return models[model_name]
                # Default to ada-002 if model not specified
                return models.get("text-embedding-ada-002", 1536)

        raise ValueError(f"Unknown embedding source: {embedding_source}")

    def create_index_if_not_exists(
        self,
        index_name: str | None = None,
        dimension: int | None = None,
        data_type: Literal["float32"] | None = None,
        distance_metric: Literal["euclidean", "cosine"] | None = None,
        metadata_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a vector index if it doesn't already exist.

        Args:
            index_name: Name of the index (uses config default if None)
            dimension: Dimension of vectors (auto-detected if None)
            data_type: Data type for vectors (uses config default if None)
            distance_metric: Distance metric (uses config default if None)
            metadata_keys: Metadata keys (uses config default if None)

        Returns:
            Response from create_index or existing index details

        """
        index_name = index_name or self.config.index_name
        data_type = data_type or self.config.data_type
        distance_metric = distance_metric or self.config.distance_metric
        metadata_keys = metadata_keys or self.config.metadata_keys

        # Auto-detect dimension if not provided
        if dimension is None:
            if self.config.embedding_source != "tfidf":
                # Get dimension from configured embedding model
                app_config = ConfigLoader.load_config()
                if self.config.embedding_source == "azure_openai":
                    # Find the Azure OpenAI embedding model
                    for model in app_config.llm.embedding_models:
                        if model.provider == "azureopenai":
                            dimension = self.get_embedding_dimension("azure_openai", model.model)
                            break
                elif self.config.embedding_source == "openai":
                    # Find the OpenAI embedding model
                    for model in app_config.llm.embedding_models:
                        if model.provider == "openai":
                            dimension = self.get_embedding_dimension("openai", model.model)
                            break

            if dimension is None:
                raise ValueError("Cannot determine embedding dimension. Please provide it explicitly.")

        try:
            # Check if index already exists
            response = self.s3vectors.get_index(
                vectorBucketName=self.config.vector_bucket_name,
                indexName=index_name,
            )
            logger.info(f"Index '{index_name}' already exists in bucket '{self.config.vector_bucket_name}'")
            return response

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ["ResourceNotFoundException", "NotFoundException"]:
                # Index doesn't exist, create it
                logger.info(
                    f"Creating new index '{index_name}' in bucket '{self.config.vector_bucket_name}' "
                    f"with dimension {dimension}",
                )

                create_params = {
                    "vectorBucketName": self.config.vector_bucket_name,
                    "indexName": index_name,
                    "dataType": data_type,
                    "dimension": dimension,
                    "distanceMetric": distance_metric,
                }

                # Add ARN if provided
                if self.config.vector_bucket_arn:
                    create_params["vectorBucketArn"] = self.config.vector_bucket_arn

                # Add metadata configuration
                if metadata_keys:
                    create_params["metadataConfiguration"] = {
                        "nonFilterableMetadataKeys": metadata_keys,
                    }

                response = self.s3vectors.create_index(**create_params)
                logger.info(f"Successfully created index '{index_name}'")
                return response
            logger.exception("Error checking/creating index")
            raise

    def put_vectors(
        self,
        vectors: list[dict[str, Any]],
        index_name: str | None = None,
    ) -> dict[str, Any]:
        """Insert vectors into the specified index.

        Args:
            vectors: List of vector dictionaries containing:
                - key: Unique identifier for the vector
                - embedding: List of float values
                - metadata: Optional metadata dictionary
            index_name: Name of the index (uses config default if None)

        Returns:
            Response from put_vectors operation

        """
        index_name = index_name or self.config.index_name

        # Transform vectors to S3 Vector format
        s3_vectors = []
        for vec in vectors:
            s3_vec = {
                "key": vec["key"],
                "data": {"float32": vec["embedding"]},
            }
            if "metadata" in vec:
                # Add timestamp and embedding model to metadata
                metadata = vec["metadata"].copy()
                metadata["timestamp"] = metadata.get("timestamp", datetime.now(tz=UTC).isoformat())
                metadata["embedding_model"] = metadata.get("embedding_model", self.config.embedding_source)
                s3_vec["metadata"] = metadata

            s3_vectors.append(s3_vec)

        try:
            response = self.s3vectors.put_vectors(
                vectorBucketName=self.config.vector_bucket_name,
                indexName=index_name,
                vectors=s3_vectors,
            )
            logger.info(f"Successfully inserted {len(vectors)} vectors into index '{index_name}'")
            return response
        except Exception:
            logger.exception("Error inserting vectors")
            raise

    def search_vectors(
        self,
        query_vector: list[float],
        top_k: int = 10,
        index_name: str | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors in the index.

        Args:
            query_vector: Query vector for similarity search
            top_k: Number of top results to return
            index_name: Name of the index (uses config default if None)
            metadata_filter: Optional metadata filter

        Returns:
            List of search results with scores and metadata

        """
        index_name = index_name or self.config.index_name

        search_params = {
            "vectorBucketName": self.config.vector_bucket_name,
            "indexName": index_name,
            "vector": {"float32": query_vector},
            "topK": top_k,
        }

        if metadata_filter:
            search_params["metadataFilter"] = metadata_filter

        try:
            response = self.s3vectors.query_vectors(**search_params)
            return response.get("matches", [])
        except Exception:
            logger.exception("Error searching vectors")
            raise

    def delete_index(self, index_name: str | None = None) -> dict[str, Any]:
        """Delete a vector index.

        Args:
            index_name: Name of the index (uses config default if None)

        Returns:
            Response from delete operation

        """
        index_name = index_name or self.config.index_name

        try:
            response = self.s3vectors.delete_index(
                vectorBucketName=self.config.vector_bucket_name,
                indexName=index_name,
            )
            logger.info(f"Successfully deleted index '{index_name}'")
            return response
        except Exception:
            logger.exception("Error deleting index")
            raise

    def batch_put_vectors(
        self,
        vectors: list[dict[str, Any]],
        batch_size: int = 100,
        index_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Insert vectors in batches for better performance.

        Args:
            vectors: List of vector dictionaries
            batch_size: Number of vectors per batch
            index_name: Name of the index

        Returns:
            List of responses from put_vectors operations

        """
        responses = []
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            response = self.put_vectors(batch, index_name)
            responses.append(response)
            logger.debug(f"Inserted batch {i // batch_size + 1} of {len(vectors) // batch_size + 1}")

        return responses
