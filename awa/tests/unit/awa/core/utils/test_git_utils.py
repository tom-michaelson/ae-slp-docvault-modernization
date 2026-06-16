"""Unit tests for git utility functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from git import Actor

from awa.core.utils.git_utils import (
    GitAuthorInfo,
    commit_with_git_config_handling,
    get_git_author_info,
    merge_with_git_config_handling,
)
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum


@pytest.fixture
def sample_agent_config() -> AgentConfiguration:
    """Create a sample agent configuration for testing."""
    return AgentConfiguration(
        provider=AgentProviderEnum.CLAUDE,
        mode=AgentModeEnum.ACT,
        prompt="Test prompt for git utils",
        working_directory="/test/path",
    )


class TestGitAuthorInfo:
    """Test cases for GitAuthorInfo NamedTuple."""

    def test_git_author_info_creation(self) -> None:
        """Test creating GitAuthorInfo with valid data."""
        # Arrange
        actor = Actor("Test Agent", "test@example.com")

        # Act
        git_info = GitAuthorInfo(
            has_existing_config=True,
            agent_name="Test Agent",
            agent_email="test@example.com",
            actor=actor,
        )

        # Assert
        assert git_info.has_existing_config is True
        assert git_info.agent_name == "Test Agent"
        assert git_info.agent_email == "test@example.com"
        assert git_info.actor == actor

    def test_git_author_info_without_actor(self) -> None:
        """Test creating GitAuthorInfo without actor (existing config scenario)."""
        # Act
        git_info = GitAuthorInfo(
            has_existing_config=True,
            agent_name="Test Agent",
            agent_email="test@example.com",
            actor=None,
        )

        # Assert
        assert git_info.has_existing_config is True
        assert git_info.actor is None


class TestGetGitAuthorInfo:
    """Test cases for get_git_author_info function."""

    @pytest.mark.asyncio
    @patch("awa.core.utils.git_utils.FileSystemUtils.check_git_config_async")
    async def test_get_git_author_info_with_existing_config(
        self,
        mock_check_git_config: AsyncMock,
        sample_agent_config: AgentConfiguration,
    ) -> None:
        """Test get_git_author_info when git config exists."""
        # Arrange
        mock_check_git_config.return_value = True

        # Act
        result = await get_git_author_info(sample_agent_config)

        # Assert
        assert result.has_existing_config is True
        assert result.agent_name == "AWA Agent: claude"
        assert result.agent_email == "awa-agent-claude@example.com"
        assert result.actor is None
        mock_check_git_config.assert_called_once()

    @pytest.mark.asyncio
    @patch("awa.core.utils.git_utils.FileSystemUtils.check_git_config_async")
    async def test_get_git_author_info_without_existing_config(
        self,
        mock_check_git_config: AsyncMock,
        sample_agent_config: AgentConfiguration,
    ) -> None:
        """Test get_git_author_info when git config doesn't exist."""
        # Arrange
        mock_check_git_config.return_value = False

        # Act
        result = await get_git_author_info(sample_agent_config)

        # Assert
        assert result.has_existing_config is False
        assert result.agent_name == "AWA Agent: claude"
        assert result.agent_email == "awa-agent-claude@example.com"
        assert result.actor is not None
        assert result.actor.name == "AWA Agent: claude"
        assert result.actor.email == "awa-agent-claude@example.com"
        mock_check_git_config.assert_called_once()

    @pytest.mark.asyncio
    @patch("awa.core.utils.git_utils.FileSystemUtils.check_git_config_async")
    async def test_get_git_author_info_different_provider(
        self,
        mock_check_git_config: AsyncMock,
    ) -> None:
        """Test get_git_author_info with different agent provider."""
        # Arrange
        mock_check_git_config.return_value = False
        agent_config = AgentConfiguration(
            provider=AgentProviderEnum.GOOSE,
            mode=AgentModeEnum.ACT,
            prompt="Test prompt",
        )

        # Act
        result = await get_git_author_info(agent_config)

        # Assert
        assert result.agent_name == "AWA Agent: goose"
        assert result.agent_email == "awa-agent-goose@example.com"
        assert result.actor is not None
        assert result.actor.name == "AWA Agent: goose"
        assert result.actor.email == "awa-agent-goose@example.com"


class TestCommitWithGitConfigHandling:
    """Test cases for commit_with_git_config_handling function."""

    @patch("awa.core.utils.git_utils.activity")
    def test_commit_with_existing_config(self, mock_activity: MagicMock) -> None:
        """Test commit when git config exists."""
        # Arrange
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_repo.index.commit.return_value = mock_commit

        git_info = GitAuthorInfo(
            has_existing_config=True,
            agent_name="AWA Agent: claude",
            agent_email="awa-agent-claude@example.com",
            actor=None,
        )

        # Act
        result = commit_with_git_config_handling(mock_repo, "Test commit", git_info)

        # Assert
        assert result == mock_commit
        mock_repo.index.commit.assert_called_once_with("Test commit")
        mock_activity.logger.info.assert_called_with("Using existing git configuration for commit")

    @patch("awa.core.utils.git_utils.activity")
    def test_commit_without_existing_config(self, mock_activity: MagicMock) -> None:
        """Test commit when git config doesn't exist."""
        # Arrange
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_repo.index.commit.return_value = mock_commit

        actor = Actor("AWA Agent: claude", "awa-agent-claude@example.com")
        git_info = GitAuthorInfo(
            has_existing_config=False,
            agent_name="AWA Agent: claude",
            agent_email="awa-agent-claude@example.com",
            actor=actor,
        )

        # Act
        result = commit_with_git_config_handling(mock_repo, "Test commit", git_info)

        # Assert
        assert result == mock_commit
        mock_repo.index.commit.assert_called_once_with(
            "Test commit",
            author=actor,
            committer=actor,
        )
        mock_activity.logger.info.assert_called_with(
            "No git configuration found, using agent as author: AWA Agent: claude",
        )


class TestMergeWithGitConfigHandling:
    """Test cases for merge_with_git_config_handling function."""

    @patch("awa.core.utils.git_utils.activity")
    def test_merge_with_existing_config(self, mock_activity: MagicMock) -> None:
        """Test merge when git config exists."""
        # Arrange
        mock_repo = MagicMock()
        commit_hexsha = "abc123def456"

        git_info = GitAuthorInfo(
            has_existing_config=True,
            agent_name="AWA Agent: claude",
            agent_email="awa-agent-claude@example.com",
            actor=None,
        )

        # Act
        merge_with_git_config_handling(mock_repo, commit_hexsha, git_info)

        # Assert
        mock_repo.git.merge.assert_called_once_with(commit_hexsha, no_ff=True)
        mock_activity.logger.info.assert_called_with("Using existing git configuration for merge")

    @patch("awa.core.utils.git_utils.activity")
    def test_merge_without_existing_config(self, mock_activity: MagicMock) -> None:
        """Test merge when git config doesn't exist."""
        # Arrange
        mock_repo = MagicMock()
        commit_hexsha = "abc123def456"

        git_info = GitAuthorInfo(
            has_existing_config=False,
            agent_name="AWA Agent: claude",
            agent_email="awa-agent-claude@example.com",
            actor=Actor("AWA Agent: claude", "awa-agent-claude@example.com"),
        )

        # Mock the custom environment context manager
        mock_custom_env = MagicMock()
        mock_repo.git.custom_environment.return_value = mock_custom_env
        mock_custom_env.__enter__ = MagicMock(return_value=mock_custom_env)
        mock_custom_env.__exit__ = MagicMock(return_value=None)

        # Act
        merge_with_git_config_handling(mock_repo, commit_hexsha, git_info)

        # Assert
        mock_repo.git.custom_environment.assert_called_once_with(
            GIT_AUTHOR_NAME="AWA Agent: claude",
            GIT_AUTHOR_EMAIL="awa-agent-claude@example.com",
            GIT_COMMITTER_NAME="AWA Agent: claude",
            GIT_COMMITTER_EMAIL="awa-agent-claude@example.com",
        )
        mock_activity.logger.info.assert_called_with(
            "No git configuration found, using agent for merge: AWA Agent: claude",
        )


class TestGitUtilsIntegration:
    """Integration tests for git utils working together."""

    @pytest.mark.asyncio
    @patch("awa.core.utils.git_utils.FileSystemUtils.check_git_config_async")
    @patch("awa.core.utils.git_utils.activity")
    async def test_full_git_workflow_with_config(
        self,
        mock_activity: MagicMock,  # noqa: ARG002
        mock_check_git_config: AsyncMock,
        sample_agent_config: AgentConfiguration,
    ) -> None:
        """Test complete git workflow when config exists."""
        # Arrange
        mock_check_git_config.return_value = True
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123def456"
        mock_repo.index.commit.return_value = mock_commit

        # Act - Get git info
        git_info = await get_git_author_info(sample_agent_config)

        # Act - Commit
        result_commit = commit_with_git_config_handling(mock_repo, "Test commit", git_info)

        # Act - Merge
        merge_with_git_config_handling(mock_repo, result_commit.hexsha, git_info)

        # Assert
        assert git_info.has_existing_config is True
        assert result_commit == mock_commit
        mock_repo.index.commit.assert_called_once_with("Test commit")
        mock_repo.git.merge.assert_called_once_with("abc123def456", no_ff=True)

    @pytest.mark.asyncio
    @patch("awa.core.utils.git_utils.FileSystemUtils.check_git_config_async")
    @patch("awa.core.utils.git_utils.activity")
    async def test_full_git_workflow_without_config(
        self,
        mock_activity: MagicMock,  # noqa: ARG002
        mock_check_git_config: AsyncMock,
        sample_agent_config: AgentConfiguration,
    ) -> None:
        """Test complete git workflow when config doesn't exist."""
        # Arrange
        mock_check_git_config.return_value = False
        mock_repo = MagicMock()
        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123def456"
        mock_repo.index.commit.return_value = mock_commit

        # Mock the custom environment context manager
        mock_custom_env = MagicMock()
        mock_repo.git.custom_environment.return_value = mock_custom_env
        mock_custom_env.__enter__ = MagicMock(return_value=mock_custom_env)
        mock_custom_env.__exit__ = MagicMock(return_value=None)

        # Act - Get git info
        git_info = await get_git_author_info(sample_agent_config)

        # Act - Commit
        result_commit = commit_with_git_config_handling(mock_repo, "Test commit", git_info)

        # Act - Merge
        merge_with_git_config_handling(mock_repo, result_commit.hexsha, git_info)

        # Assert
        assert git_info.has_existing_config is False
        assert git_info.actor is not None
        assert result_commit == mock_commit

        # Verify commit used author/committer
        commit_args = mock_repo.index.commit.call_args
        assert "author" in commit_args.kwargs
        assert "committer" in commit_args.kwargs

        # Verify merge used custom environment
        mock_repo.git.custom_environment.assert_called_once()
