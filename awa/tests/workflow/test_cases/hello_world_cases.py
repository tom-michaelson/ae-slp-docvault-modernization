# tests/workflow/test_cases/hello_world_cases.py
from awa.core.workflows.hello_world import HelloWorldInput
from tests.models import WorkflowTestCase

# Define the Pydantic model instance directly
input_data = HelloWorldInput(name="AWA Tester")

# Export test case configuration using the Pydantic model
test_case = WorkflowTestCase(
    workflow_name="awa-hello-world",
    input_data=input_data,
    custom_text_assertions=["AWA Tester"],
)
