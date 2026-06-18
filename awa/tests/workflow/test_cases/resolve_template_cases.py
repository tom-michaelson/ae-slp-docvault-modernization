# tests/workflow/test_cases/resolve_template_cases.py
from awa.core.workflows.resolve_jinja_template import ResolveTemplateInput
from tests.models import WorkflowTestCase

# Define the Pydantic model instance directly
input_data = ResolveTemplateInput(input_str="Processing workflow in test mode.")

# Export test case configuration using the Pydantic model
test_case = WorkflowTestCase(
    workflow_name="awa-resolve-template",
    input_data=input_data,
    custom_text_assertions=["Processing workflow in test mode."],
)
