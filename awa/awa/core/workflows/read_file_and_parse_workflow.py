"""Read file and parse workflow that wraps the read_file_and_parse activity.

This workflow provides a simple pass-through wrapper around the read_file_and_parse
activity, enabling workflow-level orchestration of document parsing operations.
"""

from datetime import timedelta

from temporalio import workflow

# Import activities with sandboxing for determinism
with workflow.unsafe.imports_passed_through():
    from awa.core.activities.read_file_and_parse_activity import read_file_and_parse_activity
    from awa.core.logger.logger import LoggerComponent, get_logger
    from awa.sdk import constants as sdk_constants
    from awa.sdk.models.read_file_and_parse_input import ReadFileAndParseInput


@workflow.defn(name=sdk_constants.WORKFLOW_READ_FILE_AND_PARSE)
class ReadFileAndParseWorkflow:
    """Workflow that reads and parses a file using MarkItDown.

    This workflow wraps the read_file_and_parse activity to provide workflow-level
    orchestration. It simply passes through the input to the activity and returns
    the parsed output.

    The workflow supports the same file formats as the underlying activity,
    including PDF, Word, PowerPoint, Excel, HTML, CSV, JSON, XML, EPUB, and
    Outlook MSG files.

    Attributes:
        None

    Example:
        ```python
        # Execute the workflow
        result = await workflow_client.execute_workflow(
            ReadFileAndParseWorkflow.run,
            ReadFileAndParseInput(
                file_path="s3://my-bucket/document.pdf",
                default_content="No content found",
                strict=False
            ),
            id="parse-document-123",
            task_queue=TASK_QUEUE_AGENT_OPERATIONS,
        )
        print(f"Parsed content: {result}")
        ```

    """

    @workflow.run
    async def run(self, inp: ReadFileAndParseInput) -> str:
        """Execute the read file and parse workflow.

        This method orchestrates the document parsing process by calling the
        read_file_and_parse activity. It provides a workflow-level wrapper that
        can be extended in the future with additional orchestration logic.

        Args:
            inp: The workflow input containing the file path, optional
                default content, and strict mode flag.

        Returns:
            str: The parsed content of the file, or the default content
                if the file could not be read/parsed.

        Raises:
            InvalidInputApplicationError: When strict=True and file type
                is not supported.

        """
        logger = get_logger(LoggerComponent.WORKFLOW, workflow_id=workflow.info().workflow_id)
        logger.info(f"Starting document parsing workflow for: {inp.file_path} (strict={inp.strict})")

        # Execute the activity with a reasonable timeout
        result = await workflow.execute_activity(
            read_file_and_parse_activity,
            args=[inp],
            start_to_close_timeout=timedelta(seconds=300),  # 5 minutes for large files
        )

        logger.info(f"Document parsing completed. Content length: {len(result)}")
        return result
