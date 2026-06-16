# Workflow Integration Testing

This guide explains the architecture and implementation details of AWA's workflow integration test structure, including how to add, update, and maintain workflow tests using the auto-discovery system.

## Architecture Overview

The workflow integration test system uses an auto-discovery mechanism to automatically load test cases from individual Python files, providing a scalable and maintainable testing structure.

### Key Components

#### Auto-Discovery Pipeline
1. **Test Case Files**: Individual `*_cases.py` files in `tests/workflow/test_cases/`
2. **Discovery Function**: `load_test_cases()` in `tests/workflow/utils/workflow_utils.py`
3. **Test Execution**: Parametrized pytest test in `tests/workflow/tests/test_workflow_output.py`

#### How It Works
```python
# 1. Auto-discovery scans for test case files
for module_info in pkgutil.iter_modules([test_cases_path]):
    if module_info.name.endswith('_cases'):
        # 2. Import and extract test cases
        module = importlib.import_module(module_name)
        # 3. Add to pytest parametrization
        test_cases.append((workflow_name, input_data, assertions))
```

#### Integration with pytest
The `load_test_cases()` function returns a list of tuples that pytest uses for parametrization:
```python
@pytest.mark.parametrize(
    "workflow_name,input_data,custom_text_assertions",
    load_test_cases(),  # Auto-discovered test cases
)
async def test_workflow_execution(workflow_name, input_data, custom_text_assertions):
    result = await execute_workflow(workflow_name, input_data)
    # Assert result contains expected text
```

### Benefits of Auto-Discovery

- **Zero Configuration**: New test case files are automatically included
- **Naming Convention**: Only `*_cases.py` files are processed
- **Error Resilience**: Import failures don't break the entire test suite
- **Developer Experience**: Create file → tests automatically run

## Test Case File Structure

Test case files follow a consistent structure with specific naming conventions and export patterns.

### Naming Convention
- **Location**: `tests/workflow/test_cases/`
- **Pattern**: `<workflow_name>_cases.py`
- **Examples**: `hello_world_cases.py`, `build_prompt_cases.py`

### Export Patterns

#### Single Test Case
Export a single test case using `test_case`:
```python
# tests/workflow/test_cases/hello_world_cases.py
from awa.core.workflows.hello_world import HelloWorldInput
from tests.models import WorkflowTestCase

# Direct Pydantic model instantiation
input_data = HelloWorldInput(name="AWA Tester")

# Export test case configuration
test_case = WorkflowTestCase(
    workflow_name="awa-hello-world",
    input_data=input_data,
    custom_text_assertions=["AWA Tester"],
)
```

#### Multiple Test Cases
Export multiple test cases using `test_cases` list:
```python
# tests/workflow/test_cases/build_prompt_cases.py
from awa.core.models.build_prompt_params import BuildPromptParams
from tests.models import WorkflowTestCase

# Template-based test case
template_input_data = BuildPromptParams(
    template="Hello {{ name }}, welcome to {{ product }}!",
    variables={"name": "Developer", "product": "AWA"},
    output_path="tests/workflow/tests/output/built_prompt.txt",
)
template_test_case = WorkflowTestCase(
    workflow_name="awa-build-prompt",
    input_data=template_input_data,
    custom_text_assertions=["Developer", "AWA"],
)

# File-based test case
file_input_data = BuildPromptParams(
    template_input={
        "path": "tests/workflow/test-data/prompt_template.txt",
        "name": "template",
    },
    variables={"service_name": "AWA Testing Framework"},
    output_path="tests/workflow/tests/output/prompt_from_file.txt",
)
file_test_case = WorkflowTestCase(
    workflow_name="awa-build-prompt",
    input_data=file_input_data,
    custom_text_assertions=["AWA Testing Framework"],
)

# Export both test cases
test_cases = [template_test_case, file_test_case]
```

### Test Case Schema
Each test case must be an instance of the `WorkflowTestCase` Pydantic model with these required attributes:
```python
{
    "workflow_name": str,                        # Workflow name for execute_workflow()
    "input_data": BaseModel,                     # Pre-instantiated Pydantic model
    "custom_text_assertions": Optional[List[str]]  # Text strings to assert in result
}
```

## Adding New Workflow Test Cases

Follow these steps to add integration tests for a new workflow:

### Step 1: Create Test Case File

Create a new file in `tests/workflow/test_cases/` with the pattern `<workflow_name>_cases.py`:

```python
# tests/workflow/test_cases/my_workflow_cases.py
from awa.core.workflows.my_workflow import MyWorkflowInput
from tests.models import WorkflowTestCase

# Define the Pydantic model instance directly
input_data = MyWorkflowInput(
    param1="value1",
    param2="value2",
    output_path="tests/workflow/tests/output/my_workflow_output.txt"
)

# Export test case configuration
test_case = WorkflowTestCase(
    workflow_name="awa-my-workflow",
    input_data=input_data,
    custom_text_assertions=["expected_text_in_output"],
)
```

### Step 2: Test Data Setup

If your workflow requires input files, add them to `tests/workflow/test-data/`:

```
tests/workflow/test-data/
├── my_workflow_input.txt       # Input data for your workflow
├── sample_config.json          # Configuration files
└── template_example.md         # Template files
```

**Best Practices**:
- Use descriptive filenames that indicate their purpose
- Include sample data that exercises different workflow paths
- Document any special data requirements in comments

### Step 3: Verify Auto-Discovery

Run the workflow tests to ensure your test case is discovered:

```bash
# Run all workflow tests
make run-test-workflow
```

Your test case should appear in the output:
```
test_workflow_execution[awa-my-workflow] PASSED
```

### Step 4: Validate Test Execution

Check that your test:
1. **Executes successfully**: No import or runtime errors
2. **Asserts correctly**: Custom text assertions pass
3. **Produces output**: Expected output files are created

## Test Case Patterns

Common patterns for different types of workflows:

### File I/O Workflows

For workflows that read/write files:
```python
from awa.core.workflows.file_based_transform import FileBasedTransformInput
from tests.models import WorkflowTestCase

input_data = FileBasedTransformInput(
    input_file_path="tests/workflow/test-data/input.txt",
    transform_request="Convert to uppercase",
    output_file_path="tests/workflow/tests/output/transformed.txt",
)

test_case = WorkflowTestCase(
    workflow_name="awa-transform-file",
    input_data=input_data,
    custom_text_assertions=None,  # Basic result validation only
)
```

### Template-Based Workflows

For workflows with template processing:
```python
from awa.core.models.build_prompt_params import BuildPromptParams
from tests.models import WorkflowTestCase

input_data = BuildPromptParams(
    template="Process {{ task }} for {{ client }}",
    variables={"task": "data analysis", "client": "Acme Corp"},
    output_path="tests/workflow/tests/output/processed_prompt.txt",
)

test_case = WorkflowTestCase(
    workflow_name="awa-build-prompt",
    input_data=input_data,
    custom_text_assertions=["data analysis", "Acme Corp"],
)
```

### Agent Integration Workflows

For workflows that use agents:
```python
from awa.core.workflows.execute_agent import ExecuteAgentInput
from tests.models import WorkflowTestCase

input_data = ExecuteAgentInput(
    agent_type="goose",
    task_description="Create a simple Python script",
    workspace_path="/tmp/agent_workspace",
)

test_case = WorkflowTestCase(
    workflow_name="awa-execute-agent",
    input_data=input_data,
    custom_text_assertions=["python", "script"],
)
```

### Complex Data Workflows

For workflows with nested or complex input data:
```python
from awa.core.workflows.complex_workflow import ComplexWorkflowInput
from tests.models import WorkflowTestCase

input_data = ComplexWorkflowInput(
    config={
        "processing_type": "advanced",
        "options": {
            "parallel": True,
            "max_workers": 4,
        }
    },
    data_sources=[
        {"type": "file", "path": "tests/workflow/test-data/source1.json"},
        {"type": "api", "endpoint": "http://localhost:8080/data"},
    ],
    output_format="json",
)

test_case = WorkflowTestCase(
    workflow_name="awa-complex-workflow",
    input_data=input_data,
    custom_text_assertions=["processed", "completed"],
)
```
