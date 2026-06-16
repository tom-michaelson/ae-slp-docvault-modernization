"""Model for directory information."""

from pydantic import BaseModel


class FolderInfo(BaseModel):
    """Information about a directory and its contents."""

    path: str
    files: list[str]  # File names only (not full paths)
    subdirectories: list[str]  # Subdirectory names only (not full paths)
