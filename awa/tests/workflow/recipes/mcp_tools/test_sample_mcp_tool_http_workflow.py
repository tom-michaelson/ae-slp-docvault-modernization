"""Tests for SampleMCPToolHTTPWorkflow."""

from unittest.mock import patch

import pytest

from cookbook.recipes.workflows.mcp_tools.models.workflow_input import CalculatorInput
from cookbook.recipes.workflows.mcp_tools.sample_mcp_tool_http_workflow import SampleMCPToolHTTPWorkflow
from cookbook.recipes.workflows.mcp_tools.sample_mcp_tool_stdio_workflow import SampleMCPToolStdioWorkflow

# Constants for test assertions
EXPECTED_RESULT_KEYS = 2
EXPECTED_SUM = 8.0
EXPECTED_PRODUCT = 15.0


async def mock_execute_activity(_activity_name: str, *_args: tuple, **_kwargs: dict) -> float:
    """Mock implementation of workflow.execute_activity for testing."""
    # Extract the tool name and parameters from the _kwargs
    activity_args = _kwargs.get("args", [])
    _mcp_config, tool_name, parameters = activity_args

    if tool_name == "add":
        return parameters["a"] + parameters["b"]
    if tool_name == "multiply":
        return parameters["a"] * parameters["b"]
    raise ValueError(f"Unknown tool: {tool_name}")


class TestSampleMCPToolHTTPWorkflow:
    @pytest.mark.asyncio
    async def test_sample_mcp_tool_http_workflow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        workflow = SampleMCPToolHTTPWorkflow()
        input_data = CalculatorInput(a=5.0, b=3.0)

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
            assert "sum" in result
            assert "product" in result
            assert result["sum"] == EXPECTED_SUM
            assert result["product"] == EXPECTED_PRODUCT


class TestSampleMCPToolStdioWorkflow:
    @pytest.mark.asyncio
    async def test_sample_mcp_tool_stdio_workflow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        workflow = SampleMCPToolStdioWorkflow()
        input_data = {"a": 5.0, "b": 3.0}

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
            assert "sum" in result
            assert "product" in result
            assert result["sum"] == EXPECTED_SUM
            assert result["product"] == EXPECTED_PRODUCT
