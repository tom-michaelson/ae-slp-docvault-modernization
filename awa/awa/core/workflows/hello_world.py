from datetime import timedelta

from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models import HelloWorldInput

# Import MCP decorator safely for Temporal sandbox
with workflow.unsafe.imports_passed_through():
    from awa.core.decorators.exposed import exposed


@exposed("Generates a friendly greeting message for a given name")
@workflow.defn(name=constants.WORKFLOW_HELLO_WORLD)
class HelloWorldWorkflow:
    """A simple workflow that demonstrates basic Temporal workflow functionality.

    This workflow takes a name as input and returns a greeting message by calling
    the say_hello activity. It serves as a basic example for understanding
    Temporal workflow patterns in AWA.
    """

    @workflow.run
    async def run(self, workflow_input: HelloWorldInput) -> str:
        workflow.logger.info(f"Hello, {workflow_input.name}!")

        result = await workflow.execute_activity(
            constants.ACTIVITY_SAY_HELLO,
            workflow_input.name,
            start_to_close_timeout=timedelta(seconds=5),
        )

        workflow.logger.info(f"Workflow completed with result: {result}")

        return result
