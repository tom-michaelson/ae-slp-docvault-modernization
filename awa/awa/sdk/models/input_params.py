from pydantic import BaseModel
from pydantic.json_schema import SkipJsonSchema


class InputParams(BaseModel):
    """Parameters for reading content from either a file or directory."""

    path: str
    """
    Path to the file or directory to read from.
    """
    name: str | SkipJsonSchema[None] = None
    """
    Name of the input.
    """
    ignore_file_path: str | SkipJsonSchema[None] = None
    """
    Path to .gitignore-style file for directories.
    """
    default: str | SkipJsonSchema[None] = None
    """
    Default content to return if file doesn't exist.
    """
    directory_join_template_str: str | SkipJsonSchema[None] = None
    """
    Template string for formatting each file's content when reading directories.
    Defaults to '<file name="{file}">\n{content}\n</file>'.
    """
    directory_join_str: str | SkipJsonSchema[None] = None
    """
    String used to join multiple file contents when reading directories.
    Defaults to "\n".
    """
    image_mime_type: str | SkipJsonSchema[None] = None
    """
    Mime type of the image to read (e.g. "image/png").
    If present, the image will be converted to base64.
    Omit if not an image.
    """
