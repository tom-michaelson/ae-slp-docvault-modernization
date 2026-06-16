# Test Doctor Workflow

An intelligent Temporal workflow that automatically generates unit tests for changed files in a pull request, helping maintain code quality and test coverage through orchestrated child workflows.

## Overview

The `test-doctor` workflow analyzes the differences between two git branches, identifies testable files, and orchestrates comprehensive unit test generation for each changed file by spawning [Test and Lint Pipeline](./test-and-lint-pipeline-workflow.md) child workflows. Each child workflow implements a sophisticated two-agent approach that handles both AI-powered test generation and automated code quality validation, ensuring generated tests follow your project's testing guidelines and standards.

## Demo

<div style="max-width: 640px"><div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;"><iframe src="https://twodegrees1.sharepoint.com/teams/AWA/_layouts/15/embed.aspx?UniqueId=e0a794be-45be-4447-8632-c142df630726&embed=%7B%22hvm%22%3Atrue%2C%22ust%22%3Atrue%7D&referrer=StreamWebApp&referrerScenario=EmbedDialog.Create" width="640" height="360" frameborder="0" scrolling="no" allowfullscreen title="AWA Test Doctor Walkthrough 20250715.mp4" style="border:none; position: absolute; top: 0; left: 0; right: 0; bottom: 0; height: 100%; max-width: 100%;"></iframe></div></div>

**Demo Script:** [View the demo script used for this video](./demo-script.md)

## How It Works

1. **Git Analysis**: Compares your feature branch against the base branch to identify all changed files
2. **File Filtering**: Filters files based on specified extensions and excludes files already in the tests directory
3. **Content Validation**: Ensures files have meaningful content before processing
4. **Child Workflow Orchestration**: Spawns [Test and Lint Pipeline](./test-and-lint-pipeline-workflow.md) child workflows for each file with controlled concurrency
5. **Two-Stage Test Generation**: Each child workflow implements:
   - **Test Generation Agent**: AI-powered creation of comprehensive unit tests with timeout decorators and execution validation
   - **Test Linting Agent**: Automated code quality application using ruff linter with error fixing and final validation
6. **Guideline Compliance**: Uses your custom testing guidelines to ensure generated tests follow project standards

## Key Features

- **Intelligent File Detection**: Automatically identifies which files need testing based on git changes
- **Language Support**: Configurable file extensions to support multiple programming languages
- **Parallel Processing**: Generates tests for multiple files simultaneously with controlled concurrency
- **Two-Stage Pipeline**: Separates test generation from code quality validation for better reliability through child workflows
- **AI-Powered Test Generation**: Intelligent test creation that understands source code functionality and implements timeout protection
- **Automated Code Quality**: Applies linting and formatting standards (via ruff) to generated tests with automatic error fixing
- **Comprehensive Validation**: Ensures tests pass execution before completion at both generation and linting stages
- **Custom Guidelines**: Uses project-specific testing guidelines and mocking strategies
- **Quality Filtering**: Skips empty files and non-testable content automatically

## Workflow Architecture

The Test Doctor workflow operates as a parent orchestrator that manages the overall test generation process across multiple files. For each file that needs testing, it spawns a [Test and Lint Pipeline](./test-and-lint-pipeline-workflow.md) child workflow that handles the detailed work:

- **Parent Workflow (test-doctor)**: Handles git analysis, file discovery, filtering, and orchestration
- **Child Workflow (TestAndLintPipeline)**: Implements the two-agent pipeline for each individual file:
  - Test Generation Agent: Creates comprehensive unit tests with proper error handling and timeout decorators
  - Test Linting Agent: Applies code quality standards and validates the final test output

This architecture provides better fault isolation, allows for parallel processing of multiple files, and ensures that issues with one file don't impact the testing of others.

## Usage

### Input Parameters

| Parameter                 | Description                                |
| ------------------------- | ------------------------------------------ |
| `branch_name`             | Name of your feature branch                |
| `base_branch`             | Branch to compare against (main/develop)   |
| `repo_path`               | Absolute path to your repository           |
| `working_directory`       | Directory (relative to repo) to run in     |
| `testing_guidelines_path` | Path to your testing guidelines file       |
| `file_extensions`         | File types to process (e.g., py, ts, cs)   |
| `tests_directory`         | Where to output generated tests (relative) |

### Output

Returns a status message indicating completion: "Test generation complete." or appropriate error/skip messages.

## Command Line Execution

You can execute the workflow directly using the UV command:

```bash
# Generate tests for Python files in a feature branch
uv run -m awa.main run -w test-doctor -i '{
  "branch_name": "feature/test-doctor-workflow",
  "base_branch": "feature/awa-12-awa-201-tutorial-v2",
  "repo_path": "/Users/ryan.henderson/Projects/AWA/agentic-workflow-accelerator-cookbook",
  "working_directory": "recipes",
  "testing_guidelines_path": "recipes/workflows/test_doctor/input/testing_guidelines.md",
  "file_extensions": "py",
  "tests_directory": "recipes/tests"
}'
```

```bash
# Generate tests for multiple file types
uv run -m awa.main run -w test-doctor -i '{
  "branch_name": "feature/new-feature",
  "base_branch": "main",
  "repo_path": "/path/to/your/repository",
  "working_directory": "src",
  "testing_guidelines_path": "docs/testing_guidelines.md",
  "file_extensions": "py,ts,cs",
  "tests_directory": "tests"
}'
```

## Related Workflows

- [Test and Lint Pipeline Workflow](./test-and-lint-pipeline-workflow.md) - Child workflow that handles the actual test generation and code quality validation for each individual file
