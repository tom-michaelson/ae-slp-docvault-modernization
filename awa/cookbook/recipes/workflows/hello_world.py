from datetime import timedelta

from pydantic import BaseModel
from temporalio import workflow

from cookbook.recipes.activities.hello_activities import say_hello


class HelloWorldRecipeWorkflowInput(BaseModel):
    name: str


@workflow.defn
class HelloWorldRecipeWorkflow:
    """A simple workflow that says hello."""

    @workflow.run
    async def run(self, workflow_input: HelloWorldRecipeWorkflowInput) -> str:
        workflow.logger.info(f"Hello, {workflow_input.name}!")
        return await workflow.execute_activity(
            say_hello,
            workflow_input.name,
            start_to_close_timeout=timedelta(seconds=10),
        )
