"""Unit tests for isolated agent models."""

import sys
from pathlib import Path

import pytest

from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum
from awa.sdk.models.agent_modes.isolated_agent_models import (
    IsolatedAgentEnvironmentInfo,
    IsolatedAgentEnvironmentResult,
    IsolatedAgentParams,
)

PATH_PREFIX = "" if sys.platform != "win32" else "C:"


class TestIsolatedAgentParams:
    """Test cases for IsolatedAgentParams model."""

    def test_create_isolated_agent_params_valid(self) -> None:
        """Test creating IsolatedAgentParams with valid data."""
        # Arrange
        agent_config = AgentConfiguration(
            provider=AgentProviderEnum.CLAUDE,
            mode=AgentModeEnum.ACT,
            prompt="Test prompt",
        )

        # Act
        test_dir = str(Path(f"{PATH_PREFIX}/test/repo").resolve())
        params = IsolatedAgentParams(
            source_directory=test_dir,
            source_branch="main",
            agent_config=agent_config,
            agent_execution_timeout_minutes=15,
        )

        # Assert
        assert params.source_directory == test_dir
        assert params.source_branch == "main"
        assert params.agent_config == agent_config
        assert params.agent_execution_timeout_minutes == 15

    def test_create_isolated_agent_params_with_defaults(self) -> None:
        """Test creating IsolatedAgentParams with default values."""
        # Arrange
        agent_config = AgentConfiguration(
            provider=AgentProviderEnum.CLAUDE,
            mode=AgentModeEnum.ACT,
            prompt="Test prompt",
        )

        # Act
        test_dir = str(Path(f"{PATH_PREFIX}/test/repo").resolve())
        params = IsolatedAgentParams(
            source_directory=test_dir,
            source_branch="main",
            agent_config=agent_config,
        )

        # Assert
        assert params.source_directory == test_dir
        assert params.source_branch == "main"
        assert params.agent_config == agent_config
        assert params.agent_execution_timeout_minutes == 10  # Default value

    def test_isolated_agent_params_serialization(self) -> None:
        """Test that IsolatedAgentParams can be serialized and deserialized."""
        # Arrange
        agent_config = AgentConfiguration(
            provider=AgentProviderEnum.CLAUDE,
            mode=AgentModeEnum.ACT,
            prompt="Test prompt",
        )

        test_dir = str(Path(f"{PATH_PREFIX}/test/repo").resolve())
        original_params = IsolatedAgentParams(
            source_directory=test_dir,
            source_branch="main",
            agent_config=agent_config,
            agent_execution_timeout_minutes=20,
        )

        # Act
        serialized = original_params.model_dump()
        deserialized = IsolatedAgentParams.model_validate(serialized)

        # Assert
        assert deserialized == original_params
        assert deserialized.source_directory == test_dir
        assert deserialized.source_branch == "main"
        assert deserialized.agent_execution_timeout_minutes == 20


class TestIsolatedAgentEnvironmentInfo:
    """Test cases for IsolatedAgentEnvironmentInfo model."""

    def test_create_isolated_agent_environment_info_valid(self) -> None:
        """Test creating IsolatedAgentEnvironmentInfo with valid data."""
        # Act
        env_path = str(
            Path(f"{PATH_PREFIX}/test/repo_worktrees/feature_branch").resolve(),
        )
        source_path = str(Path(f"{PATH_PREFIX}/test/repo").resolve())
        info = IsolatedAgentEnvironmentInfo(
            environment_path=env_path,
            source_directory_path=source_path,
            source_branch="main",
        )

        # Assert
        assert info.environment_path == env_path
        assert info.source_directory_path == source_path
        assert info.source_branch == "main"

    def test_isolated_agent_environment_info_serialization(self) -> None:
        """Test that IsolatedAgentEnvironmentInfo can be serialized and deserialized."""
        # Arrange
        env_path = str(
            Path(f"{PATH_PREFIX}/test/repo_worktrees/feature_branch").resolve(),
        )
        source_path = str(Path(f"{PATH_PREFIX}/test/repo").resolve())
        original_info = IsolatedAgentEnvironmentInfo(
            environment_path=env_path,
            source_directory_path=source_path,
            source_branch="main",
        )

        # Act
        serialized = original_info.model_dump()
        deserialized = IsolatedAgentEnvironmentInfo.model_validate(serialized)

        # Assert
        assert deserialized == original_info

    def test_isolated_agent_environment_info_field_descriptions(self) -> None:
        """Test that IsolatedAgentEnvironmentInfo has proper field descriptions."""
        # Arrange
        schema = IsolatedAgentEnvironmentInfo.model_json_schema()

        # Assert
        properties = schema["properties"]
        assert "description" in properties["environment_path"]
        assert "description" in properties["source_directory_path"]
        assert "description" in properties["source_branch"]

    def test_environment_path_validation_absolute_path(self) -> None:
        """Test that environment_path accepts absolute paths."""
        # Act & Assert - Should not raise an exception
        abs_path = str(
            Path(f"{PATH_PREFIX}/absolute/path/to/worktree").resolve(),
        )
        source_path = str(Path(f"{PATH_PREFIX}/test/repo").resolve())
        info = IsolatedAgentEnvironmentInfo(
            environment_path=abs_path,
            source_directory_path=source_path,
            source_branch="main",
        )
        assert info.environment_path == abs_path

    def test_environment_path_validation_relative_path_raises_error(self) -> None:
        """Test that environment_path rejects relative paths."""
        # Act & Assert - Should raise ValueError for relative path
        with pytest.raises(ValueError, match="environment_path must be an absolute path"):
            IsolatedAgentEnvironmentInfo(
                environment_path="relative/path/to/worktree",
                source_directory_path=str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
                source_branch="main",
            )

    def test_environment_path_validation_current_directory_raises_error(self) -> None:
        """Test that environment_path rejects current directory notation."""
        # Act & Assert - Should raise ValueError for current directory
        with pytest.raises(ValueError, match="environment_path must be an absolute path"):
            IsolatedAgentEnvironmentInfo(
                environment_path="./worktree",
                source_directory_path=str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
                source_branch="main",
            )

    def test_environment_path_validation_parent_directory_raises_error(self) -> None:
        """Test that environment_path rejects parent directory notation."""
        # Act & Assert - Should raise ValueError for parent directory
        with pytest.raises(ValueError, match="environment_path must be an absolute path"):
            IsolatedAgentEnvironmentInfo(
                environment_path="../worktree",
                source_directory_path=str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
                source_branch="main",
            )


class TestIsolatedAgentEnvironmentResult:
    """Test cases for IsolatedAgentEnvironmentResult model."""

    def test_create_isolated_agent_environment_result_success(self) -> None:
        """Test creating IsolatedAgentEnvironmentResult for successful operation."""
        # Arrange
        worktree_info = IsolatedAgentEnvironmentInfo(
            environment_path=str(
                Path(f"{PATH_PREFIX}/test/repo_worktrees/feature_branch").resolve(),
            ),
            source_directory_path=str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
            source_branch="main",
        )

        # Act
        result = IsolatedAgentEnvironmentResult(
            success=True,
            message="Environment created successfully",
            environment_info=worktree_info,
        )

        # Assert
        assert result.success is True
        assert result.message == "Environment created successfully"
        assert result.environment_info == worktree_info

    def test_create_isolated_agent_environment_result_failure(self) -> None:
        """Test creating IsolatedAgentEnvironmentResult for failed operation."""
        # Act
        result = IsolatedAgentEnvironmentResult(
            success=False,
            message="Failed to create environment",
        )

        # Assert
        assert result.success is False
        assert result.message == "Failed to create environment"
        assert result.environment_info is None

    def test_create_isolated_agent_environment_result_with_defaults(self) -> None:
        """Test creating IsolatedAgentEnvironmentResult with default values."""
        # Act
        result = IsolatedAgentEnvironmentResult(
            success=True,
            message="Operation completed",
        )

        # Assert
        assert result.success is True
        assert result.message == "Operation completed"
        assert result.environment_info is None  # Default value

    def test_isolated_agent_environment_result_serialization(self) -> None:
        """Test that IsolatedAgentEnvironmentResult can be serialized and deserialized."""
        # Arrange
        worktree_info = IsolatedAgentEnvironmentInfo(
            environment_path=str(
                Path(f"{PATH_PREFIX}/test/repo_worktrees/feature_branch").resolve(),
            ),
            source_directory_path=str(Path(f"{PATH_PREFIX}/test/repo").resolve()),
            source_branch="main",
        )

        original_result = IsolatedAgentEnvironmentResult(
            success=True,
            message="Environment created successfully",
            environment_info=worktree_info,
        )

        # Act
        serialized = original_result.model_dump()
        deserialized = IsolatedAgentEnvironmentResult.model_validate(serialized)

        # Assert
        assert deserialized == original_result

    def test_isolated_agent_environment_result_field_descriptions(self) -> None:
        """Test that IsolatedAgentEnvironmentResult has proper field descriptions."""
        # Arrange
        schema = IsolatedAgentEnvironmentResult.model_json_schema()

        # Assert
        properties = schema["properties"]
        assert "description" in properties["success"]
        assert "description" in properties["message"]
        assert "description" in properties["environment_info"]

    def test_isolated_agent_environment_result_optional_worktree_info(self) -> None:
        """Test that IsolatedAgentEnvironmentResult can be created without worktree_info."""
        # Act
        result = IsolatedAgentEnvironmentResult(
            success=False,
            message="Operation failed",
        )

        # Assert
        assert result.success is False
        assert result.message == "Operation failed"
        assert result.environment_info is None


class TestModelIntegration:
    """Test cases for model integration."""

    def test_full_workflow_model_integration(self) -> None:
        """Test that all models work together in a typical workflow scenario."""
        # Arrange - Create agent config
        agent_config = AgentConfiguration(
            provider=AgentProviderEnum.CLAUDE,
            mode=AgentModeEnum.ACT,
            prompt="Add unit tests to the codebase",
            working_directory=str(Path(f"{PATH_PREFIX}/original/path").resolve()),
        )

        # Create IsolatedAgentParams
        source_dir = str(Path(f"{PATH_PREFIX}/project/awesome-app").resolve())
        params = IsolatedAgentParams(
            source_directory=source_dir,
            source_branch="feature/new-feature",
            agent_config=agent_config,
            agent_execution_timeout_minutes=30,
        )

        # Create IsolatedAgentEnvironmentInfo (what would be returned from setup)
        worktree_info = IsolatedAgentEnvironmentInfo(
            environment_path=str(
                Path(f"{PATH_PREFIX}/project/awesome-app_worktrees/add_unit_tests").resolve(),
            ),
            source_directory_path=source_dir,
            source_branch="feature/new-feature",
        )

        # Create IsolatedAgentEnvironmentResult (what would be returned from activities)
        result = IsolatedAgentEnvironmentResult(
            success=True,
            message="Environment setup completed successfully",
            environment_info=worktree_info,
        )

        # Assert - Verify all models work together
        assert params.source_directory == worktree_info.source_directory_path
        assert params.source_branch == worktree_info.source_branch
        assert result.success is True
        assert result.environment_info == worktree_info
