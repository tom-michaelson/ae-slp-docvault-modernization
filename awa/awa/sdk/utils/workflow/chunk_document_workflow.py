from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models.chunking_models import ChunkDocumentInput, ChunkDocumentOutput, ChunkerType


async def chunk_document_workflow(
    content: str,
    chunker_type: ChunkerType = ChunkerType.RECURSIVE,
    max_chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> ChunkDocumentOutput:
    """Chunk a document into smaller pieces using various chunking strategies.

    This method executes the chunk document workflow which provides a consistent
    interface for document chunking across AWA. The workflow internally calls
    the chunk document activity and can be extended in the future to support
    additional features like caching or batch processing.

    Args:
        content: The text content to be chunked
        chunker_type: The type of chunker to use (TOKEN, SENTENCE, or RECURSIVE)
        max_chunk_size: Maximum size of each chunk in tokens
        chunk_overlap: Number of tokens to overlap between chunks

    Returns:
        ChunkDocumentOutput containing the chunks and metadata

    """
    input_data = ChunkDocumentInput(
        content=content,
        chunker_type=chunker_type,
        max_chunk_size=max_chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return await workflow.execute_child_workflow(
        workflow=constants.WORKFLOW_CHUNK_DOCUMENT,
        arg=input_data,
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        id=f"chunk-document-{workflow.info().workflow_id}",
    )
