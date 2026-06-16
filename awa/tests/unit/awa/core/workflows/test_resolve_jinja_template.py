import uuid

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from awa.core.workflows.resolve_jinja_template import ResolveTemplateInput, ResolveTemplateWorkflow
from awa.sdk import constants as sdk_constants


@activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
async def resolve_template_activity_mock(input_str: str) -> str:
    return f"{{ result: {{ data: '{input_str}'}} }}"


class TestResolveJinjnaTemplateWorkflow:
    @pytest.mark.asyncio
    async def test_resolve_jinja_template_workflow(self, workflow_client: Client) -> None:
        # Arrange
        task_queue_name = str(uuid.uuid4())
        input_str = "Test!"

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ResolveTemplateWorkflow],
            activities=[resolve_template_activity_mock],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ResolveTemplateWorkflow.run,
                ResolveTemplateInput(input_str=input_str),
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == f"{{ result: {{ data: '{input_str}'}} }}"
