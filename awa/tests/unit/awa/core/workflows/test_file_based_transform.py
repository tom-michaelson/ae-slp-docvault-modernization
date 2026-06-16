import json
import uuid
from unittest.mock import AsyncMock

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from awa.core.workflows.file_based_transform import FileBasedTransformInput, TransformFileWorkflow
from awa.sdk import constants


class TestFileBasedTransformWorkflow:
    @pytest.mark.asyncio
    async def test_file_based_transform_workflow(self, workflow_client: Client) -> None:
        # Arrange
        task_queue_name = str(uuid.uuid4())
        input_path = "/test/input.json"
        output_path = "/test/output.txt"
        request_data = {"tone": "dramatic", "style": "sonnet"}
        poem_text = "This is a dramatic sonnet."

        input_obj = FileBasedTransformInput(input_path=input_path, output_path=output_path)

        # Mock activities
        @activity.defn(name=constants.ACTIVITY_READ_FILE)
        async def read_file_activity_mock(_path: str) -> str:
            return json.dumps(request_data)

        @activity.defn(name=constants.ACTIVITY_TRANSFORM)
        async def transform_activity_mock(_params: dict) -> dict:
            return {"poem": poem_text}

        write_file_spy = AsyncMock()

        @activity.defn(name=constants.ACTIVITY_WRITE_FILE)
        async def write_file_activity_mock(path: str, content: str) -> None:
            await write_file_spy(path, content)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformFileWorkflow],
            activities=[read_file_activity_mock, transform_activity_mock, write_file_activity_mock],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                TransformFileWorkflow.run,
                input_obj,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == f"Poem successfully written to {output_path}"
            write_file_spy.assert_called_once_with(output_path, poem_text)
