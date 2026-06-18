import uuid

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from awa.core.workflows.hello_world import HelloWorldInput, HelloWorldWorkflow
from awa.sdk import constants


@activity.defn(name=constants.ACTIVITY_SAY_HELLO)
async def say_hello_activity_mock(name: str) -> str:
    return f"mock:{name}"


class TestHelloWorldWorkflow:
    @pytest.mark.asyncio
    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    async def test_hello_world_workflow(self, workflow_client: Client) -> None:
        # Arrange
        task_queue_name = str(uuid.uuid4())
        name = "Test!"

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[HelloWorldWorkflow],
            activities=[say_hello_activity_mock],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                HelloWorldWorkflow.run,
                HelloWorldInput(name=name),
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == f"mock:{name}"
