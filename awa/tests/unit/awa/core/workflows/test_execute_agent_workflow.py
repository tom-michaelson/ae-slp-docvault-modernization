"""Unit tests for ExecuteAgentWorkflow."""

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from awa.core.workflows.execute_agent_workflow import ExecuteAgentWorkflow
from awa.sdk import constants as sdk_constants
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum
from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel


class TestExecuteAgentWorkflow:
    """Test cases for ExecuteAgentWorkflow."""

    def test_workflow_class_exists(self) -> None:
        """Test that ExecuteAgentWorkflow class exists and is instantiable."""
        workflow = ExecuteAgentWorkflow()
        assert workflow is not None
        assert hasattr(workflow, "run")

    @pytest.mark.asyncio
    async def test_run_with_direct_prompt_isolated(self) -> None:
        """Test workflow run with direct prompt using isolated environment."""
        from temporalio.testing import WorkflowEnvironment

        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = TaskResponseModel(
            status="success",
            reason="Agent executed successfully",
            output="Agent executed successfully",
        )
        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ACT,
            provider=AgentProviderEnum.CLAUDE,
            prompt="Hello, please help me with this task",
            timeout_seconds=60,
        )

        execute_agent_mock = MagicMock(return_value=expected_result.model_dump())

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def mock_execute_agent(config: AgentConfiguration) -> dict[str, Any]:
            return execute_agent_mock(config)

        # Use time-skipping environment for faster, isolated testing
        env = await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter)
        try:
            async with Worker(
                env.client,
                task_queue=task_queue_name,
                workflows=[ExecuteAgentWorkflow],
                activities=[mock_execute_agent],
            ):
                # Act
                result = await env.client.execute_workflow(
                    ExecuteAgentWorkflow.run,
                    agent_config,
                    id=str(uuid.uuid4()),
                    task_queue=task_queue_name,
                )

                # Assert
                assert result == expected_result
                execute_agent_mock.assert_called_once_with(agent_config)
        finally:
            await env.shutdown()

    @pytest.mark.asyncio
    async def test_run_with_direct_prompt(self, workflow_client: Client) -> None:
        """Test workflow run with direct prompt (no build_prompt_params)."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = TaskResponseModel(
            status="success",
            reason="Agent executed successfully",
            output="Agent executed successfully",
        )
        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ACT,
            provider=AgentProviderEnum.CLAUDE,
            prompt="Hello, please help me with this task",
            timeout_seconds=60,
        )

        execute_agent_mock = MagicMock(return_value=expected_result.model_dump())

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def mock_execute_agent(config: AgentConfiguration) -> dict[str, Any]:
            return execute_agent_mock(config)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ExecuteAgentWorkflow],
            activities=[mock_execute_agent],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ExecuteAgentWorkflow.run,
                agent_config,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == expected_result
            execute_agent_mock.assert_called_once_with(agent_config)

    @pytest.mark.asyncio
    async def test_run_with_custom_timeout(self, workflow_client: Client) -> None:
        """Test workflow run with custom timeout configuration."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = TaskResponseModel(
            status="success",
            reason="Agent executed with custom timeout",
            output="Agent executed with custom timeout",
        )
        custom_timeout = 300

        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ACT,
            provider=AgentProviderEnum.CLAUDE,
            prompt="Test prompt",
            timeout_seconds=custom_timeout,
        )

        execute_agent_mock = MagicMock(return_value=expected_result.model_dump())

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def mock_execute_agent(config: AgentConfiguration) -> dict[str, Any]:
            return execute_agent_mock(config)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ExecuteAgentWorkflow],
            activities=[mock_execute_agent],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ExecuteAgentWorkflow.run,
                agent_config,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == expected_result
            execute_agent_mock.assert_called_once_with(agent_config)

    @pytest.mark.asyncio
    async def test_run_with_no_timeout_uses_default(self, workflow_client: Client) -> None:
        """Test workflow run with no timeout specified uses default."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = TaskResponseModel(
            status="success",
            reason="Agent executed with default timeout",
            output="Agent executed with default timeout",
        )

        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ACT,
            provider=AgentProviderEnum.CLAUDE,
            prompt="Test prompt",
            timeout_seconds=None,  # No timeout specified
        )

        execute_agent_mock = MagicMock(return_value=expected_result.model_dump())

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def mock_execute_agent(config: AgentConfiguration) -> dict[str, Any]:
            return execute_agent_mock(config)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ExecuteAgentWorkflow],
            activities=[mock_execute_agent],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ExecuteAgentWorkflow.run,
                agent_config,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == expected_result
            execute_agent_mock.assert_called_once_with(agent_config)

    @pytest.mark.asyncio
    async def test_run_with_complex_configuration(self, workflow_client: Client, tmp_path: Any) -> None:  # noqa: ANN401
        """Test workflow run with complex agent configuration."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = TaskResponseModel(
            status="success",
            reason="Complex task completed",
            output="Complex task completed",
        )

        # Use tmp_path fixture for safe temporary paths
        command_file = tmp_path / "commands.txt"
        working_dir = tmp_path / "workspace"
        working_dir.mkdir()
        command_file.write_text("test commands")

        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ANALYZE,
            provider=AgentProviderEnum.CLAUDE,
            prompt="Complex task prompt",
            command_file_path=str(command_file),
            working_directory=str(working_dir),
            initialize=True,
            timeout_seconds=180,
        )

        execute_agent_mock = MagicMock(return_value=expected_result.model_dump())

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def mock_execute_agent(config: AgentConfiguration) -> dict[str, Any]:
            return execute_agent_mock(config)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ExecuteAgentWorkflow],
            activities=[mock_execute_agent],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ExecuteAgentWorkflow.run,
                agent_config,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == expected_result
            execute_agent_mock.assert_called_once_with(agent_config)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "output_value",
        [
            "String result",
            '{"key": "value", "number": 42}',
            '["item1", "item2", "item3"]',
            "42",
            "true",
        ],
    )
    async def test_run_returns_various_result_types(self, workflow_client: Client, output_value: str) -> None:
        """Test workflow run can return various result types in the output field."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = TaskResponseModel(
            status="success",
            reason="Agent executed successfully",
            output=output_value,
        )

        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ACT,
            provider=AgentProviderEnum.CLAUDE,
            prompt="Test prompt",
        )

        execute_agent_mock = MagicMock(return_value=expected_result.model_dump())

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def mock_execute_agent(config: AgentConfiguration) -> dict[str, Any]:
            return execute_agent_mock(config)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ExecuteAgentWorkflow],
            activities=[mock_execute_agent],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ExecuteAgentWorkflow.run,
                agent_config,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == expected_result
            execute_agent_mock.assert_called_once_with(agent_config)

    @pytest.mark.asyncio
    async def test_run_with_empty_prompt(self, workflow_client: Client) -> None:
        """Test workflow run with empty prompt."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = TaskResponseModel(
            status="success",
            reason="Agent executed with empty prompt",
            output="Agent executed with empty prompt",
        )

        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ACT,
            provider=AgentProviderEnum.CLAUDE,
            prompt="",  # Empty prompt
        )

        execute_agent_mock = MagicMock(return_value=expected_result.model_dump())

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def mock_execute_agent(config: AgentConfiguration) -> dict[str, Any]:
            return execute_agent_mock(config)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ExecuteAgentWorkflow],
            activities=[mock_execute_agent],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ExecuteAgentWorkflow.run,
                agent_config,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == expected_result
            execute_agent_mock.assert_called_once_with(agent_config)

    @pytest.mark.asyncio
    async def test_run_with_different_agent_modes(self, workflow_client: Client) -> None:
        """Test workflow run with different agent modes."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = TaskResponseModel(
            status="success",
            reason="Agent executed with ANALYZE mode",
            output="Agent executed with ANALYZE mode",
        )

        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ANALYZE,
            provider=AgentProviderEnum.CLAUDE,
            prompt="Analyze this code",
            timeout_seconds=120,
        )

        execute_agent_mock = MagicMock(return_value=expected_result.model_dump())

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def mock_execute_agent(config: AgentConfiguration) -> dict[str, Any]:
            return execute_agent_mock(config)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[ExecuteAgentWorkflow],
            activities=[mock_execute_agent],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                ExecuteAgentWorkflow.run,
                agent_config,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Assert
            assert result == expected_result
            execute_agent_mock.assert_called_once()

            # Verify the agent config was passed correctly
            called_config = execute_agent_mock.call_args[0][0]
            assert called_config.mode == AgentModeEnum.ANALYZE
            assert called_config.provider == AgentProviderEnum.CLAUDE
            assert called_config.prompt == "Analyze this code"
