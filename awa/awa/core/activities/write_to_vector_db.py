"""Activity for writing embeddings to a vector database."""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from temporalio import activity

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.vector_ingestion_output import ChunkInfo
from awa.sdk import constants as sdk_constants

logger = get_logger(LoggerComponent.ACTIVITY)


def _raise_unsupported_db_error(vector_db_type: str) -> None:
    """Raise error for unsupported vector database type."""
    msg = f"Unsupported vector database type: {vector_db_type}"
    raise ValueError(msg)


@activity.defn(name=sdk_constants.ACTIVITY_WRITE_TO_VECTOR_DB)
async def write_to_vector_db_activity(
    chunks: list[ChunkInfo],
    vector_db_type: str,
    vector_db_path: str | None = None,
    collection_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write embeddings to a vector database.

    This activity takes chunks with embeddings and stores them in the specified
    vector database. Currently supports ChromaDB as the default vector database.
    It creates a collection and stores the embeddings with metadata.

    Args:
        chunks: List of ChunkInfo objects with embeddings
        vector_db_type: Type of vector database to use (e.g., 'chroma')
        vector_db_path: Path to the vector database (optional)
        collection_name: Name for the collection (optional)
        metadata: Additional metadata to store with embeddings (optional)

    Returns:
        Dictionary containing database information and status

    Raises:
        ValueError: If vector database type is not supported
        Exception: If writing to database fails

    """
    activity.logger.info(f"Writing {len(chunks)} embeddings to {vector_db_type} vector database")

    # Set default paths and names
    if not vector_db_path:
        vector_db_path = f"./{vector_db_type}_db"

    if not collection_name:
        collection_name = f"documents_{datetime.now(tz=UTC).strftime('%Y%m%d_%H%M%S')}"

    if not metadata:
        metadata = {}

    try:
        if vector_db_type.lower() == "chroma":
            return await _write_to_chromadb(chunks, vector_db_path, collection_name, metadata)
        _raise_unsupported_db_error(vector_db_type)

    except Exception as e:
        activity.logger.error(f"Error writing to vector database: {e}")
        raise RuntimeError(f"Failed to write to vector database: {e}") from e


async def _write_to_chromadb(
    chunks: list[ChunkInfo],
    db_path: str,
    collection_name: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Write embeddings to ChromaDB.

    Args:
        chunks: List of chunks with embeddings
        db_path: Path to ChromaDB database
        collection_name: Name of the collection
        metadata: Additional metadata

    Returns:
        Dictionary with database information

    """
    # Ensure database directory exists
    Path(db_path).mkdir(parents=True, exist_ok=True)

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        # Create or get collection
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata=metadata,
        )

        # Prepare data for ChromaDB
        ids = [str(uuid.uuid4()) for _ in chunks]
        texts = [chunk.text for chunk in chunks]
        embeddings = [chunk.embedding_vector for chunk in chunks if chunk.embedding_vector]

        # Prepare metadatas
        metadatas = []
        for chunk in chunks:
            chunk_metadata = {
                "chunk_id": chunk.chunk_id,
                "token_count": chunk.token_count,
                "start_index": chunk.start_index,
                "end_index": chunk.end_index,
                "processed_at": datetime.now(tz=UTC).isoformat(),
            }
            metadatas.append(chunk_metadata)

        # Add embeddings to collection
        if embeddings:
            collection.add(
                ids=ids[: len(embeddings)],
                embeddings=embeddings,
                documents=texts[: len(embeddings)],
                metadatas=metadatas[: len(embeddings)],
            )

        # Get collection info
        collection.get()

        activity.logger.info(
            f"Successfully wrote {len(embeddings)} embeddings to ChromaDB collection '{collection_name}'",
        )

        return {
            "vector_db_type": "chroma",
            "vector_db_path": db_path,
            "collection_name": collection_name,
            "total_embeddings_stored": len(embeddings),
            "collection_count": collection.count(),
            "collection_metadata": collection.metadata,
        }

    finally:
        # ChromaDB client doesn't need explicit cleanup in newer versions
        # The client is lightweight and will be garbage collected
        pass
