"""Tests for SampleMCPToolNPXStdioWorkflow."""

from unittest.mock import patch

import pytest

from cookbook.recipes.workflows.mcp_tools.models.workflow_input import NPXStdioFilesystemInput
from cookbook.recipes.workflows.mcp_tools.sample_mcp_tool_npx_stdio_workflow import SampleMCPToolNPXStdioWorkflow

# Constants for test assertions
EXPECTED_RESULT_KEYS = 4
EXPECTED_LIST_DIRECTORY_LENGTH = 4


async def mock_execute_activity(_activity_name: str, *_args: tuple, **_kwargs: dict) -> dict | list:
    """Mock implementation of workflow.execute_activity for testing filesystem operations."""
    # Extract the tool name and parameters from the _kwargs
    activity_args = _kwargs.get("args", [])
    _mcp_config, tool_name, parameters = activity_args

    if tool_name == "list_directory":
        return [
            "[FILE] README.md",
            "[FILE] pyproject.toml",
            "[DIR] awa",
            "[DIR] tests",
        ]
    if tool_name == "read_file":
        return {
            "content": "# Agentic Workflow Accelerator\n\nThis is a sample README content for testing.",
            "path": parameters.get("path", "README.md"),
        }
    if tool_name == "get_file_info":
        return {
            "size": 1024,
            "type": "file",
            "path": parameters.get("path", "README.md"),
            "modifiedTime": "2025-06-24T14:00:00.000Z",
        }
    raise ValueError(f"Unknown tool: {tool_name}")


class TestSampleMCPToolNPXStdioWorkflow:
    @pytest.mark.asyncio
    async def test_sample_mcp_tool_npx_stdio_workflow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        workflow = SampleMCPToolNPXStdioWorkflow()
        input_data = NPXStdioFilesystemInput(directory_path=".")

        # Mock the workflow dependencies
        monkeypatch.setattr("temporalio.workflow.execute_activity", mock_execute_activity, raising=False)
        monkeypatch.setattr(
            "temporalio.workflow.logger",
            type(
                "Logger",
                (),
                {
                    "info": lambda *_a, **_k: None,
                    "exception": lambda *_a, **_k: None,
                },
            )(),
            raising=False,
        )

        with patch(
            "temporalio.workflow.info",
            return_value=type(
                "Info",
                (),
                {
                    "workflow_id": "test-workflow-id",
                    "task_queue": "test-task-queue",
                    "run_id": "test-run-id",
                },
            )(),
        ):
            # Act
            result = await workflow.run(input_data)

            # Assert
            assert isinstance(result, dict)
            assert len(result) == EXPECTED_RESULT_KEYS
            assert "list_directory" in result
            assert "read_file" in result
            assert "file_info" in result
            assert "explored_directory" in result

            # Check list_directory result
            assert isinstance(result["list_directory"], list)
            assert len(result["list_directory"]) == EXPECTED_LIST_DIRECTORY_LENGTH
            assert "[FILE] README.md" in result["list_directory"]
            assert "[DIR] awa" in result["list_directory"]

            # Check read_file result
            assert "content" in result["read_file"]
            assert "Agentic Workflow Accelerator" in result["read_file"]["content"]

            # Check file_info result
            assert "size" in result["file_info"]
            assert "type" in result["file_info"]
            assert result["file_info"]["type"] == "file"

            # Check explored_directory
            assert result["explored_directory"] == "."
