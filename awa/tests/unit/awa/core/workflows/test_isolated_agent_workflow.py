"""Unit and integration tests for the isolated agent workflow."""

import sys
import uuid
from pathlib import Path
from typing import Any, Never
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio import activity, exceptions
from temporalio.client import Client, WorkflowFailureError
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

from awa.core.workflows.isolated_agent_workflow import IsolatedAgentChildWorkflow
from awa.sdk import constants as sdk_constants
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum
from awa.sdk.models.agent_modes.isolated_agent_models import (
    IsolatedAgentEnvironmentInfo,
    IsolatedAgentEnvironmentResult,
    IsolatedAgentParams,
)
from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel

PATH_PREFIX = "" if sys.platform != "win32" else "C:"


@pytest.fixture
def sample_agent_config_act() -> AgentConfiguration:
    """Create a sample agent configuration for ACT mode."""
    return AgentConfiguration(
        mode=AgentModeEnum.ACT,
        provider=AgentProviderEnum.CLAUDE,
        prompt="Test prompt for ACT mode",
    )


@pytest.fixture
def sample_agent_config_analyze() -> AgentConfiguration:
    """Create a sample agent configuration for ANALYZE mode."""
    return AgentConfiguration(
        mode=AgentModeEnum.ANALYZE,
        provider=AgentProviderEnum.CLAUDE,
        prompt="Test prompt for ANALYZE mode",
    )


@pytest.fixture
def sample_environment_info(tmp_path: Path) -> IsolatedAgentEnvironmentInfo:
    """Create sample environment info for testing."""
    return IsolatedAgentEnvironmentInfo(
        environment_path=str(tmp_path / "worktree"),
        source_directory_path=str(tmp_path / "source"),
        source_branch="main",
    )


@pytest.fixture
def sample_isolated_agent_params_act(
    sample_agent_config_act: AgentConfiguration,
    tmp_path: Path,
) -> IsolatedAgentParams:
    """Create sample isolated agent parameters for ACT mode."""
    return IsolatedAgentParams(
        source_directory=str(tmp_path / "source"),
        source_branch="main",
        agent_config=sample_agent_config_act,
    )


@pytest.fixture
def sample_isolated_agent_params_analyze(
    sample_agent_config_analyze: AgentConfiguration,
    tmp_path: Path,
) -> IsolatedAgentParams:
    """Create sample isolated agent parameters for ANALYZE mode."""
    return IsolatedAgentParams(
        source_directory=str(tmp_path / "source"),
        agent_config=sample_agent_config_analyze,
        output_directory="test_output",
    )


class TestIsolatedAgentChildWorkflowUnit:
    """Unit tests for the IsolatedAgentChildWorkflow using mocks."""

    @pytest.mark.asyncio
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.logger")
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.execute_activity")
    async def test_run_successful_act_mode(
        self,
        mock_execute_activity: AsyncMock,
        mock_logger: MagicMock,
        sample_isolated_agent_params_act: IsolatedAgentParams,
        sample_environment_info: IsolatedAgentEnvironmentInfo,
    ) -> None:
        """Test successful workflow execution in ACT mode."""
        workflow = IsolatedAgentChildWorkflow()
        isolated_config = sample_isolated_agent_params_act.agent_config.model_copy()
        isolated_config.working_directory = sample_environment_info.environment_path

        mock_execute_activity.side_effect = [
            (
                IsolatedAgentEnvironmentResult(
                    success=True,
                    message="Setup successful",
                    environment_info=sample_environment_info,
                ),
                isolated_config,
            ),
            TaskResponseModel(status="completed", output="Agent completed"),
            IsolatedAgentEnvironmentResult(success=True, message="Merged"),
            IsolatedAgentEnvironmentResult(success=True, message="Cleaned"),
        ]

        result = await workflow.run(sample_isolated_agent_params_act)

        assert result.status == "completed"
        assert result.output == "Agent completed"
        assert mock_execute_activity.call_count == 4
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.logger")
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.execute_activity")
    async def test_run_successful_analyze_mode(
        self,
        mock_execute_activity: AsyncMock,
        mock_logger: MagicMock,
        sample_isolated_agent_params_analyze: IsolatedAgentParams,
        sample_environment_info: IsolatedAgentEnvironmentInfo,
    ) -> None:
        """Test successful workflow execution in ANALYZE mode."""
        workflow = IsolatedAgentChildWorkflow()
        isolated_config = sample_isolated_agent_params_analyze.agent_config.model_copy()
        isolated_config.working_directory = sample_environment_info.environment_path

        mock_execute_activity.side_effect = [
            (
                IsolatedAgentEnvironmentResult(
                    success=True,
                    message="Setup successful",
                    environment_info=sample_environment_info,
                ),
                isolated_config,
            ),
            TaskResponseModel(status="completed", output="Agent analyzed"),
            IsolatedAgentEnvironmentResult(success=True, message="Copied"),
            IsolatedAgentEnvironmentResult(success=True, message="Cleaned"),
        ]

        result = await workflow.run(sample_isolated_agent_params_analyze)

        assert result.status == "completed"
        assert result.output == "Agent analyzed"
        assert mock_execute_activity.call_count == 4
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.logger")
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.execute_activity")
    async def test_run_setup_failure(
        self,
        mock_execute_activity: AsyncMock,
        mock_logger: MagicMock,
        sample_isolated_agent_params_act: IsolatedAgentParams,
    ) -> None:
        """Test workflow execution when setup fails."""
        workflow = IsolatedAgentChildWorkflow()
        mock_execute_activity.side_effect = [
            (
                IsolatedAgentEnvironmentResult(
                    success=False,
                    message="Setup failed",
                ),
                None,
            ),
        ]

        with pytest.raises(exceptions.ApplicationError) as err:
            await workflow.run(sample_isolated_agent_params_act)

        assert "Failed to setup isolated environment: Setup failed" in str(err.value)
        assert mock_execute_activity.call_count == 1
        mock_logger.error.assert_called_with(
            "Failed to setup isolated environment: Setup failed",
        )

    @pytest.mark.asyncio
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.logger")
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.execute_activity")
    async def test_agent_execution_failure(
        self,
        mock_execute_activity: AsyncMock,
        mock_logger: MagicMock,
        sample_isolated_agent_params_act: IsolatedAgentParams,
        sample_environment_info: IsolatedAgentEnvironmentInfo,
    ) -> None:
        """Test workflow when agent execution fails."""
        workflow = IsolatedAgentChildWorkflow()
        isolated_config = sample_isolated_agent_params_act.agent_config.model_copy()
        isolated_config.working_directory = sample_environment_info.environment_path
        agent_failure_reason = "Agent process exploded"

        mock_execute_activity.side_effect = [
            (
                IsolatedAgentEnvironmentResult(
                    success=True,
                    message="Setup successful",
                    environment_info=sample_environment_info,
                ),
                isolated_config,
            ),
            TaskResponseModel(status="failed", reason=agent_failure_reason),
            IsolatedAgentEnvironmentResult(success=True, message="Cleaned up"),
        ]

        with pytest.raises(exceptions.ApplicationError) as err:
            await workflow.run(sample_isolated_agent_params_act)

        assert agent_failure_reason in str(err.value)
        assert mock_execute_activity.call_count == 3
        mock_logger.error.assert_called_with(
            f"Agent execution failed: {agent_failure_reason}",
        )

    @pytest.mark.asyncio
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.logger")
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.execute_activity")
    async def test_merge_failure_act_mode(
        self,
        mock_execute_activity: AsyncMock,
        mock_logger: MagicMock,
        sample_isolated_agent_params_act: IsolatedAgentParams,
        sample_environment_info: IsolatedAgentEnvironmentInfo,
    ) -> None:
        """Test workflow when merge fails in ACT mode."""
        workflow = IsolatedAgentChildWorkflow()
        isolated_config = sample_isolated_agent_params_act.agent_config.model_copy()
        isolated_config.working_directory = sample_environment_info.environment_path

        mock_execute_activity.side_effect = [
            (
                IsolatedAgentEnvironmentResult(
                    success=True,
                    message="Setup successful",
                    environment_info=sample_environment_info,
                ),
                isolated_config,
            ),
            TaskResponseModel(status="completed", output="Agent completed"),
            IsolatedAgentEnvironmentResult(success=False, message="Merge conflict!"),
            IsolatedAgentEnvironmentResult(success=True, message="Cleaned up"),
        ]

        result = await workflow.run(sample_isolated_agent_params_act)

        assert result.status == "completed"
        assert "Agent completed but merge failed: Merge conflict!" in result.reason
        mock_logger.warning.assert_called_with(
            "Failed to merge changes: Merge conflict!",
        )
        assert mock_execute_activity.call_count == 4

    @pytest.mark.asyncio
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.logger")
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.execute_activity")
    async def test_copy_failure_analyze_mode(
        self,
        mock_execute_activity: AsyncMock,
        mock_logger: MagicMock,
        sample_isolated_agent_params_analyze: IsolatedAgentParams,
        sample_environment_info: IsolatedAgentEnvironmentInfo,
    ) -> None:
        """Test workflow when copy fails in ANALYZE mode."""
        workflow = IsolatedAgentChildWorkflow()
        isolated_config = sample_isolated_agent_params_analyze.agent_config.model_copy()
        isolated_config.working_directory = sample_environment_info.environment_path

        mock_execute_activity.side_effect = [
            (
                IsolatedAgentEnvironmentResult(
                    success=True,
                    message="Setup successful",
                    environment_info=sample_environment_info,
                ),
                isolated_config,
            ),
            TaskResponseModel(status="completed", output="Agent analyzed"),
            IsolatedAgentEnvironmentResult(success=False, message="Cannot copy!"),
            IsolatedAgentEnvironmentResult(success=True, message="Cleaned up"),
        ]

        result = await workflow.run(sample_isolated_agent_params_analyze)

        assert result.status == "completed"
        assert "Agent completed but output copy failed: Cannot copy!" in result.reason
        mock_logger.warning.assert_called_with(
            "Failed to copy analyze outputs: Cannot copy!",
        )
        assert mock_execute_activity.call_count == 4

    @pytest.mark.asyncio
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.logger")
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.execute_activity")
    async def test_cleanup_failure_does_not_fail_workflow(
        self,
        mock_execute_activity: AsyncMock,
        mock_logger: MagicMock,
        sample_isolated_agent_params_act: IsolatedAgentParams,
        sample_environment_info: IsolatedAgentEnvironmentInfo,
    ) -> None:
        """Test that a cleanup failure is logged but does not fail the workflow."""
        workflow = IsolatedAgentChildWorkflow()
        isolated_config = sample_isolated_agent_params_act.agent_config.model_copy()
        isolated_config.working_directory = sample_environment_info.environment_path

        mock_execute_activity.side_effect = [
            (
                IsolatedAgentEnvironmentResult(
                    success=True,
                    message="Setup successful",
                    environment_info=sample_environment_info,
                ),
                isolated_config,
            ),
            TaskResponseModel(status="completed", output="Agent completed"),
            IsolatedAgentEnvironmentResult(success=True, message="Merged"),
            IsolatedAgentEnvironmentResult(success=False, message="Cleanup failed!"),
        ]

        result = await workflow.run(sample_isolated_agent_params_act)

        assert result.status == "completed"
        mock_logger.error.assert_called_with(
            "Environment cleanup failed: Cleanup failed!",
        )
        assert mock_execute_activity.call_count == 4

    @pytest.mark.asyncio
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.logger")
    @patch("awa.core.workflows.isolated_agent_workflow.workflow.execute_activity")
    async def test_cleanup_always_called_on_agent_failure(
        self,
        mock_execute_activity: AsyncMock,
        mock_logger: MagicMock,
        sample_isolated_agent_params_act: IsolatedAgentParams,
        sample_environment_info: IsolatedAgentEnvironmentInfo,
    ) -> None:
        """Test that cleanup is always called even when the agent fails."""
        workflow = IsolatedAgentChildWorkflow()
        isolated_config = sample_isolated_agent_params_act.agent_config.model_copy()
        isolated_config.working_directory = sample_environment_info.environment_path

        mock_execute_activity.side_effect = [
            (
                IsolatedAgentEnvironmentResult(
                    success=True,
                    message="Setup successful",
                    environment_info=sample_environment_info,
                ),
                isolated_config,
            ),
            ValueError("Agent crashed"),  # Simulate activity failure
            IsolatedAgentEnvironmentResult(success=True, message="Cleaned up"),
        ]

        with pytest.raises(ValueError, match="Agent crashed"):
            await workflow.run(sample_isolated_agent_params_act)

        assert mock_execute_activity.call_count == 3
        last_call_activity_name = mock_execute_activity.call_args_list[2].args[0].__name__
        assert "cleanup_isolated_environment_activity" in last_call_activity_name
        mock_logger.info.assert_called()


class TestIsolatedAgentChildWorkflowIntegration:
    """Integration tests for the IsolatedAgentChildWorkflow."""

    @pytest.mark.asyncio
    async def test_successful_act_mode_integration(
        self,
        workflow_client: Client,
        sample_agent_config_act: AgentConfiguration,
    ) -> None:
        """Test a successful workflow execution in ACT mode with a real worker."""
        task_queue = str(uuid.uuid4())
        env_info = IsolatedAgentEnvironmentInfo(
            environment_path=str(Path(f"{PATH_PREFIX}/fake/worktree").resolve()),
            source_directory_path=str(Path(f"{PATH_PREFIX}/fake/source").resolve()),
            source_branch="main",
        )
        isolated_config = sample_agent_config_act.model_copy()
        isolated_config.working_directory = env_info.environment_path

        @activity.defn(name=sdk_constants.ACTIVITY_SETUP_ISOLATED_AGENT)
        async def setup_isolated_agent_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> tuple[IsolatedAgentEnvironmentResult, AgentConfiguration]:
            return (
                IsolatedAgentEnvironmentResult(
                    success=True,
                    message="Setup successful",
                    environment_info=env_info,
                ),
                isolated_config,
            )

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def execute_agent_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> TaskResponseModel:
            return TaskResponseModel(status="completed", output="Agent completed")

        @activity.defn(name=sdk_constants.ACTIVITY_MERGE_WORKTREE_CHANGES)
        async def merge_worktree_changes_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> IsolatedAgentEnvironmentResult:
            return IsolatedAgentEnvironmentResult(success=True, message="Merged")

        @activity.defn(name=sdk_constants.ACTIVITY_COPY_ANALYZE_OUTPUTS)
        async def copy_analyze_outputs_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> Never:
            raise RuntimeError("Should not be called")

        @activity.defn(name=sdk_constants.ACTIVITY_CLEANUP_ISOLATED_AGENT)
        async def cleanup_isolated_environment_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> IsolatedAgentEnvironmentResult:
            return IsolatedAgentEnvironmentResult(success=True, message="Cleaned up")

        params = IsolatedAgentParams(
            source_directory="/fake/source",
            source_branch="main",
            agent_config=sample_agent_config_act,
        )

        async with Worker(
            workflow_client,
            task_queue=task_queue,
            workflows=[IsolatedAgentChildWorkflow],
            activities=[
                setup_isolated_agent_activity_mock,
                execute_agent_activity_mock,
                merge_worktree_changes_activity_mock,
                copy_analyze_outputs_activity_mock,
                cleanup_isolated_environment_activity_mock,
            ],
        ):
            result = await workflow_client.execute_workflow(
                IsolatedAgentChildWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue,
            )
            assert result.status == "completed"
            assert result.output == "Agent completed"

    @pytest.mark.asyncio
    async def test_successful_analyze_mode_integration(
        self,
        workflow_client: Client,
        sample_agent_config_analyze: AgentConfiguration,
    ) -> None:
        """Test a successful workflow execution in ANALYZE mode with a real worker."""
        task_queue = str(uuid.uuid4())
        env_info = IsolatedAgentEnvironmentInfo(
            environment_path=str(Path(f"{PATH_PREFIX}/fake/tempdir").resolve()),
            source_directory_path=str(Path(f"{PATH_PREFIX}/fake/source").resolve()),
            source_branch=None,
        )
        isolated_config = sample_agent_config_analyze.model_copy()
        isolated_config.working_directory = env_info.environment_path

        @activity.defn(name=sdk_constants.ACTIVITY_SETUP_ISOLATED_AGENT)
        async def setup_isolated_agent_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> tuple[IsolatedAgentEnvironmentResult, AgentConfiguration]:
            return (
                IsolatedAgentEnvironmentResult(
                    success=True,
                    message="Setup successful",
                    environment_info=env_info,
                ),
                isolated_config,
            )

        @activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
        async def execute_agent_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> TaskResponseModel:
            return TaskResponseModel(status="completed", output="Agent analyzed")

        @activity.defn(name=sdk_constants.ACTIVITY_MERGE_WORKTREE_CHANGES)
        async def merge_worktree_changes_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> Never:
            raise RuntimeError("Should not be called")

        @activity.defn(name=sdk_constants.ACTIVITY_COPY_ANALYZE_OUTPUTS)
        async def copy_analyze_outputs_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> IsolatedAgentEnvironmentResult:
            return IsolatedAgentEnvironmentResult(success=True, message="Copied")

        @activity.defn(name=sdk_constants.ACTIVITY_CLEANUP_ISOLATED_AGENT)
        async def cleanup_isolated_environment_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> IsolatedAgentEnvironmentResult:
            return IsolatedAgentEnvironmentResult(success=True, message="Cleaned up")

        params = IsolatedAgentParams(
            source_directory="/fake/source",
            agent_config=sample_agent_config_analyze,
            output_directory="test_output",
        )

        async with Worker(
            workflow_client,
            task_queue=task_queue,
            workflows=[IsolatedAgentChildWorkflow],
            activities=[
                setup_isolated_agent_activity_mock,
                execute_agent_activity_mock,
                merge_worktree_changes_activity_mock,
                copy_analyze_outputs_activity_mock,
                cleanup_isolated_environment_activity_mock,
            ],
        ):
            result = await workflow_client.execute_workflow(
                IsolatedAgentChildWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue,
            )
            assert result.status == "completed"
            assert result.output == "Agent analyzed"

    @pytest.mark.asyncio
    async def test_setup_failure_integration(
        self,
        workflow_client: Client,
        sample_isolated_agent_params_act: IsolatedAgentParams,
    ) -> None:
        """Test workflow execution when setup fails with a real worker."""
        task_queue = str(uuid.uuid4())

        @activity.defn(name=sdk_constants.ACTIVITY_SETUP_ISOLATED_AGENT)
        async def setup_isolated_agent_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> tuple[IsolatedAgentEnvironmentResult, None]:
            return (
                IsolatedAgentEnvironmentResult(
                    success=False,
                    message="Setup integration test fail",
                ),
                None,
            )

        @activity.defn(name=sdk_constants.ACTIVITY_CLEANUP_ISOLATED_AGENT)
        async def cleanup_isolated_environment_activity_mock(
            *_args: Any,  # noqa: ANN401
            **_kwargs: Any,  # noqa: ANN401
        ) -> IsolatedAgentEnvironmentResult:
            return IsolatedAgentEnvironmentResult(success=True, message="Cleaned up")

        async with Worker(
            workflow_client,
            task_queue=task_queue,
            workflows=[IsolatedAgentChildWorkflow],
            activities=[
                setup_isolated_agent_activity_mock,
                cleanup_isolated_environment_activity_mock,
            ],
        ):
            with pytest.raises(WorkflowFailureError) as exc_info:
                await workflow_client.execute_workflow(
                    IsolatedAgentChildWorkflow.run,
                    sample_isolated_agent_params_act,
                    id=str(uuid.uuid4()),
                    task_queue=task_queue,
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
            assert isinstance(exc_info.value.cause, exceptions.ApplicationError)
            assert "Failed to setup isolated environment" in str(exc_info.value.cause)
