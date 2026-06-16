# tests/workflow/test_cases/single_file_diff_cases.py
from awa.core.workflows.single_file_diff import SingleFileDiffInput

# Define the Pydantic model instance directly
input_data = SingleFileDiffInput(
    file_path="tests/workflow/test-data/single-file-diff-test.json",
    natural_language_request="Large JSON object with keys, values, and nested objects",
)

# Export test case configuration using the Pydantic model
# test_case = WorkflowTestCase(
#     workflow_name="awa-apply-single-file-diff",
#     input_data=input_data,
#     custom_text_assertions=None,  # No custom text assertions
# )
