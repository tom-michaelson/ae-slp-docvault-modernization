# Release Notes Workflow

A powerful Temporal workflow that automatically generates comprehensive release notes by analyzing git commit history and file changes between releases.

## Overview

The `release-notes` workflow takes the complexity out of creating detailed release notes. Simply provide your release branch and the commit hash of the last release, and the workflow will analyze all the changes, summarize them intelligently using AI, and generate professional markdown-formatted release notes.

## How It Works

1. **Git Analysis**: The workflow analyzes commit logs from the specified first commit to the release branch HEAD
2. **Change Detection**: Compares file differences between the first commit and current release branch
3. **Intelligent Summarization**: Uses BAML functions powered by LLMs to summarize each file's changes individually
4. **Batch Processing**: Groups file summaries into batches for efficient processing of large changesets
5. **High-Level Summary**: Generates an overall summary that captures the essence of all changes in the release
6. **Structured Output**: Combines everything into a well-formatted markdown release notes document with both high-level overview and file-by-file details

## Key Features

- **Comprehensive Analysis**: Examines both commit logs and detailed file diffs since last release
- **AI-Powered Summarization**: Uses advanced language models to understand and summarize code changes
- **Scalable Processing**: Handles large changesets efficiently with controlled concurrency
- **Professional Format**: Generates structured markdown output ready for release documentation
- **Detailed Logging**: Provides extensive logging for debugging and monitoring
- **File Output**: Saves generated release notes to `release_notes.md` in the workflow output directory

## Usage

### Input Parameters

The workflow requires a `ReleaseNotesWorkflowInput` object with:

- `last_released_commit`: The hash of the latest commit included in the previous release
- `repo_path`: Absolute path to your git repository
- `release_branch`: The branch containing the release changes (defaults to "main")

### Output

Returns a markdown-formatted string containing:

- **Summary section**: High-level overview of all changes in the release
- **File-by-File Changes section**: Detailed breakdown of what changed in each file

The release notes are also saved to a file at `{workflow_output}/release_notes.md`.

## Command Line Execution

You can execute the workflow directly using the UV command:

```bash
# Basic usage - generate release notes from a specific commit to main
uv run -m awa.main run -w "release-notes" -i '{
  "last_released_commit": "abc123def456",
  "repo_path": "/Users/developer/my-project",
  "release_branch": "main"
}'
```

```bash
# Generate release notes for a specific release branch
uv run -m awa.main run -w "release-notes" -i '{
  "last_released_commit": "def456abc789",
  "repo_path": "/path/to/your/repository",
  "release_branch": "release/v2.1.0"
}'
```

## MCP Server Execution

The Release Notes workflow can be executed through the MCP (Model Context Protocol) server interface, which allows agents and AI tools like Claude, Cursor, or VS Code to invoke AWA workflows directly.

### MCP Server Configuration

First, configure the AWA MCP server in your MCP client configuration:

```json
{
  "mcpServers": {
    "awa": {
      "command": "uv",
      "args": ["run", "-m", "awa.main", "mcp"]
    }
  }
}
```

### Using the MCP Start Workflow Tool

Once configured, agents can use the `start_workflow` tool to execute the Release Notes workflow. Here's the payload format:

```json
{
  "workflow": "release-notes",
  "workflow_input": {
    "last_released_commit": "a1b2c3d4e5f6",
    "release_branch": "main",
    "repo_path": "/Users/developer/agentic-workflow-accelerator"
  }
}
```

The MCP execution will:

- **Input**: The JSON payload sent to the `start_workflow` tool with commit and branch details
- **Output**: The AI-generated release notes with comprehensive summary and file-by-file changes

For more information on MCP tool integration, see the [MCP tools recipes](/cookbook/recipes/use-mcp-tools/sample-mcp-tool-stdio-workflow).
