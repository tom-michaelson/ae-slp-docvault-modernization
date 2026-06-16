# SampleIsolatedAgentActWorkflow

Sample workflow demonstrating isolated agent execution in ACT mode.

## Overview

This workflow demonstrates how to use the IsolatedAgentChildWorkflow to execute agents in isolated git worktrees for making changes to code repositories. It is useful for scenarios where you want an LLM-powered agent to safely modify code in a repository, with all changes isolated to a worktree and merged back to the source branch.

## Key Features

- Executes agents in isolated git worktrees (no risk to main branch until merge)
- Uses ACT mode for code modification
- Supports configurable agent provider and prompt
- Timeout and task queue configuration for robust execution

## How It Works

1. Receives a repository path and branch as input
2. Configures an agent in ACT mode (e.g., Claude)
3. Creates an isolated git worktree for the operation
4. Runs the agent to make code changes (e.g., add logging)
5. Merges changes back to the source branch
6. Returns the agent execution result as a dictionary

## Usage

### Input

| Name        | Type  | Description                         |
| ----------- | ----- | ----------------------------------- |
| `repo_path` | `str` | Path to the git repository          |
| `branch`    | `str` | Branch to work on (default: "main") |

### Output

**Direct Output**: Dictionary with the agent execution result (status, details, etc.)

**File Outputs**: Changes are made to the specified git repository branch via a worktree merge.

## Configuration

- You must have a directory containing a git repository to point to as `repo_path`.
- LLM credentials (e.g., for Claude) must be configured in your environment.
- Ensure AWA core services are running and accessible.

## Command Line Execution

```bash
uv run -m awa.main run -w sample-isolated-agent-act -i '{"repo_path":"/some/path/to/git/repo","branch":"main"}'
```

## Related Workflows

- [SampleIsolatedAgentAnalyzeWorkflow](./sample-isolated-agent-analyze-workflow.md) – Example of using ANALYZE mode for read-only security analysis.
