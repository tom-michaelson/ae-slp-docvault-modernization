import asyncio
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.setup_config import setup_config_files


class TestSetupConfigFiles(unittest.TestCase):
    def setUp(self) -> None:
        """Set up a temporary directory for test files."""
        self.test_dir = Path("temp_test_dir_for_config")
        self.test_dir.mkdir(exist_ok=True)
        self.project_root = self.test_dir.resolve()

        # Mock the project root detection in the script.
        # The script calculates the project root with:
        # script_dir = Path(__file__).resolve().parent
        # project_root = script_dir.parents[0]
        # We'll patch Path so that when it's used to get the script_dir,
        # script_dir.parents[0] is our test directory.
        self.patcher = patch("scripts.setup_config.Path")
        mock_path_class = self.patcher.start()
        mock_path_instance = mock_path_class.return_value
        # Use a MagicMock for the fake script dir to allow setting .parents
        fake_script_dir = MagicMock()
        fake_script_dir.parents = [self.project_root]
        mock_path_instance.resolve.return_value.parent = fake_script_dir

    def tearDown(self) -> None:
        """Clean up the temporary directory."""
        self.patcher.stop()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _create_file(self, filename: str, content: str = "") -> None:
        (self.project_root / filename).write_text(content)

    @patch("scripts.setup_config._print_summary")
    @patch("scripts.setup_config._print_header")
    def test_neither_file_exists(
        self,
        mock_header: MagicMock,
        mock_summary: MagicMock,
    ) -> None:
        """Test that config files are created when neither exists."""
        self._create_file("config.example.yaml", "key: value")
        self._create_file(".env.example", "VAR=secret")
        setup_config_files()
        assert (self.project_root / "config.yaml").exists()
        assert (self.project_root / ".env").exists()
        assert (self.project_root / "config.yaml").read_text() == "key: value"
        assert (self.project_root / ".env").read_text() == "VAR=secret"
        mock_header.assert_called_once()
        mock_summary.assert_called_once_with(
            [
                ("Created 'config.yaml' from 'config.example.yaml'.", "created"),
                ("Created '.env' from '.env.example'.", "created"),
            ],
        )

    @patch("scripts.setup_config._print_summary")
    @patch("scripts.setup_config._print_header")
    def test_config_exists_env_does_not(
        self,
        mock_header: MagicMock,
        mock_summary: MagicMock,
    ) -> None:
        """Test that only .env is created if config.yaml already exists."""
        self._create_file("config.yaml", "already exists")
        self._create_file(".env.example", "VAR=secret")
        setup_config_files()
        assert (self.project_root / ".env").exists()
        assert (self.project_root / "config.yaml").read_text() == "already exists"
        assert (self.project_root / ".env").read_text() == "VAR=secret"
        mock_header.assert_called_once()
        mock_summary.assert_called_once_with(
            [
                ("'config.yaml' already exists.", "existed"),
                ("Created '.env' from '.env.example'.", "created"),
            ],
        )

    @patch("scripts.setup_config._print_summary")
    @patch("scripts.setup_config._print_header")
    def test_env_exists_config_does_not(
        self,
        mock_header: MagicMock,
        mock_summary: MagicMock,
    ) -> None:
        """Test that only config.yaml is created if .env already exists."""
        self._create_file(".env", "already exists")
        self._create_file("config.example.yaml", "key: value")
        setup_config_files()
        assert (self.project_root / "config.yaml").exists()
        assert (self.project_root / ".env").read_text() == "already exists"
        assert (self.project_root / "config.yaml").read_text() == "key: value"
        mock_header.assert_called_once()
        mock_summary.assert_called_once_with(
            [
                ("Created 'config.yaml' from 'config.example.yaml'.", "created"),
                ("'.env' already exists.", "existed"),
            ],
        )

    @patch("scripts.setup_config._print_summary")
    @patch("scripts.setup_config._print_header")
    def test_both_files_exist(
        self,
        mock_header: MagicMock,
        mock_summary: MagicMock,
    ) -> None:
        """Test that no files are changed if both already exist."""
        self._create_file("config.yaml", "config exists")
        self._create_file(".env", "env exists")
        self._create_file("config.example.yaml", "key: value")
        self._create_file(".env.example", "VAR=secret")
        setup_config_files()
        assert (self.project_root / "config.yaml").read_text() == "config exists"
        assert (self.project_root / ".env").read_text() == "env exists"
        mock_header.assert_called_once()
        mock_summary.assert_called_once_with(
            [
                ("'config.yaml' already exists.", "existed"),
                ("'.env' already exists.", "existed"),
            ],
        )

    @patch("scripts.setup_config._print_summary")
    @patch("scripts.setup_config._print_header")
    def test_env_example_missing(
        self,
        mock_header: MagicMock,
        mock_summary: MagicMock,
    ) -> None:
        """Test that an empty .env file is created if .env.example is missing."""
        self._create_file("config.example.yaml", "key: value")
        setup_config_files()
        assert (self.project_root / ".env").exists()
        assert (self.project_root / ".env").read_text() == ""
        mock_header.assert_called_once()
        mock_summary.assert_called_once_with(
            [
                ("Created 'config.yaml' from 'config.example.yaml'.", "created"),
                (
                    "Created an empty '.env' as '.env.example' was not found.",
                    "created",
                ),
            ],
        )

    @patch("scripts.setup_config._print_summary")
    @patch("scripts.setup_config._print_header")
    def test_config_example_missing(
        self,
        mock_header: MagicMock,
        mock_summary: MagicMock,
    ) -> None:
        """Test that config.yaml is not created if config.example.yaml is missing."""
        self._create_file(".env.example", "VAR=secret")
        # Ensure all coroutines are properly awaited
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            setup_config_files()
            assert not (self.project_root / "config.yaml").exists()
            mock_header.assert_called_once()
            mock_summary.assert_called_once_with(
                [("Created '.env' from '.env.example'.", "created")],
            )
        finally:
            # Clean up any pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.close()


if __name__ == "__main__":
    unittest.main()
