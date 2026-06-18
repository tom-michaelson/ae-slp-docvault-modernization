from pathlib import Path

from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models.read_file_and_parse_input import ReadFileAndParseInput


async def read_file_and_parse_workflow(
    file_path: str | Path,
    default: str | None = None,
    strict: bool = False,
) -> str:
    """Read and parse a file from a specified path, converting to markdown if supported.

    Uses MarkItDown to parse specific whitelisted document formats:
    - Documents: .pdf, .docx, .pptx, .xlsx, .xls
    - Web: .html, .htm
    - Data: .csv
    - E-books: .epub
    - Email: .msg (Outlook messages)

    All other file types (including .txt, .md, .py, etc.) are returned as-is without parsing
    when strict=False, or raise an exception when strict=True.

    Args:
        file_path: The file path to read and parse.
        default: A string to return if the file does not exist.
        strict: If True, raise exception for unsupported file types; if False, return raw content.

    Returns:
        A string containing the parsed content (markdown) for supported formats,
        or raw content for unsupported formats when strict=False.

    Raises:
        InvalidInputApplicationError: When strict=True and file type is not supported.

    """
    result = await workflow.execute_child_workflow(
        workflow=constants.WORKFLOW_READ_FILE_AND_PARSE,
        arg=ReadFileAndParseInput(
            file_path=str(file_path),
            default_content=default,
            strict=strict,
        ),
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
    )
    return result
