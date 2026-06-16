from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models import HelloPoemInput
from awa.sdk.models.transform_params import TransformParams
from awa.sdk.utils.workflow import execute_baml_transform_workflow

# Import MCP decorator safely for Temporal sandbox
with workflow.unsafe.imports_passed_through():
    from awa.core.decorators.exposed import exposed


@exposed("Generates a poem")
@workflow.defn(name=constants.WORKFLOW_HELLO_POEM)
class HelloWorldWorkflow:
    """A simple workflow that executes a simple BAML transform to write a poem."""

    @workflow.run
    async def run(self, workflow_input: HelloPoemInput) -> str:
        result = await execute_baml_transform_workflow(
            TransformParams(
                baml_function_name="WritePoem",
                request=workflow_input,
            ),
        )

        workflow.logger.info(f"Workflow completed with result: {result}")

        return result
