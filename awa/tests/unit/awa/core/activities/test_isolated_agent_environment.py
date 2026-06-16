"""Tests for isolated agent environment activities."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.isolated_agent_environment import setup_isolated_agent_activity
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum
from awa.sdk.models.agent_modes.isolated_agent_models import (
    IsolatedAgentEnvironmentInfo,
    IsolatedAgentEnvironmentResult,
)

PATH_PREFIX = "" if sys.platform != "win32" else "C:"


@pytest.fixture
def sample_agent_config() -> AgentConfiguration:
    """Create a sample agent configuration for testing."""
    working_dir = str(Path(f"{PATH_PREFIX}/original/path").resolve())
    return AgentConfiguration(
        provider=AgentProviderEnum.CLAUDE,
        mode=AgentModeEnum.ACT,
        prompt="Test prompt",
        working_directory=working_dir,
    )


@pytest.fixture
def sample_environment_info() -> IsolatedAgentEnvironmentInfo:
    """Create sample environment info for testing."""
    return IsolatedAgentEnvironmentInfo(
        environment_path=str(
            Path(f"{PATH_PREFIX}/test/repo_worktrees/test_worktree").resolve(),
        ),
        source_directory_path=str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
        source_branch="main",
    )


class TestSetupIsolatedAgentActivity:
    """Test cases for setup_isolated_agent_activity."""

    @pytest.mark.asyncio
    @patch("awa.core.activities.isolated_agent_environment.setup_isolated_agent_git_activity")
    async def test_setup_isolated_agent_act_mode_requires_branch(
        self,
        mock_setup_git: AsyncMock,
        sample_agent_config: AgentConfiguration,
        sample_environment_info: IsolatedAgentEnvironmentInfo,
    ) -> None:
        """Test that ACT mode requires a source_branch parameter."""
        # Arrange
        act_config = sample_agent_config.model_copy()
        act_config.mode = AgentModeEnum.ACT

        mock_setup_git.return_value = (
            IsolatedAgentEnvironmentResult(success=True, message="Success", environment_info=sample_environment_info),
            act_config,
        )

        # Act
        test_repo = str(Path(f"{PATH_PREFIX}/test/repo").resolve())
        worktree_result, agent_config = await setup_isolated_agent_activity(
            test_repo,
            "main",  # Branch provided
            act_config,
        )

        # Assert
        assert isinstance(worktree_result, IsolatedAgentEnvironmentResult)
        assert worktree_result.success is True
        assert agent_config is not None
        mock_setup_git.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_isolated_agent_act_mode_fails_without_branch(
        self,
        sample_agent_config: AgentConfiguration,
    ) -> None:
        """Test that ACT mode fails when no source_branch is provided."""
        # Arrange
        act_config = sample_agent_config.model_copy()
        act_config.mode = AgentModeEnum.ACT

        # Act
        worktree_result, agent_config = await setup_isolated_agent_activity(
            str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
            None,  # No branch provided
            act_config,
        )

        # Assert
        assert isinstance(worktree_result, IsolatedAgentEnvironmentResult)
        assert worktree_result.success is False
        assert "source_branch is required for ACT mode" in worktree_result.message
        assert agent_config is None

    @pytest.mark.asyncio
    @patch("awa.core.activities.isolated_agent_environment.setup_isolated_agent_temp_activity")
    async def test_setup_isolated_agent_analyze_mode_accepts_no_branch(
        self,
        mock_setup_temp: AsyncMock,
        sample_agent_config: AgentConfiguration,
    ) -> None:
        """Test that ANALYZE mode accepts None for source_branch parameter."""
        # Arrange
        analyze_config = sample_agent_config.model_copy()
        analyze_config.mode = AgentModeEnum.ANALYZE

        temp_worktree_info = IsolatedAgentEnvironmentInfo(
            environment_path=str(
                Path(f"{PATH_PREFIX}/test/analyze_worktree").resolve(),
            ),
            source_directory_path=str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
            source_branch=None,  # None for temporary directories
        )

        mock_setup_temp.return_value = (
            IsolatedAgentEnvironmentResult(success=True, message="Success", environment_info=temp_worktree_info),
            analyze_config,
        )

        # Act
        worktree_result, agent_config = await setup_isolated_agent_activity(
            str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
            None,  # No branch provided
            analyze_config,
        )

        # Assert
        assert isinstance(worktree_result, IsolatedAgentEnvironmentResult)
        assert worktree_result.success is True
        assert agent_config is not None
        # Verify that setup_isolated_agent_temp_activity was called with None for source_branch
        mock_setup_temp.assert_called_once()
        call_args = mock_setup_temp.call_args[0]
        assert call_args[1] is None  # source_branch parameter

    @pytest.mark.asyncio
    @patch("awa.core.activities.isolated_agent_environment.setup_isolated_agent_temp_activity")
    async def test_setup_isolated_agent_analyze_mode_accepts_branch(
        self,
        mock_setup_temp: AsyncMock,
        sample_agent_config: AgentConfiguration,
    ) -> None:
        """Test that ANALYZE mode accepts a source_branch parameter (even though it's not used)."""
        # Arrange
        analyze_config = sample_agent_config.model_copy()
        analyze_config.mode = AgentModeEnum.ANALYZE

        temp_worktree_info = IsolatedAgentEnvironmentInfo(
            environment_path=str(
                Path(f"{PATH_PREFIX}/test/analyze_worktree").resolve(),
            ),
            source_directory_path=str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
            source_branch="main",  # Branch provided but not used
        )

        mock_setup_temp.return_value = (
            IsolatedAgentEnvironmentResult(success=True, message="Success", environment_info=temp_worktree_info),
            analyze_config,
        )

        # Act
        worktree_result, agent_config = await setup_isolated_agent_activity(
            str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
            "main",  # Branch provided
            analyze_config,
        )

        # Assert
        assert isinstance(worktree_result, IsolatedAgentEnvironmentResult)
        assert worktree_result.success is True
        assert agent_config is not None
        # Verify that setup_isolated_agent_temp_activity was called with the branch
        mock_setup_temp.assert_called_once()
        call_args = mock_setup_temp.call_args[0]
        assert call_args[1] == "main"  # source_branch parameter
