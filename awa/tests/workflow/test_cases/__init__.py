# Test case definitions for workflow tests
#
# This package contains individual test case files for each workflow type.
# Files use the _cases.py suffix to avoid pytest discovery.
#
# Each test case file should export either:
# - test_case: WorkflowTestCase for a single test case
# - test_cases: list[WorkflowTestCase] for multiple test cases
#
# Test case structure:
# {
#     "workflow_name": str,                        # Workflow name passed to execute_workflow()
#     "input_data": BaseModel,                     # Instantiated Pydantic model with validation
#     "custom_text_assertions": Optional[List[str]]  # Text strings to assert in result
# }
