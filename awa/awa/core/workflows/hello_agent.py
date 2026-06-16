from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models import HelloPoemAgentInput
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum

# Import MCP decorator safely for Temporal sandbox
with workflow.unsafe.imports_passed_through():
    from awa.core.decorators.exposed import exposed


@exposed("Generates a poem using an agent")
@workflow.defn(name=constants.WORKFLOW_HELLO_POEM_AGENT)
class HelloWorldWorkflow:
    """A simple workflow that executes an agent to write a poem."""

    @workflow.run
    async def run(self, workflow_input: HelloPoemAgentInput) -> str:
        workflow_id = workflow.info().workflow_id

        generation_agent_config = AgentConfiguration(
            mode=AgentModeEnum.ANALYZE,
            provider=workflow_input.provider,
            prompt=f"""
            Write a rhyming 3-stanza poem about the following noun, verb, and adjective.
            Use a Task subagent to independently critique your poem and improve it.
            Perform this iterative review loop at least 5 times, and then return the final polished poem.

            <noun>{workflow_input.noun}</noun>
            <verb>{workflow_input.verb}</verb>
            <adjective>{workflow_input.adjective}</adjective>
            """,
            initialize=False,
            stream_enabled=True,
        )

        result = await workflow.execute_child_workflow(
            constants.WORKFLOW_EXECUTE_AGENT,
            generation_agent_config,
            id=f"HelloPoem-{workflow_id}",
            execution_timeout=workflow.timedelta(seconds=1800),
        )

        workflow.logger.info(f"Workflow completed with result: {result}")

        return result
