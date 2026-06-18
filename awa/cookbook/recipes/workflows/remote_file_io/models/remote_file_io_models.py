"""Models for remote file IO workflows."""

from enum import Enum

from pydantic import BaseModel, Field


class RemoteStorageType(str, Enum):
    """Supported remote storage types."""

    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    GCP_STORAGE = "gcp_storage"
    SFTP = "sftp"


class RemoteFileIOWorkflowInput(BaseModel):
    """Input model for remote file IO workflow."""

    storage_type: RemoteStorageType = Field(..., description="Type of remote storage to use")
    remote_base_path: str = Field(..., description="Base path in remote storage (e.g., s3://bucket/path)")
    test_file_name: str = Field(default="test_file.txt", description="Name of test file to create/read")
    test_directory_name: str = Field(default="test_directory", description="Name of test directory to create/list")
    test_content: str = Field(
        default="Hello from AWA Remote File IO!",
        description="Content to write to test file",
    )
    cleanup_after_test: bool = Field(default=True, description="Whether to cleanup test files after completion")


class FileOperationResult(BaseModel):
    """Result of a file operation."""

    operation: str = Field(..., description="Operation performed (read, write, list, etc.)")
    success: bool = Field(..., description="Whether the operation succeeded")
    path: str = Field(..., description="Path operated on")
    message: str = Field(..., description="Result message or error")
    data: str | list[str] | None = Field(default=None, description="Data returned from operation (if any)")


class RemoteFileIOWorkflowOutput(BaseModel):
    """Output model for remote file IO workflow."""

    storage_type: RemoteStorageType = Field(..., description="Type of remote storage used")
    remote_base_path: str = Field(..., description="Base path in remote storage")
    operations: list[FileOperationResult] = Field(..., description="Results of all file operations performed")
    summary: str = Field(..., description="Summary of test results")
