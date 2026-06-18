import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from temporalio.testing import ActivityEnvironment

from awa.core.activities.git import GitOperationError, git_clone_repository_activity


class TestGitCloneRepositoryActivity:
    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_success_with_temp_dir(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        expected_path = str(Path(os.sep) / "tmp" / "awa_git_clone_test123")

        with (
            patch("tempfile.mkdtemp", return_value=expected_path),
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "mkdir") as mock_mkdir,
        ):
            mock_run.return_value = MagicMock(stderr="", returncode=0)

            result = await activity_env.run(git_clone_repository_activity, git_url)

            assert result == expected_path
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == ["git", "clone", git_url, expected_path]

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_success_with_destination_path(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        destination_path = str(Path(os.sep) / "custom" / "destination")

        with (
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "mkdir") as mock_mkdir,
        ):
            mock_run.return_value = MagicMock(stderr="", returncode=0)

            result = await activity_env.run(
                git_clone_repository_activity,
                git_url,
                destination_path,
            )

            assert result == destination_path
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == ["git", "clone", git_url, destination_path]

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_success_with_branch(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        destination_path = str(Path(os.sep) / "custom" / "destination")
        branch = "feature-branch"

        with (
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "mkdir"),
        ):
            mock_run.return_value = MagicMock(stderr="", returncode=0)

            result = await activity_env.run(
                git_clone_repository_activity,
                git_url,
                destination_path,
                branch,
            )

            assert result == destination_path
            mock_run.assert_called_once()
            expected_cmd = ["git", "clone", "-b", branch, git_url, destination_path]
            assert mock_run.call_args[0][0] == expected_cmd

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_existing_non_empty_directory(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        destination_path = str(Path(os.sep) / "existing" / "destination")
        expected_subdirectory = str(Path(os.sep) / "existing" / "destination" / "repo")

        with (
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "iterdir", return_value=["some_file"]),
            patch.object(Path, "mkdir") as mock_mkdir,
        ):
            mock_run.return_value = MagicMock(stderr="", returncode=0)

            result = await activity_env.run(
                git_clone_repository_activity,
                git_url,
                destination_path,
            )

            assert result == expected_subdirectory
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == ["git", "clone", git_url, expected_subdirectory]

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_git_url_with_git_extension(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        destination_path = str(Path(os.sep) / "existing" / "destination")
        expected_subdirectory = str(Path(os.sep) / "existing" / "destination" / "repo")

        with (
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "iterdir", return_value=["some_file"]),
            patch.object(Path, "mkdir"),
        ):
            mock_run.return_value = MagicMock(stderr="", returncode=0)

            await activity_env.run(
                git_clone_repository_activity,
                git_url,
                destination_path,
            )

            assert mock_run.call_args[0][0] == ["git", "clone", git_url, expected_subdirectory]

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_git_url_without_git_extension(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo"
        destination_path = str(Path(os.sep) / "existing" / "destination")
        expected_subdirectory = str(Path(os.sep) / "existing" / "destination" / "repo")

        with (
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "iterdir", return_value=["some_file"]),
            patch.object(Path, "mkdir"),
        ):
            mock_run.return_value = MagicMock(stderr="", returncode=0)

            await activity_env.run(
                git_clone_repository_activity,
                git_url,
                destination_path,
            )

            assert mock_run.call_args[0][0] == ["git", "clone", git_url, expected_subdirectory]

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_subprocess_error(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        destination_path = str(Path(os.sep) / "custom" / "destination")
        error_message = "Repository not found"

        with (
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "mkdir"),
        ):
            import subprocess

            mock_run.side_effect = subprocess.CalledProcessError(
                1,
                ["git", "clone"],
                stderr=error_message,
            )

            with pytest.raises(GitOperationError, match="Failed to clone repository"):
                await activity_env.run(
                    git_clone_repository_activity,
                    git_url,
                    destination_path,
                )

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_subprocess_error_with_temp_cleanup(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        temp_dir = str(Path(os.sep) / "tmp" / "awa_git_clone_test123")

        with (
            patch("tempfile.mkdtemp", return_value=temp_dir),
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "mkdir"),
            patch("shutil.rmtree") as mock_rmtree,
        ):
            # First call for destination check, second call for cleanup check
            mock_exists.side_effect = [False, True]

            import subprocess

            mock_run.side_effect = subprocess.CalledProcessError(
                1,
                ["git", "clone"],
                stderr="Repository not found",
            )

            with pytest.raises(GitOperationError):
                await activity_env.run(git_clone_repository_activity, git_url)

            mock_rmtree.assert_called_once_with(temp_dir)

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_unexpected_error(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        destination_path = str(Path(os.sep) / "custom" / "destination")

        with (
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "mkdir"),
        ):
            mock_run.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(RuntimeError, match="Unexpected error"):
                await activity_env.run(
                    git_clone_repository_activity,
                    git_url,
                    destination_path,
                )

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_unexpected_error_with_temp_cleanup(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        temp_dir = str(Path(os.sep) / "tmp" / "awa_git_clone_test123")

        with (
            patch("tempfile.mkdtemp", return_value=temp_dir),
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists") as mock_exists,
            patch.object(Path, "mkdir"),
            patch("shutil.rmtree") as mock_rmtree,
        ):
            # First call for destination check, second call for cleanup check
            mock_exists.side_effect = [False, True]

            mock_run.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(RuntimeError):
                await activity_env.run(git_clone_repository_activity, git_url)

            mock_rmtree.assert_called_once_with(temp_dir)

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_with_stderr_but_success(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        destination_path = str(Path(os.sep) / "custom" / "destination")
        stderr_output = "Cloning into '/custom/destination'..."

        with (
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "mkdir"),
        ):
            mock_run.return_value = MagicMock(stderr=stderr_output, returncode=0)

            result = await activity_env.run(
                git_clone_repository_activity,
                git_url,
                destination_path,
            )

            assert result == destination_path
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_git_clone_repository_activity_path_object_destination(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        git_url = "https://github.com/example/repo.git"
        destination_path = Path(os.sep) / "custom" / "destination"

        with (
            patch("subprocess.run") as mock_run,
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "mkdir"),
        ):
            mock_run.return_value = MagicMock(stderr="", returncode=0)

            result = await activity_env.run(
                git_clone_repository_activity,
                git_url,
                destination_path,
            )

            assert result == str(destination_path)
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == ["git", "clone", git_url, str(destination_path)]
