# PR Description Workflow

A powerful Temporal workflow that automatically generates comprehensive pull request descriptions by analyzing git branch differences.

## Overview

The `pr-description` workflow takes the hassle out of writing detailed PR descriptions. Simply provide your feature branch and base branch, and the workflow will analyze all the changes, summarize them intelligently using AI, and generate a professional markdown-formatted PR description.

## Demo

<div style="max-width: 640px"><div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;"><iframe src="https://twodegrees1.sharepoint.com/teams/AWA/_layouts/15/embed.aspx?UniqueId=2c12284e-99e4-4853-99ef-c4157ccc875f&embed=%7B%22hvm%22%3Atrue%2C%22ust%22%3Atrue%7D&referrer=StreamWebApp&referrerScenario=EmbedDialog.Create" width="640" height="360" frameborder="0" scrolling="no" allowfullscreen title="AWA PR Description Writer Walkthrough 20250711.mp4" style="border:none; position: absolute; top: 0; left: 0; right: 0; bottom: 0; height: 100%; max-width: 100%;"></iframe></div></div>

**Demo Script:** [View the demo script used for this video](./DemoScript.md)

## How It Works

1. **Git Analysis**: The workflow compares your feature branch against the base branch to identify all commits and file changes
2. **Intelligent Summarization**: Uses BAML functions powered by LLMs to summarize each file's changes individually
3. **Batch Processing**: Groups file summaries into batches for efficient processing of large changesets
4. **High-Level Summary**: Generates an overall summary that captures the essence of your changes
5. **Structured Output**: Combines everything into a well-formatted markdown PR description with both high-level overview and file-by-file details

## Key Features

- **Comprehensive Analysis**: Examines both commit logs and detailed file diffs
- **AI-Powered Summarization**: Uses advanced language models to understand and summarize code changes
- **Scalable Processing**: Handles large changesets efficiently with controlled concurrency
- **Professional Format**: Generates structured markdown output ready for GitHub/GitLab
- **Detailed Logging**: Provides extensive logging for debugging and monitoring

## Usage

### Input Parameters

The workflow requires a `PrDescriptionWorkflowInput` object with:

- `branch_name`: Your feature branch name (e.g., "feature/user-authentication")
- `repo_path`: Absolute path to your git repository
- `base_branch`: The branch to compare against (typically "main" or "develop")

### Output

Returns a markdown-formatted string containing:

- **Summary section**: High-level overview of all changes
- **File-by-File Changes section**: Detailed breakdown of what changed in each file

## Command Line Execution

You can execute the workflow directly using the UV command:

```bash
# Basic usage - compare feature branch against main
uv run -m awa.main run -w "pr-description" -i '{
  "branch_name": "feature/user-authentication",
  "repo_path": "/Users/developer/my-project",
  "base_branch": "main"
}'
```

```bash
# Compare against a different base branch
uv run -m awa.main run -w "pr-description" -i '{
  "branch_name": "feature/payment-integration",
  "repo_path": "/path/to/your/repository",
  "base_branch": "develop"
}'
```

## MCP Server Execution

The PR Description workflow can be executed through the MCP (Model Context Protocol) server interface, which allows agents and AI tools like Claude, Cursor, or VS Code to invoke AWA workflows directly.

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

Once configured, agents can use the `start_workflow` tool to execute the PR Description workflow. Here's the payload format:

```json
{
  "workflow": "pr-description",
  "workflow_input": {
    "branch_name": "hotfix/cognito-fix",
    "base_branch": "main",
    "repo_path": "/Users/robert.forshier/Projects/AWA/agentic-workflow-accelerator"
  }
}
```

![PR Description MCP Execution Example](./PRDescriptionMCP.png)

The image shows:

- **Input**: The JSON payload sent to the `start_workflow` tool with branch details
- **Output**: The AI-generated PR description with comprehensive summary and file-by-file changes

For more information on MCP tool integration, see the [MCP tools recipes](/cookbook/recipes/use-mcp-tools/sample-mcp-tool-stdio-workflow).
