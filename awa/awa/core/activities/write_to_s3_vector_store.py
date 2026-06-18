"""Activity for writing embeddings to S3 Vector Store."""

from datetime import UTC, datetime
from typing import Any

from temporalio import activity

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.vector_ingestion_output import ChunkInfo
from awa.core.utils.config_loader import ConfigLoader
from awa.core.utils.s3_vector_store import S3VectorStore
from awa.sdk import constants as sdk_constants

logger = get_logger(LoggerComponent.ACTIVITY)


def _raise_no_embeddings_error() -> None:
    """Raise error when no chunks with embeddings are provided."""
    raise ValueError("No chunks with embeddings provided")


@activity.defn(name=sdk_constants.ACTIVITY_WRITE_TO_S3_VECTOR_STORE)
async def write_to_s3_vector_store_activity(
    chunks: list[ChunkInfo],
    index_name: str | None = None,
    create_index: bool = True,
    batch_size: int = 100,
) -> dict[str, Any]:
    """Write embeddings to S3 Vector Store.

    This activity takes embedded chunks and writes them to an S3 Vector Store index.
    It can optionally create the index if it doesn't exist.

    Args:
        chunks: List of ChunkInfo objects with embeddings
        index_name: Name of the index (uses config default if None)
        create_index: Whether to create the index if it doesn't exist
        batch_size: Number of vectors to write per batch

    Returns:
        Dictionary with operation results including:
            - vectors_written: Number of vectors written
            - index_name: Name of the index used
            - created_index: Whether a new index was created

    Raises:
        RuntimeError: If writing to S3 Vector Store fails

    """
    activity.logger.info(f"Writing {len(chunks)} chunks to S3 Vector Store")

    try:
        # Load configuration
        app_config = ConfigLoader.get_config()
        if not app_config.s3_vector or not app_config.s3_vector.enabled:
            activity.logger.warning("S3 Vector Store is not enabled in configuration, skipping write")
            return {
                "vectors_written": 0,
                "index_name": None,
                "created_index": False,
                "skipped": True,
                "reason": "S3 Vector Store not enabled",
            }

        # Initialize S3 Vector Store
        s3_store = S3VectorStore(app_config.s3_vector)
        index_name = index_name or app_config.s3_vector.index_name

        # Create index if needed
        created_index = False
        if create_index:
            # Get embedding dimension from first chunk
            if not chunks or not hasattr(chunks[0], "embedding_vector"):
                _raise_no_embeddings_error()

            dimension = len(chunks[0].embedding_vector)
            activity.logger.info(f"Creating index '{index_name}' with dimension {dimension}")

            s3_store.create_index_if_not_exists(
                index_name=index_name,
                dimension=dimension,
            )
            created_index = True

        # Prepare vectors for insertion
        vectors = []
        for i, chunk in enumerate(chunks):
            if not hasattr(chunk, "embedding_vector") or not chunk.embedding_vector:
                activity.logger.warning(f"Chunk {i} has no embedding, skipping")
                continue

            # Create unique key for the vector
            chunk_key = f"{chunk.file_path}_{chunk.chunk_id}" if hasattr(chunk, "file_path") else f"chunk_{i}"

            # Prepare metadata
            metadata = {
                "source_text": chunk.text if hasattr(chunk, "text") else "",
                "file_path": chunk.file_path if hasattr(chunk, "file_path") else "",
                "chunk_id": chunk.chunk_id if hasattr(chunk, "chunk_id") else i,
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "embedding_model": app_config.s3_vector.embedding_source,
            }

            # Add any additional metadata from the chunk
            if hasattr(chunk, "metadata") and isinstance(chunk.metadata, dict):
                metadata.update(chunk.metadata)

            vectors.append(
                {
                    "key": chunk_key,
                    "embedding": chunk.embedding_vector,
                    "metadata": metadata,
                },
            )

        # Write vectors in batches
        if vectors:
            activity.logger.info(f"Writing {len(vectors)} vectors to index '{index_name}'")
            responses = s3_store.batch_put_vectors(vectors, batch_size=batch_size, index_name=index_name)
            activity.logger.info(f"Successfully wrote {len(vectors)} vectors in {len(responses)} batches")
        else:
            activity.logger.warning("No vectors to write")

        return {
            "vectors_written": len(vectors),
            "index_name": index_name,
            "created_index": created_index,
            "skipped": False,
        }

    except Exception as e:
        activity.logger.exception("Error writing to S3 Vector Store")
        raise RuntimeError(f"Failed to write to S3 Vector Store: {e}") from e
