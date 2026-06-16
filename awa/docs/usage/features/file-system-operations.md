# File System Operations

AWA provides comprehensive file system capabilities that enable seamless interaction with files and directories across multiple storage backends. These operations support local file systems as well as cloud storage services, making it easy to build workflows that work with data wherever it lives.

## Overview

AWA offers robust file system operations through a unified interface:

- **File Operations**: Read, write, and copy individual files with support for text and binary content
- **Directory Operations**: List, read, copy, and manage entire directory structures
- **Multi-Backend Support**: Work seamlessly with local, S3, GCS, and other `fsspec`-supported file systems
- **Smart Pattern Matching**: Use .gitignore-style patterns to include or exclude files during operations

These capabilities enable workflows to process data from various sources and destinations without requiring different code for different storage backends.

## File Operations

### Reading Files

AWA provides flexible file reading capabilities that adapt to your data access patterns:

- **Single File Reading**: Read individual files with optional default fallback content
- **Binary File Reading**: Handle binary data like images, documents, and other non-text files
- **Smart File/Directory Reading**: Automatically detect and handle both files and directories with a single operation

**Common use cases:**
- Loading configuration files and settings
- Reading source code and documentation files
- Processing data files for analysis
- Loading templates and content for generation
- Reading binary assets like images or documents

See the activity reference documentation for [`awa-read-file`](/reference/activity/read-file.md) and [`awa-read-file-or-directory`](/reference/activity/read-file-or-directory.md).

### Writing Files

File writing operations support creating new files or updating existing ones:

- **Text Content**: Write string content to files with automatic encoding handling
- **Path Creation**: Automatically create parent directories when writing to new locations
- **Overwrite Safety**: Explicitly overwrite existing files or create new ones as needed

**Common use cases:**
- Generating reports and documentation
- Saving processed data and results
- Creating configuration files
- Writing generated code and templates
- Storing workflow outputs and artifacts

See the activity reference documentation for [`awa-write-file`](/reference/activity/write-file.md).

## Directory Operations

### Listing Directories

Directory listing provides flexible ways to discover and enumerate file structures:

- **Recursive Listing**: Find all files within directory trees
- **Pattern Filtering**: Use .gitignore-style patterns to include or exclude specific files
- **Path Resolution**: Get full paths suitable for use with other file operations

**Common use cases:**
- Discovering files for batch processing
- Building file inventories and catalogs
- Implementing selective file operations
- Creating directory-based workflows

See the activity reference documentation for [`awa-list-directory`](/reference/activity/list-directory.md).

### Reading Directories

Bulk directory reading enables efficient processing of multiple files:

- **Parallel Processing**: Read multiple files concurrently for optimal performance
- **Customizable Formatting**: Control how multiple file contents are combined and structured
- **Template-Based Output**: Use flexible templates to format file content with metadata

**Common use cases:**
- Loading entire codebases for analysis
- Aggregating documentation and content
- Preparing multi-file inputs for LLM processing
- Building comprehensive data sets from directory structures

### Copying Directories

Directory copying supports efficient data movement and duplication:

- **Recursive Copying**: Copy entire directory trees with full structure preservation
- **Selective Copying**: Use .gitignore patterns to control which files are copied
- **Same-Backend Operations**: Efficient copying within the same storage backend (local to local, S3 to S3, etc.)

**Common use cases:**
- Creating project templates and scaffolding
- Backing up and archiving directory structures
- Preparing isolated environments for processing
- Duplicating data for testing and development

See the activity reference documentation for [`awa-copy-directory`](/reference/activity/copy-directory.md).

## Multi-Backend Support

AWA's file system operations are built on [fsspec](https://filesystem-spec.readthedocs.io/), providing unified access to multiple storage backends:

### Supported Backends

- **Local File System**: Standard file and directory operations on local storage
- **Amazon S3**: Direct integration with S3 buckets using `s3://` URLs
- **Google Cloud Storage**: Native GCS support using `gs://` URLs
- **Azure Blob Storage**: Azure integration using `az://` URLs
- **FTP/SFTP**: Remote file access over network protocols
- **And More**: Additional backends available through fsspec ecosystem

### Usage Patterns

```python
# Local file system
local_path = "/home/user/documents/file.txt"

# Amazon S3
s3_path = "s3://my-bucket/path/to/file.txt"

# Google Cloud Storage
gcs_path = "gs://my-bucket/path/to/file.txt"

# All use the same AWA activities
content = await workflow.execute_activity("awa-read-file", local_path)
content = await workflow.execute_activity("awa-read-file", s3_path)
content = await workflow.execute_activity("awa-read-file", gcs_path)
```

## Pattern Matching and Filtering

AWA supports .gitignore-style patterns for flexible file filtering:

### Pattern Examples

- `*.py` - Include only Python files
- `!important.txt` - Exclude specific files (negation)
- `temp/` - Exclude entire directories
- `**/*.log` - Exclude log files in any subdirectory
- `build/**` - Exclude everything in build directories

### Use Cases

- **Selective Processing**: Focus on relevant files while ignoring generated content
- **Security**: Exclude sensitive files from copying or processing operations
- **Performance**: Skip large or unnecessary files to improve workflow speed
- **Compliance**: Automatically exclude files that shouldn't be processed

## How It Works

### Backend Detection

AWA automatically detects the storage backend from the file path or URL:

1. **Protocol Analysis**: Examines URL prefixes (`s3://`, `gs://`, etc.)
2. **Backend Selection**: Chooses the appropriate fsspec implementation
3. **Credential Resolution**: Uses configured authentication for cloud backends
4. **Operation Execution**: Performs the requested file system operation

### Error Handling

File system operations include robust error handling:

- **Missing Files**: Optional default content for read operations
- **Permission Issues**: Clear error messages for access problems
- **Network Failures**: Automatic retry capabilities for remote backends
- **Path Issues**: Validation and normalization of file paths

## Getting Started

To start using file system operations in your workflows:

1. **Configure Backends**: Set up authentication for cloud storage providers (AWS credentials, GCP service accounts, etc.)
2. **Plan Your Operations**: Identify which files and directories your workflow needs to access
3. **Choose Activities**: Select the appropriate file system activities for your use cases
4. **Handle Errors**: Implement appropriate error handling for missing files or access issues

The file system operations integrate seamlessly with other AWA features like [document parsing](/usage/features/document-parsing.md) and [transform workflows](/usage/features/prompts-and-templates.md) to create powerful data processing pipelines.
