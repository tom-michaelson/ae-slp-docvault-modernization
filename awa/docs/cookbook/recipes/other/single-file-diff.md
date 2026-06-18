# Single File Diff Workflow

A reusable Temporal workflow for applying edits to a single file based on natural language requests.

## Overview

The `awa-apply-single-file-diff` workflow allows you to make changes to files using natural language instructions. It leverages Large Language Models to interpret your request and generate precise code changes in a diff format, which are then applied to the target file.

## How It Works

1. The workflow reads the content of the target file
2. It sends the file content and your natural language request to an LLM to generate a diff
3. The diff is applied to the file, making the requested changes
4. The workflow returns the status of the operation

## Usage

### Input

The workflow requires a `SingleFileDiffInput` object with the following properties:

- `file_path`: The path to the file you want to modify
- `natural_language_request`: A description of the changes you want to make

### Output

The workflow returns a `SingleFileDiffOutput` object with:

- `success`: Boolean indicating if the changes were applied successfully
- `file_path`: Path of the modified file
- `message`: Status message describing the result

### Example

```python
from temporalio.client import Client
from awa.core.workflows.single_file_diff import SingleFileDiffInput, SingleFileDiffWorkflow

async def main():
    # Connect to Temporal
    client = await Client.connect("localhost:7233")

    # Define the input
    input_data = SingleFileDiffInput(
        file_path="path/to/your/file.py",
        natural_language_request="Add error handling to the process_data function"
    )

    # Execute the workflow
    result = await client.execute_workflow(
        SingleFileDiffWorkflow.run,
        input_data,
        id="modify-file-workflow",
        task_queue="default",
    )

    print(f"Workflow result: {result.message}")

    if result.success:
        print("Changes applied successfully!")
    else:
        print("Failed to apply changes.")
```

## Sample Usage

Check out the example in the `examples/single_file_diff/` directory:

```bash
# Run the example
python examples/single_file_diff/example.py
```

This example demonstrates how to:

1. Make a backup of a file before modifying it
2. Add a new method to a class
3. Modify an existing function
4. Compare the changes with the original file

## Command Line Execution

You can also use the CLI to execute this workflow:

```bash
# Run the workflow using the CLI
uv run -m awa.main run -w awa-apply-single-file-diff -i '{"file_path": "examples/single_file_diff/sample.py", "natural_language_request": "Add a power method to calculate x raised to power n"}'
```

```bash
# Run the workflow using the CLI
uv run -m awa.main run -w awa-apply-single-file-diff -i '{"file_path": "", "natural_language_request": "Create a new file under examples/single_file_diff with name test.py that prints the current time."}'
```

```bash
# Run the workflow using the CLI
uv run -m awa.main run -w awa-apply-single-file-diff -i '{"file_path": "examples/single_file_diff/test.py", "natural_language_request": "Delete this file"}'
```
