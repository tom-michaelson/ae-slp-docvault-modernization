"""Tests for AgentModePydanticAIWorkflow."""

from unittest.mock import patch

import pytest

from cookbook.recipes.workflows.pydantic_ai.agent_mode_pydantic_ai_workflow import AgentModePydanticAIWorkflow


async def mock_read_file_activity(_path: str) -> str:
    """Mock implementation of awa_activity.read_file for testing MCP config loading."""
    return (
        '{"mcpServers": {"desktop-commander": {"command": "npx", '
        '"args": ["-y", "@wonderwhy-er/desktop-commander@latest"], "timeout_ms": 30000}}}'
    )


async def mock_execute_agent(_config: object) -> dict:
    """Mock implementation of awa_workflow.execute_agent for testing agent execution."""
    return {
        "status": "completed",
        "result": "Agent successfully completed all tasks",
        "files_created": [
            "math_calculator/src/big_math.py",
            "math_calculator/tests/test_big_math.py",
            "math_calculator/results/test_output.txt",
            "math_calculator/README.md",
            "math_calculator/OPERATIONS_SUMMARY.md",
        ],
    }


class TestAgentModePydanticAIWorkflow:
    """Test suite for AgentModePydanticAIWorkflow."""

    @pytest.mark.asyncio
    async def test_run_with_custom_prompt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test workflow execution with a custom prompt."""
        workflow = AgentModePydanticAIWorkflow()
        custom_prompt = "Create a simple Python calculator"

        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_activity.read_file",
            mock_read_file_activity,
            raising=False,
        )
        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_workflow.execute_agent",
            mock_execute_agent,
            raising=False,
        )
        monkeypatch.setattr(
            "temporalio.workflow.logger",
            type(
                "Logger",
                (),
                {
                    "info": lambda *_a, **_k: None,
                    "warning": lambda *_a, **_k: None,
                },
            )(),
            raising=False,
        )

        with patch("temporalio.workflow.info", return_value=type("Info", (), {"workflow_id": "test-workflow-id"})()):
            result = await workflow.run(custom_prompt)

        assert isinstance(result, dict)
        assert result["status"] == "completed"
        assert "files_created" in result
        assert len(result["files_created"]) == 5

    @pytest.mark.asyncio
    async def test_run_with_default_prompt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test workflow execution with the default prompt."""
        workflow = AgentModePydanticAIWorkflow()

        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_activity.read_file",
            mock_read_file_activity,
            raising=False,
        )
        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_workflow.execute_agent",
            mock_execute_agent,
            raising=False,
        )
        monkeypatch.setattr(
            "temporalio.workflow.logger",
            type(
                "Logger",
                (),
                {
                    "info": lambda *_a, **_k: None,
                    "warning": lambda *_a, **_k: None,
                },
            )(),
            raising=False,
        )

        with patch("temporalio.workflow.info", return_value=type("Info", (), {"workflow_id": "test-workflow-id"})()):
            result = await workflow.run(None)

        assert isinstance(result, dict)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_run_without_mcp_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test workflow execution when MCP config file is not found."""
        workflow = AgentModePydanticAIWorkflow()

        async def mock_read_file_error(_path: str) -> str:
            raise OSError("File not found")

        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_activity.read_file",
            mock_read_file_error,
            raising=False,
        )
        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_workflow.execute_agent",
            mock_execute_agent,
            raising=False,
        )
        monkeypatch.setattr(
            "temporalio.workflow.logger",
            type(
                "Logger",
                (),
                {
                    "info": lambda *_a, **_k: None,
                    "warning": lambda *_a, **_k: None,
                },
            )(),
            raising=False,
        )

        with patch("temporalio.workflow.info", return_value=type("Info", (), {"workflow_id": "test-workflow-id"})()):
            result = await workflow.run("Test prompt")

        assert isinstance(result, dict)
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_run_agent_execution_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test workflow behavior when agent execution fails."""
        workflow = AgentModePydanticAIWorkflow()

        async def mock_execute_agent_error(_config: object) -> None:
            raise RuntimeError("Agent execution failed")

        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_activity.read_file",
            mock_read_file_activity,
            raising=False,
        )
        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_workflow.execute_agent",
            mock_execute_agent_error,
            raising=False,
        )
        monkeypatch.setattr(
            "temporalio.workflow.logger",
            type(
                "Logger",
                (),
                {
                    "info": lambda *_a, **_k: None,
                    "warning": lambda *_a, **_k: None,
                },
            )(),
            raising=False,
        )

        with (
            patch("temporalio.workflow.info", return_value=type("Info", (), {"workflow_id": "test-workflow-id"})()),
            pytest.raises(RuntimeError, match="Agent execution failed"),
        ):
            await workflow.run("Test prompt")

    @pytest.mark.asyncio
    async def test_run_invalid_mcp_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test workflow execution with invalid MCP configuration."""
        workflow = AgentModePydanticAIWorkflow()

        async def mock_read_file_invalid(_path: str) -> str:
            return "invalid json content"

        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_activity.read_file",
            mock_read_file_invalid,
            raising=False,
        )
        monkeypatch.setattr(
            "workflows.pydantic_ai.agent_mode_pydantic_ai_workflow.awa_workflow.execute_agent",
            mock_execute_agent,
            raising=False,
        )
        monkeypatch.setattr(
            "temporalio.workflow.logger",
            type(
                "Logger",
                (),
                {
                    "info": lambda *_a, **_k: None,
                    "warning": lambda *_a, **_k: None,
                },
            )(),
            raising=False,
        )

        with patch("temporalio.workflow.info", return_value=type("Info", (), {"workflow_id": "test-workflow-id"})()):
            result = await workflow.run("Test prompt")

        assert isinstance(result, dict)
        assert result["status"] == "completed"
