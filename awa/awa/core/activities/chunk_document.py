"""Activity for chunking documents using the Chonkie library."""

from typing import Any

from chonkie import RecursiveChunker, SentenceChunker, TokenChunker
from temporalio import activity

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.sdk.constants import ACTIVITY_CHUNK_DOCUMENT
from awa.sdk.models.chunking_models import ChunkDocumentInput, ChunkDocumentOutput, ChunkerType, ChunkResult

logger = get_logger(LoggerComponent.ACTIVITY)


@activity.defn(name=ACTIVITY_CHUNK_DOCUMENT)
async def chunk_document_activity(input_data: ChunkDocumentInput) -> ChunkDocumentOutput:
    """Chunk a document using the specified Chonkie chunker.

    Args:
        input_data: Input containing content and chunker configuration

    Returns:
        ChunkDocumentOutput with list of chunks and metadata

    Raises:
        ValueError: If an unknown chunker type is specified

    """
    activity.logger.info(f"Chunking document with {input_data.chunker_type} chunker")

    # Handle empty content
    if not input_data.content:
        activity.logger.warning("Empty content provided, returning empty chunks")
        return ChunkDocumentOutput(
            chunks=[],
            total_chunks=0,
            chunker_used=input_data.chunker_type.value,
        )

    try:
        # Create the appropriate chunker
        chunker = _create_chunker(input_data)

        # Perform chunking
        chunks = chunker(input_data.content)

        # Convert to output format
        chunk_results = [
            ChunkResult(
                text=chunk.text,
                token_count=chunk.token_count,
                start_index=chunk.start_index,
                end_index=chunk.end_index,
            )
            for chunk in chunks
        ]

        activity.logger.info(f"Successfully chunked document into {len(chunk_results)} chunks")

        return ChunkDocumentOutput(
            chunks=chunk_results,
            total_chunks=len(chunk_results),
            chunker_used=input_data.chunker_type.value,
        )

    except Exception as e:
        activity.logger.error(f"Error chunking document: {e!s}")
        raise


def _create_chunker(input_data: ChunkDocumentInput) -> Any:  # noqa: ANN401
    """Create the appropriate chunker based on input configuration.

    Args:
        input_data: Input containing chunker configuration

    Returns:
        Configured chunker instance

    Raises:
        ValueError: If an unknown chunker type is specified

    """
    chunker_map = {
        ChunkerType.TOKEN: TokenChunker,
        ChunkerType.SENTENCE: SentenceChunker,
        ChunkerType.RECURSIVE: RecursiveChunker,
    }

    chunker_class = chunker_map.get(input_data.chunker_type)
    if not chunker_class:
        raise ValueError(f"Unknown chunker type: {input_data.chunker_type}")

    # Create chunker with optional parameters
    kwargs: dict[str, Any] = {}

    # Different chunkers have different parameter names
    # Most use chunk_size, but some might use max_chunk_size
    if input_data.max_chunk_size is not None:
        if input_data.chunker_type in [ChunkerType.TOKEN, ChunkerType.RECURSIVE, ChunkerType.SENTENCE]:
            kwargs["chunk_size"] = input_data.max_chunk_size
        else:
            # For other chunkers that might use different parameter names
            kwargs["max_chunk_size"] = input_data.max_chunk_size

    if input_data.chunk_overlap is not None:
        kwargs["chunk_overlap"] = input_data.chunk_overlap

    try:
        return chunker_class(**kwargs)
    except TypeError as e:
        # Some chunkers might not accept all parameters
        activity.logger.warning(
            f"Chunker {input_data.chunker_type} doesn't accept all provided parameters: {e}. "
            "Creating with default parameters.",
        )
        return chunker_class()
