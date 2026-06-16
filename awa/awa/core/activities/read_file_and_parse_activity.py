"""Document parsing activity using MarkItDown library."""

import tempfile
from pathlib import Path

from markitdown import MarkItDown
from temporalio import activity, workflow

from awa.core.utils.file_system_utils import FileSystemUtils

# Import necessary modules for sandboxing
with workflow.unsafe.imports_passed_through():
    from awa.core.logger.logger import LoggerComponent, get_logger
from awa.sdk import constants as sdk_constants
from awa.sdk.models.exceptions.fatal_application_error import FatalApplicationError
from awa.sdk.models.exceptions.file_extension_not_supported_error import FileExtensionNotSupportedApplicationError
from awa.sdk.models.read_file_and_parse_input import ReadFileAndParseInput

# Define extensions that are supported by MarkItDown for parsing
SUPPORTED_EXTENSIONS = {
    # Documents
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".xls",  # Excel legacy format
    # Web
    ".html",
    ".htm",
    # Data
    ".csv",
    # E-books
    ".epub",
    # Email
    ".msg",  # Outlook message files
}


@activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_AND_PARSE)
async def read_file_and_parse_activity(
    inp_or_file_path: ReadFileAndParseInput | str,
    default_content: str | None = None,
    strict: bool = False,
) -> str:
    """Read and parse a file from a specified path, converting to markdown if supported.

    This function uses MarkItDown to parse specific whitelisted document formats into markdown.
    Only files with the following extensions are parsed:
    - Documents: .pdf, .docx, .pptx, .xlsx, .xls
    - Web: .html, .htm
    - Data: .csv
    - E-books: .epub
    - Email: .msg (Outlook messages)

    All other file types (including .txt, .md, .py, etc.) are returned as-is without parsing
    when strict=False, or raise an exception when strict=True.

    Args:
        inp_or_file_path: Either a `ReadFileAndParseInput` model or the file path string.
        default_content: Optional default content when providing a raw file path.
        strict: If True, raise exception for unsupported file types.

    Returns:
        A string containing the parsed content (markdown) for supported formats,
        or raw content for unsupported formats when strict=False.

    Raises:
        InvalidInputApplicationError: When strict=True and file type is not supported.

    Examples:
        # Parse a Word document (whitelisted) using model input
        >>> inp = ReadFileAndParseInput(file_path="/path/to/document.docx")
        >>> content = await read_file_and_parse_activity(inp)
        # Returns: Markdown-formatted content

        # Using positional args
        >>> content = await read_file_and_parse_activity("/path/to/readme.txt", None, False)
        # Returns: Original text content without parsing

        # Plain text file with strict=True (raises exception)
        >>> content = await read_file_and_parse_activity("/path/to/readme.txt", None, True)
        # Raises: InvalidInputApplicationError

    """
    # Debug logging to identify the issue
    logger = get_logger(LoggerComponent.ACTIVITY)
    logger.info(f"Activity called with inp_or_file_path: {inp_or_file_path!r} (type: {type(inp_or_file_path)})")

    # Normalize inputs to the model
    if isinstance(inp_or_file_path, ReadFileAndParseInput):
        inp = inp_or_file_path
        logger.info("Using ReadFileAndParseInput object")
        logger.info(f"  file_path: {inp.file_path!r} (type: {type(inp.file_path)})")
        logger.info(f"  default_content: {inp.default_content!r}")
        logger.info(f"  strict: {inp.strict!r}")
    elif isinstance(inp_or_file_path, dict):
        # Handle case where Temporal passes a dict instead of the model
        logger.warning(f"Received dict instead of ReadFileAndParseInput: {inp_or_file_path}")
        inp = ReadFileAndParseInput(**inp_or_file_path)
        logger.info(f"Converted dict to ReadFileAndParseInput with file_path: {inp.file_path!r}")
    else:
        # If inp_or_file_path is accidentally a dict or model, this could cause issues
        logger.warning(f"Converting non-ReadFileAndParseInput to string: {inp_or_file_path!r}")
        inp = ReadFileAndParseInput(
            file_path=str(inp_or_file_path),
            default_content=default_content,
            strict=strict,
        )
        logger.info(f"Created ReadFileAndParseInput with file_path: {inp.file_path!r}")

    # Read file using existing FileSystemUtils
    try:
        # Ensure we're passing a string path
        file_path_str = str(inp.file_path)
        logger.info(f"About to call read_bytes_async with path: '{file_path_str}' (type: {type(file_path_str)})")

        content = await FileSystemUtils.read_bytes_async(
            file_path_str,
            inp.default_content.encode("utf-8") if inp.default_content else None,
        )
    except FileNotFoundError:
        # If file doesn't exist and no default was provided, return empty string
        return inp.default_content if inp.default_content is not None else ""

    # Handle case where file doesn't exist
    if content is None:
        return inp.default_content if inp.default_content is not None else ""

    # Handle case where default was returned as string
    if isinstance(content, str):
        return content

    # Determine if file should be parsed based on extension
    file_ext = Path(inp.file_path).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        # Check strict mode
        if inp.strict:
            raise FileExtensionNotSupportedApplicationError(
                f"File type '{file_ext}' is not supported for parsing. "
                f"Supported extensions are: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            )
        # Return raw content for unsupported file types when not strict
        return content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content

    # Parse with MarkItDown (only for supported extensions)
    md = MarkItDown()  # No configuration options needed for basic usage

    # For better file type detection, save to a temp file with the same extension
    # This allows MarkItDown to properly identify and parse the file type
    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
        tmp_file.write(content if isinstance(content, bytes) else content.encode("utf-8"))
        tmp_file_path = tmp_file.name

    try:
        result = md.convert(tmp_file_path)
        return result.text_content
    except Exception as e:
        raise FatalApplicationError(f"Error parsing file: {e}") from e
    finally:
        # Clean up temp file
        Path(tmp_file_path).unlink(missing_ok=True)
