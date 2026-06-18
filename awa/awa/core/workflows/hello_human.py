from datetime import timedelta

from temporalio import workflow

from awa.core.models.hitl import HITLInput
from awa.sdk import constants


@workflow.defn(name=constants.WORKFLOW_HELLO_HUMAN)
class HelloHumanWorkflow:
    """A workflow that demonstrates Human-in-the-Loop interaction.

    This workflow executes a HITL child workflow that uses signal handlers
    to receive user input, then returns a personalized greeting.

    The child workflow (HITLChildWorkflow) handles:
    - Setting up the HITL context for UI display
    - Receiving responses via the submit_response signal
    - Managing timeouts and response state
    """

    @workflow.run
    async def run(self) -> str:
        """Run the awa-hello-human workflow with HITL name collection.

        This delegates to the HITL child workflow which internally uses
        signal handlers to receive the user's response.
        """
        # Create HITL input to ask for the user's name
        hitl_input = HITLInput(
            title="Hello Human Workflow",
            description="Please provide your name so we can greet you properly.",
            markdown="## Welcome!\n\nWhat's your name?",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "title": "Your Name",
                        "description": "Enter your full name",
                    },
                },
                "required": ["name"],
            },
            timeout_seconds=900,  # 15 minutes timeout
            non_blocking=False,  # Wait for response
            chat_mode=False,
        )

        # Execute the HITL child workflow which handles signal reception
        # The child workflow will:
        # 1. Set up context that can be queried by the UI
        # 2. Wait for a submit_response signal with the user's input
        # 3. Return the response or timeout
        hitl_result = await workflow.execute_child_workflow(
            constants.WORKFLOW_HITL,
            hitl_input,
            id=f"{workflow.info().workflow_id}-hitl",
        )

        # Handle both dict and HITLOutput object cases (Temporal serialization)
        if isinstance(hitl_result, dict):
            # Result is a dictionary, access fields directly
            response = hitl_result.get("response")
            timed_out = hitl_result.get("timed_out", False)
            if response and not timed_out:
                response_data = response.get("data", {})
                user_name = response_data.get("name", "Anonymous")
            else:
                user_name = "Anonymous"
        # Result is an HITLOutput object
        elif hitl_result.response and not hitl_result.timed_out:
            user_name = hitl_result.response.data.get("name", "Anonymous")
        else:
            user_name = "Anonymous"

        # Return the greeting using the say_hello activity
        return await workflow.execute_activity(
            constants.ACTIVITY_SAY_HELLO,
            user_name,
            start_to_close_timeout=timedelta(seconds=5),
        )
