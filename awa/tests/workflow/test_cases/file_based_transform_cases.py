# tests/workflow/test_cases/file_based_transform_cases.py
from awa.core.workflows.file_based_transform import FileBasedTransformInput
from tests.models import WorkflowTestCase

# Define the Pydantic model instance directly
input_data = FileBasedTransformInput(
    input_path="tests/workflow/test-data/input_data.json",
    output_path="tests/workflow/tests/output/output_data.txt",
)

# Export test case configuration using the Pydantic model
test_case = WorkflowTestCase(
    workflow_name="awa-transform-file",
    input_data=input_data,
    custom_text_assertions=None,  # Only checks result is not None
)
