"""Tests for the read_file_and_parse workflow."""

import pytest
from temporalio import activity
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from awa.core.workflows.read_file_and_parse_workflow import ReadFileAndParseWorkflow
from awa.sdk.constants import ACTIVITY_READ_FILE_AND_PARSE, AWA_DEFAULT_TASK_QUEUE
from awa.sdk.models.read_file_and_parse_input import ReadFileAndParseInput


@activity.defn(name=ACTIVITY_READ_FILE_AND_PARSE)
async def mock_read_file_and_parse_activity(inp: ReadFileAndParseInput) -> str:
    """Mock activity that returns predefined content."""
    if inp.file_path == "test.pdf":
        return "# Parsed PDF Content\n\nThis is a test PDF."
    return inp.default_content or ""


@pytest.mark.asyncio
async def test_read_file_and_parse_workflow_success() -> None:
    """Test successful execution of the read_file_and_parse workflow."""
    async with await WorkflowEnvironment.start_local(data_converter=pydantic_data_converter) as env:  # noqa: SIM117
        # Create worker with mock activity
        async with Worker(
            env.client,
            task_queue=AWA_DEFAULT_TASK_QUEUE,
            workflows=[ReadFileAndParseWorkflow],
            activities=[mock_read_file_and_parse_activity],
        ):
            # Execute workflow
            result = await env.client.execute_workflow(
                ReadFileAndParseWorkflow.run,
                ReadFileAndParseInput(
                    file_path="test.pdf",
                    default_content="Failed to parse",
                    strict=False,
                ),
                id="test-parse-workflow",
                task_queue=AWA_DEFAULT_TASK_QUEUE,
            )

            # Verify result
            assert result == "# Parsed PDF Content\n\nThis is a test PDF."


@pytest.mark.asyncio
async def test_read_file_and_parse_workflow_with_default() -> None:
    """Test workflow execution with default content when file doesn't exist."""
    async with await WorkflowEnvironment.start_local(data_converter=pydantic_data_converter) as env:  # noqa: SIM117
        # Create worker with mock activity
        async with Worker(
            env.client,
            task_queue=AWA_DEFAULT_TASK_QUEUE,
            workflows=[ReadFileAndParseWorkflow],
            activities=[mock_read_file_and_parse_activity],
        ):
            # Execute workflow
            result = await env.client.execute_workflow(
                ReadFileAndParseWorkflow.run,
                ReadFileAndParseInput(
                    file_path="nonexistent.pdf",
                    default_content="Default content",
                    strict=False,
                ),
                id="test-parse-workflow-default",
                task_queue=AWA_DEFAULT_TASK_QUEUE,
            )

            # Verify result
            assert result == "Default content"
