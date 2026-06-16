"""Workflow for chunking documents using the Chonkie library."""

from datetime import timedelta

from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models.chunking_models import ChunkDocumentInput, ChunkDocumentOutput


@workflow.defn(name=constants.WORKFLOW_CHUNK_DOCUMENT)
class ChunkDocumentWorkflow:
    """A workflow that chunks documents into smaller pieces using various strategies.

    This workflow takes document content and chunking parameters as input and returns
    the chunked output by calling the chunk_document activity. It serves as a wrapper
    that allows for future enhancement such as caching, batch processing, or
    multi-step chunking strategies.

    The workflow supports three chunking strategies:
    - TOKEN: Fixed-size token chunks
    - SENTENCE: Splits by sentences
    - RECURSIVE: Hierarchical, semantically meaningful chunks (default)
    """

    @workflow.run
    async def run(self, workflow_input: ChunkDocumentInput) -> ChunkDocumentOutput:
        """Execute the document chunking workflow.

        Args:
            workflow_input: A ChunkDocumentInput object containing:
                - content: The text content to be chunked
                - chunker_type: The type of chunker to use (default: RECURSIVE)
                - max_chunk_size: Maximum size of each chunk in tokens (optional)
                - chunk_overlap: Number of tokens to overlap between chunks (optional)

        Returns:
            A ChunkDocumentOutput object containing:
                - chunks: List of chunks with text, token count, and position info
                - total_chunks: Total number of chunks created
                - chunker_used: The chunker type that was used

        """
        workflow.logger.info(
            f"Starting document chunking with {workflow_input.chunker_type} chunker "
            f"for content of length {len(workflow_input.content)}",
        )

        # Call the chunk document activity
        result = await workflow.execute_activity(
            constants.ACTIVITY_CHUNK_DOCUMENT,
            workflow_input,
            start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
        )

        workflow.logger.info(f"Document chunked into {result['total_chunks']} chunks")

        # Return the result as ChunkDocumentOutput
        return ChunkDocumentOutput.model_validate(result)
