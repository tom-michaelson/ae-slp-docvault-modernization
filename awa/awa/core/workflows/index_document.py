"""Index document workflow that combines parsing and chunking operations.

This workflow orchestrates the sequential execution of document parsing
and chunking operations, providing a unified interface for document indexing.
"""

from temporalio import workflow

from awa.core.decorators.exposed import exposed
from awa.sdk import constants

# Import activities and workflows with sandboxing for determinism
with workflow.unsafe.imports_passed_through():
    from awa.sdk.models.chunking_models import ChunkDocumentInput, ChunkDocumentOutput
    from awa.sdk.models.read_file_and_parse_input import ReadFileAndParseInput


@exposed("Workflow that reads, parses, and chunks a document into smaller pieces")
@workflow.defn(name=constants.WORKFLOW_INDEX_DOCUMENT)
class IndexDocumentWorkflow:
    """Workflow that combines document parsing and chunking operations.

    This workflow provides a streamlined interface for document indexing by:
    1. Reading and parsing a document from a file path
    2. Chunking the parsed content into smaller, manageable pieces

    The workflow uses default chunking parameters (recursive chunker) to ensure
    semantically meaningful chunks are created from the parsed document content.

    Attributes:
        None

    Example:
        ```python
        # Execute the workflow
        result = await workflow_client.execute_workflow(
            IndexDocumentWorkflow.run,
            ReadFileAndParseInput(
                file_path="s3://my-bucket/document.pdf",
                default_content="No content found",
                strict=False
            ),
            id="index-document-123",
            task_queue=TASK_QUEUE_AGENT_OPERATIONS,
        )
        print(f"Document chunked into {result.total_chunks} chunks")
        ```

    """

    @workflow.run
    async def run(self, inp: ReadFileAndParseInput) -> ChunkDocumentOutput:
        """Execute the document indexing workflow.

        This method orchestrates the sequential execution of document parsing
        and chunking operations. It first parses the document from the provided
        file path, then chunks the parsed content using default parameters.

        Args:
            inp: The workflow input containing the file path, optional
                default content, and strict mode flag.

        Returns:
            ChunkDocumentOutput: The chunked document output containing:
                - chunks: List of chunks with text, token count, and position info
                - total_chunks: Total number of chunks created
                - chunker_used: The chunker type that was used

        Raises:
            InvalidInputApplicationError: When strict=True and file type
                is not supported during parsing.

        """
        workflow.logger.info(f"Starting document indexing workflow for: {inp.file_path}")

        # Step 1: Read and parse the document
        workflow.logger.info("Executing document parsing workflow")
        parsed_content = await workflow.execute_child_workflow(
            constants.WORKFLOW_READ_FILE_AND_PARSE,
            args=[inp],
        )

        workflow.logger.info(f"Document parsed successfully. Content length: {len(parsed_content)}")

        # Step 2: Chunk the parsed content
        workflow.logger.info("Executing document chunking workflow")
        chunk_input = ChunkDocumentInput(
            content=parsed_content,
            # Using defaults for other parameters:
            # - chunker_type: ChunkerType.RECURSIVE (default)
            # - max_chunk_size: None (uses chunker defaults)
            # - chunk_overlap: None (uses chunker defaults)
        )

        chunk_output = await workflow.execute_child_workflow(
            constants.WORKFLOW_CHUNK_DOCUMENT,
            args=[chunk_input],
        )

        workflow.logger.info(
            f"Document indexing completed. Created {chunk_output['total_chunks']} chunks "
            f"using {chunk_output['chunker_used']} chunker",
        )

        return chunk_output
