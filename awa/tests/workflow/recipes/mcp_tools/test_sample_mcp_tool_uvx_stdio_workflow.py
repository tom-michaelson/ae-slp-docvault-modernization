"""Tests for SampleMCPToolUVXStdioWorkflow."""

from unittest.mock import patch

import pytest

from cookbook.recipes.workflows.mcp_tools.models.workflow_input import UVXStdioTimeInput
from cookbook.recipes.workflows.mcp_tools.sample_mcp_tool_uvx_stdio_workflow import SampleMCPToolUVXStdioWorkflow

# Constants for test assertions
EXPECTED_RESULT_KEYS = 6


async def mock_execute_activity(_activity_name: str, *_args: tuple, **_kwargs: dict) -> dict:
    """Mock implementation of workflow.execute_activity for testing time operations."""
    # Extract the tool name and parameters from the _kwargs
    activity_args = _kwargs.get("args", [])
    _mcp_config, tool_name, parameters = activity_args

    if tool_name == "get_current_time":
        timezone = parameters.get("timezone", "America/New_York")
        return {
            "timezone": timezone,
            "datetime": "2024-01-01T13:00:00-05:00",
            "is_dst": False,
        }
    if tool_name == "convert_time":
        source_timezone = parameters.get("source_timezone", "America/New_York")
        target_timezone = parameters.get("target_timezone", "Asia/Tokyo")
        time = parameters.get("time", "16:30")
        return {
            "source": {
                "timezone": source_timezone,
                "datetime": f"2024-01-01T{time}:00-05:00",
                "is_dst": False,
            },
            "target": {
                "timezone": target_timezone,
                "datetime": f"2024-01-01T{time}:00+09:00",
                "is_dst": False,
            },
            "time_difference": "+14.0h",
        }
    raise ValueError(f"Unknown tool: {tool_name}")


class TestSampleMCPToolUVXStdioWorkflow:
    @pytest.mark.asyncio
    async def test_sample_mcp_tool_uvx_stdio_workflow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Arrange
        workflow = SampleMCPToolUVXStdioWorkflow()
        input_data = UVXStdioTimeInput(
            source_timezone="America/New_York",
            target_timezone="Asia/Tokyo",
            time="16:30",
        )

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
            assert "source_current_time" in result
            assert "time_conversion" in result
            assert "target_current_time" in result
            assert "source_timezone" in result
            assert "target_timezone" in result
            assert "converted_time" in result

            # Check source_current_time result
            assert "timezone" in result["source_current_time"]
            assert "datetime" in result["source_current_time"]
            assert result["source_current_time"]["timezone"] == "America/New_York"

            # Check time_conversion result
            assert "source" in result["time_conversion"]
            assert "target" in result["time_conversion"]
            assert "time_difference" in result["time_conversion"]
            assert result["time_conversion"]["source"]["timezone"] == "America/New_York"
            assert result["time_conversion"]["target"]["timezone"] == "Asia/Tokyo"

            # Check target_current_time result
            assert "timezone" in result["target_current_time"]
            assert "datetime" in result["target_current_time"]
            assert result["target_current_time"]["timezone"] == "Asia/Tokyo"

            # Check input parameters are preserved
            assert result["source_timezone"] == "America/New_York"
            assert result["target_timezone"] == "Asia/Tokyo"
            assert result["converted_time"] == "16:30"
