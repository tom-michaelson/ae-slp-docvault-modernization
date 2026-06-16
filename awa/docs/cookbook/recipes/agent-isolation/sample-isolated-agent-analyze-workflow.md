# SampleIsolatedAgentAnalyzeWorkflow

Sample workflow demonstrating isolated agent execution in ANALYZE mode.

## Overview

This workflow demonstrates how to use the IsolatedAgentChildWorkflow to execute agents in isolated temporary directories for security analysis, without making changes to the original directory. It is ideal for running LLM-powered agents to analyze codebases and generate security reports in a safe, read-only environment.

## Key Features

- Executes agents in isolated temporary directories (no risk to source files)
- Uses ANALYZE mode for read-only analysis
- Supports configurable agent provider and prompt
- Generates a detailed security analysis report in markdown format
- Timeout and task queue configuration for robust execution

## How It Works

1. Receives a directory path and output directory as input
2. Configures an agent in ANALYZE mode (e.g., Claude)
3. Creates an isolated temporary directory for the operation
4. Runs the agent to analyze code for security vulnerabilities
5. Saves a detailed markdown report to the output directory
6. Returns the agent execution result as a dictionary

## Usage

### Input

| Name               | Type  | Description                                                                  |
| ------------------ | ----- | ---------------------------------------------------------------------------- |
| `directory_path`   | `str` | Path to the directory to analyze                                             |
| `output_directory` | `str` | Directory where analysis results will be saved (default: "awa-agent-output") |

### Output

**Direct Output**: Dictionary with the agent execution result (status, details, etc.)

**File Outputs**: Markdown security analysis report saved to the specified output directory as `security_analysis_report.md`.

## Configuration

- You must have a directory containing the codebase to analyze as `directory_path`.
- LLM credentials (e.g., for Claude) must be configured in your environment.
- Ensure AWA core services are running and accessible.

## Command Line Execution

```bash
uv run -m awa.main run -w sample-isolated-agent-analyze -i '{"directory_path":"/some/path/to/directory","branch":"main"}'
```

## Related Workflows

- [SampleIsolatedAgentActWorkflow](./sample-isolated-agent-act-workflow.md) – Example of using ACT mode for code modification in isolated worktrees.
