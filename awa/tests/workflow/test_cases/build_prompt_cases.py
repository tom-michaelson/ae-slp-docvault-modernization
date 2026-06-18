# tests/workflow/test_cases/build_prompt_cases.py
from awa.sdk.models.build_prompt_params import BuildPromptParams
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
    variables={
        "service_name": "AWA Testing Framework",
        "task_description": "validate workflow functionality and ensure proper template resolution",
        "inputs": ["input_data.json", "transform_request.json", "prompt_template.txt"],
        "action_type": "comprehensive testing",
    },
    output_path="tests/workflow/tests/output/prompt_from_file.txt",
)

file_test_case = WorkflowTestCase(
    workflow_name="awa-build-prompt",
    input_data=file_input_data,
    custom_text_assertions=[
        "AWA Testing Framework",
        "validate workflow functionality",
        "input_data.json",
        "comprehensive testing",
    ],
)

# Export both test cases
test_cases = [template_test_case, file_test_case]
