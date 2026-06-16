import uuid
from unittest.mock import AsyncMock, patch

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from awa.core.workflows.figma_workflow import CreatePrototypeFromFigmaWorkflow, FigmaWorkflowParams
from awa.sdk import constants as sdk_constants
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel


class TestFigmaWorkflow:
    """Test cases for the FigmaWorkflow."""

    @pytest.mark.asyncio
    async def test_workflow_success(self, workflow_client: Client) -> None:
        """Test the FigmaWorkflow with a successful agent execution."""
        task_queue_name = str(uuid.uuid4())
        output_path = "/fake/path"
        params = FigmaWorkflowParams(output_path=output_path)
        mcp_json_content = '{"some": "json"}'
        task_response = TaskResponseModel(status="completed", output="some output")

        read_file_mock = AsyncMock(return_value=mcp_json_content)
        execute_agent_spy = AsyncMock(return_value=task_response)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE)
        async def read_file_activity_mock(_path: str) -> str:
            return await read_file_mock(_path)

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def execute_agent_activity_mock(config: AgentConfiguration) -> TaskResponseModel:
            return await execute_agent_spy(config)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[CreatePrototypeFromFigmaWorkflow],
            activities=[read_file_activity_mock, execute_agent_activity_mock],
        ):
            await workflow_client.execute_workflow(
                CreatePrototypeFromFigmaWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            read_file_mock.assert_called_once_with(".mcp.json")
            execute_agent_spy.assert_called_once()
            # We can add more specific assertions on the AgentConfiguration if needed

    @pytest.mark.asyncio
    async def test_workflow_failure(self) -> None:
        """Test the FigmaWorkflow with a failed agent execution."""
        # Use WorkflowEnvironment for safer testing with pydantic data converter
        async with await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter) as env:
            task_queue_name = str(uuid.uuid4())
            output_path = "/fake/path"
            params = FigmaWorkflowParams(output_path=output_path)
            mcp_json_content = '{"some": "json"}'
            task_response = TaskResponseModel(status="failed", reason="some reason")

            read_file_mock = AsyncMock(return_value=mcp_json_content)
            execute_agent_spy = AsyncMock(return_value=task_response)

            @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE)
            async def read_file_activity_mock(_path: str) -> str:
                return await read_file_mock(_path)

            @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
            async def execute_agent_activity_mock(config: AgentConfiguration) -> TaskResponseModel:
                return await execute_agent_spy(config)

            # Patch the workflow's logger before running
            with patch("awa.core.workflows.figma_workflow.workflow.logger.error") as logger_error_mock:
                async with Worker(
                    env.client,
                    task_queue=task_queue_name,
                    workflows=[CreatePrototypeFromFigmaWorkflow],
                    activities=[read_file_activity_mock, execute_agent_activity_mock],
                ):
                    await env.client.execute_workflow(
                        CreatePrototypeFromFigmaWorkflow.run,
                        params,
                        id=str(uuid.uuid4()),
                        task_queue=task_queue_name,
                    )

                    read_file_mock.assert_called_once_with(".mcp.json")
                    execute_agent_spy.assert_called_once()
                    logger_error_mock.assert_called_once_with("Figma task failed: some reason")
