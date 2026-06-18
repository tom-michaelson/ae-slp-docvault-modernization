# Remote File IO

## Overview

The Remote File IO workflow demonstrates how to use AWA's file IO activities with remote storage systems. This recipe shows that AWA's existing file IO functionality transparently supports remote file systems through `fsspec`, enabling seamless integration with cloud storage providers.

### Key Features

- Transparent remote file system access using standard file IO activities
- Support for AWS S3, with others coming soon!
- Demonstrates all core file operations: read, write, list, and directory operations
- No code changes required - just use remote paths with protocol prefixes
- Smart error handling - fails fast on authentication/permission errors instead of retrying

## How It Works

1. **Protocol Detection**: AWA's file system utilities automatically detect the storage protocol from the path prefix (e.g., `s3://`)
2. **Transparent Operations**: The same file IO activities work for both local and remote files
3. **Demonstration Flow**:
   - Writes a test file to remote storage
   - Reads the file back to verify
   - Creates a directory structure with multiple files
   - Lists directory contents
   - Reads all files in the directory

## Usage

### Input Model

```python
class RemoteFileIOWorkflowInput(BaseModel):
    storage_type: RemoteStorageType  # aws_s3
    remote_base_path: str  # Base path with protocol prefix
    test_file_name: str = "test_file.txt"
    test_directory_name: str = "test_directory"
    test_content: str = "Hello from AWA Remote File IO!"
    cleanup_after_test: bool = True
```

### Output Model

```python
class RemoteFileIOWorkflowOutput(BaseModel):
    storage_type: RemoteStorageType
    remote_base_path: str
    operations: list[FileOperationResult]  # Details of each operation
    summary: str  # Human-readable summary
```

## Configuration

### Prerequisites

Before running the workflow, ensure you have:

1. **Storage container/bucket exists** - The S3 bucket must already exist
2. **Credentials configured** for your chosen storage provider in the core AWA `.env` file
3. **Required Python packages** installed (handled automatically by AWA)
4. **Appropriate permissions** on the remote storage location (read/write/list)

### Storage-Specific Setup

#### AWS S3

```bash
# In agentic-workflow-accelerator/.env
AWS_REGION=us-west-2
AWS_PROFILE=your-profile-name
```

Alternatively, configure AWS credentials using one of these methods:

```bash
# Configure AWS credentials (if not using IAM roles)
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

#### Azure Blob Storage

Coming soon!

#### GCP Cloud Storage

Coming soon!

#### SFTP

Coming soon!

## Command Line Execution

### AWS S3 Example

```bash
uv run -m awa.main run -w remote-file-io -i '{
  "storage_type": "aws_s3",
  "remote_base_path": "s3://my-bucket/awa-test",
  "test_file_name": "test_s3_file.txt",
  "test_directory_name": "test_s3_directory"
}'
```

## Using Remote File IO in Your Workflows

The beauty of AWA's remote file IO support is that you don't need special activities or code changes. Simply use remote paths with the standard file IO activities through the constants pattern:

```python
import constants
from temporalio import workflow

# Works with any supported remote path
await workflow.execute_activity(
    constants.AWA_ACTIVITY_WRITE_FILE,
    args=["s3://my-bucket/file.txt", "Hello S3!"],
    task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
    start_to_close_timeout=timedelta(minutes=2)
)
```

## Related Workflows

- [Transform Workflow](../../../reference/workflow/transform.md) - Transform files
- [AWA 101 Workflows](../../tutorials/awa-101/index.md) - Basic file processing examples
- [Single File Diff](./single-file-diff.md) - Transform single files with diff generation
