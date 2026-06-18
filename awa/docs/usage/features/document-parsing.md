# Document Parsing with MarkItDown

The AWA Document Parsing feature enables seamless conversion of various document formats into markdown, making them suitable for processing by Large Language Models (LLMs). This feature is powered by [Microsoft's MarkItDown library](https://github.com/microsoft/markitdown) and integrates directly with AWA's workflow system.

## Overview

The `read_file_and_parse` activity extends AWA's file reading capabilities by automatically detecting and converting supported document formats to markdown. Files with unsupported extensions are returned as-is without parsing, ensuring safe handling of all file types.

## Supported File Types

<!--@include: ../.shared/supported-file-types.md -->

## Usage

See the Activity reference documentation for [read-file-and-parse](/reference/activity/read-file-and-parse.md).

## How It Works

1. **File Reading**: Uses AWA's `FileSystemUtils` to read files from any supported filesystem (local, S3, GCS, etc.)
2. **Format Detection**: Checks if file extension is in the supported formats whitelist
3. **Supported Formats**: Only files with whitelisted extensions are parsed to markdown
4. **Unsupported Formats**: Files with non-whitelisted extensions are returned as-is
5. **Error Handling**: Falls back to raw content if parsing fails, unless `strict` is set to `True`

## Workflow Integration

The document parsing functionality is available as both an activity and a workflow:

- **Activity**: `read_file_and_parse` - Direct execution for simple use cases
- **Workflow**: `ReadFileAndParseWorkflow` - Provides workflow-level orchestration

### Using the Workflow

The `ReadFileAndParseWorkflow` wraps the parsing activity to enable:

- Workflow-level retries and error handling
- Integration with other workflows as a child workflow
- Future extensibility for additional processing steps

```python
from awa.core.workflows.read_file_and_parse_workflow import ReadFileAndParseWorkflow
from awa.core.activities.core_models.document_parsing import ReadFileAndParseActivityInput

# Execute the workflow
result = await workflow_client.execute_workflow(
    ReadFileAndParseWorkflow.run,
    ReadFileAndParseActivityInput(
        file_path="s3://my-bucket/document.pdf",
        default_content="No content found",
        strict=False, # Set to True to raise an error if the file extension is not supported
    ),
    id="parse-document-123",
    task_queue=TASK_QUEUE_AGENT_OPERATIONS,
)
print(f"Parsed content: {result.file_content}")
```
