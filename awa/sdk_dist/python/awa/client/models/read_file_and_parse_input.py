"""Models for document parsing functionality."""

from pydantic import BaseModel, Field


class ReadFileAndParseInput(BaseModel):
    """Input model for read_file_and_parse activity.

    Attributes:
        file_path: The file path to read and parse.
        default_content: A string to return if the file does not exist.
        strict: If True, raise an exception for unsupported file types.
               If False (default), return raw content for unsupported types.

    """

    file_path: str = Field(description="The file path to read and parse")
    default_content: str | None = Field(
        None,
        description="A string to return if the file does not exist",
    )
    strict: bool = Field(
        False,  # noqa: FBT003
        description="If True, raise exception for unsupported file types; if False, return raw content",
    )
