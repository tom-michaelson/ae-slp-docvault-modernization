# Test and Lint Pipeline Workflow

A specialized two-stage Temporal workflow that generates comprehensive unit tests for a single file and applies code quality standards through an intelligent agent pipeline.

## Overview

The `TestAndLintPipelineWorkflow` is a child workflow designed to be called by the [Test Doctor Workflow](./test-doctor-workflow.md) for each individual file that needs testing. It implements a sophisticated two-agent approach to ensure high-quality test generation with proper code standards compliance.

## Key Features

- **Two-Stage Pipeline**: Separates test generation from code quality validation for better reliability
- **Intelligent Test Generation**: AI-powered test creation that understands source code functionality
- **Automated Code Quality**: Applies linting and formatting standards to generated tests
- **Guideline Compliance**: Uses project-specific testing guidelines and best practices
- **Comprehensive Validation**: Ensures tests pass execution before completion
- **Timeout Protection**: Prevents tests from hanging with mandatory timeout decorators

## How It Works

1. **Input Processing**: Receives a single file path and configuration from parent test-doctor workflow
2. **Path Resolution**: Calculates appropriate test file paths mirroring source structure in tests directory
3. **Test Generation Agent**:
   - Reads source file to understand functionality
   - Creates or updates comprehensive unit tests
   - Implements timeout decorators for safety
   - Validates tests execute successfully
4. **Test Linting Agent**:
   - Applies code quality standards using ruff linter
   - Fixes linting errors automatically or manually
   - Performs final test validation to ensure no regressions

## Usage

### Input Parameters

The workflow requires a `TestAndLintPipelineWorkflowInput` object with:

- `root_workflow_input`: The original TestDoctorWorkflowInput containing branch and repo information
- `file_path`: Relative path to the source file needing tests (e.g., "workflows/sample_workflow.py")
- `testing_guidelines_path`: Path to file containing testing guidelines and mocking strategies
- `tests_directory`: Directory for generated tests, relative to repository root
- `working_directory`: Working directory relative to repo path where agents operate

### Output

Returns `None` upon successful completion. Generated test files are written to the file system in the specified tests directory.

## Command Line Execution

While this workflow is primarily designed as a child workflow, it can be executed directly for testing purposes:

```bash
# Execute for a specific file using TestDoctor parameters
uv run -m awa.main run -w test-and-lint-pipeline -i '{
  "root_workflow_input": {
    "branch_name": "feature/test-doctor-workflow",
    "base_branch": "feature/awa-12-awa-201-tutorial-v2",
    "repo_path": "/Users/robert.forshier/Projects/AWA/agentic-workflow-accelerator-cookbook",
    "working_directory": "recipes",
    "testing_guidelines_path": "recipes/workflows/test_doctor/input/testing_guidelines.md",
    "file_extensions": "py",
    "tests_directory": "recipes/tests"
  },
  "file_path": "workflows/sample_workflow.py",
  "testing_guidelines_path": "recipes/workflows/test_doctor/input/testing_guidelines.md",
  "tests_directory": "recipes/tests",
  "working_directory": "recipes"
}'
```

```bash
# Execute for a different file in the same project
uv run -m awa.main run -w test-and-lint-pipeline -i '{
  "root_workflow_input": {
    "branch_name": "feature/test-doctor-workflow",
    "base_branch": "feature/awa-12-awa-201-tutorial-v2",
    "repo_path": "/Users/robert.forshier/Projects/AWA/agentic-workflow-accelerator-cookbook",
    "working_directory": "recipes",
    "testing_guidelines_path": "recipes/workflows/test_doctor/input/testing_guidelines.md",
    "file_extensions": "py",
    "tests_directory": "recipes/tests"
  },
  "file_path": "utilities/workflow_utils.py",
  "testing_guidelines_path": "recipes/workflows/test_doctor/input/testing_guidelines.md",
  "tests_directory": "recipes/tests",
  "working_directory": "recipes"
}'
```

## Related Workflows

- [Test Doctor Workflow](./test-doctor-workflow.md) - Parent workflow that orchestrates testing for multiple files
- [PR Description Workflow](../pr-description/PRDescriptionWorkflow.md) - Analyzes the same git changes for documentation purposes
