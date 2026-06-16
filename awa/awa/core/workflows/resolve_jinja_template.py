from datetime import timedelta

from pydantic import BaseModel
from temporalio import workflow

from awa.sdk import constants as sdk_constants


class ResolveTemplateInput(BaseModel):
    input_str: str


@workflow.defn(name=sdk_constants.WORKFLOW_RESOLVE_TEMPLATE)
class ResolveTemplateWorkflow:
    """Workflow for resolving Jinja2 template strings.

    This workflow takes a template string as input and resolves it using the
    resolve_template activity. It provides a workflow-level interface for
    template resolution operations.
    """

    @workflow.run
    async def run(self, workflow_input: ResolveTemplateInput) -> str:
        return await workflow.execute_activity(
            sdk_constants.ACTIVITY_RESOLVE_TEMPLATE,
            workflow_input.input_str,
            start_to_close_timeout=timedelta(seconds=5),
        )
