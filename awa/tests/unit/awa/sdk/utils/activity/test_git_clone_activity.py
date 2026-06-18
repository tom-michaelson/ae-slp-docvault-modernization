"""Test cases for SDK git clone activity utility."""

from pathlib import Path
from unittest.mock import patch

import pytest

from awa.sdk.utils.activity.git_clone_activity import git_clone_activity


class TestGitCloneActivity:
    """Test cases for git_clone_activity utility function."""

    @pytest.mark.asyncio
    async def test_git_clone_activity_with_string_url(self) -> None:
        """Test git clone activity with string URL."""
        # Arrange
        git_url = "https://github.com/example/repo.git"
        expected_result = "/tmp/cloned_repo"  # noqa: S108

        with patch("awa.sdk.utils.activity.git_clone_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = expected_result

            # Act
            result = await git_clone_activity(git_url)

            # Assert
            assert result == expected_result
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [git_url, None, None]

    @pytest.mark.asyncio
    async def test_git_clone_activity_with_destination_path_string(self) -> None:
        """Test git clone activity with destination path as string."""
        # Arrange
        git_url = "https://github.com/example/repo.git"
        destination_path = "/custom/destination"
        expected_result = "/custom/destination"

        with patch("awa.sdk.utils.activity.git_clone_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = expected_result

            # Act
            result = await git_clone_activity(git_url, destination_path)

            # Assert
            assert result == expected_result
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [git_url, destination_path, None]

    @pytest.mark.asyncio
    async def test_git_clone_activity_with_destination_path_object(self) -> None:
        """Test git clone activity with destination path as Path object."""
        # Arrange
        git_url = "https://github.com/example/repo.git"
        destination_path = Path("/custom/destination")
        expected_result = "/custom/destination"

        with patch("awa.sdk.utils.activity.git_clone_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = expected_result

            # Act
            result = await git_clone_activity(git_url, destination_path)

            # Assert
            assert result == expected_result
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [git_url, str(destination_path), None]

    @pytest.mark.asyncio
    async def test_git_clone_activity_with_branch(self) -> None:
        """Test git clone activity with specific branch."""
        # Arrange
        git_url = "https://github.com/example/repo.git"
        destination_path = "/custom/destination"
        branch = "feature-branch"
        expected_result = "/custom/destination"

        with patch("awa.sdk.utils.activity.git_clone_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = expected_result

            # Act
            result = await git_clone_activity(git_url, destination_path, branch)

            # Assert
            assert result == expected_result
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [git_url, destination_path, branch]

    @pytest.mark.asyncio
    async def test_git_clone_activity_with_all_parameters(self) -> None:
        """Test git clone activity with all parameters provided."""
        # Arrange
        git_url = "https://github.com/example/repo.git"
        destination_path = Path("/custom/destination")
        branch = "main"
        expected_result = "/custom/destination"

        with patch("awa.sdk.utils.activity.git_clone_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = expected_result

            # Act
            result = await git_clone_activity(git_url, destination_path, branch)

            # Assert
            assert result == expected_result
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [git_url, str(destination_path), branch]

    @pytest.mark.asyncio
    async def test_git_clone_activity_uses_correct_activity_name(self) -> None:
        """Test that git clone activity uses the correct activity name constant."""
        # Arrange
        git_url = "https://github.com/example/repo.git"

        with patch("awa.sdk.utils.activity.git_clone_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = "/tmp/result"  # noqa: S108

            # Act
            await git_clone_activity(git_url)

            # Assert
            mock_execute.assert_called_once()
            args, _kwargs = mock_execute.call_args
            # First positional argument should be the activity constant
            assert args[0] == "awa-git-clone"  # This should match constants.ACTIVITY_GIT_CLONE

    @pytest.mark.asyncio
    async def test_git_clone_activity_uses_correct_task_queue(self) -> None:
        """Test that git clone activity uses the correct task queue."""
        # Arrange
        git_url = "https://github.com/example/repo.git"

        with patch("awa.sdk.utils.activity.git_clone_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = "/tmp/result"  # noqa: S108

            # Act
            await git_clone_activity(git_url)

            # Assert
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert "task_queue" in kwargs
            # Should use the AWA default task queue constant

    @pytest.mark.asyncio
    async def test_git_clone_activity_uses_correct_timeout(self) -> None:
        """Test that git clone activity uses the correct timeout."""
        # Arrange
        git_url = "https://github.com/example/repo.git"

        with patch("awa.sdk.utils.activity.git_clone_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = "/tmp/result"  # noqa: S108

            # Act
            await git_clone_activity(git_url)

            # Assert
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert "start_to_close_timeout" in kwargs
            # Should use the git timeout constant
