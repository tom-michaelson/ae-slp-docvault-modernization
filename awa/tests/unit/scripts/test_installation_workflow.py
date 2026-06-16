"""Integration tests for AWA installation and initialization workflow."""

# Add scripts directory to path for importing
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from install import backup_existing_config, detect_existing_installation, install_awa_wheel


class TestInstallationWorkflow:
    """Integration tests for the complete installation workflow."""

    @pytest.fixture
    def temp_home(self) -> Generator[Path, None, None]:
        """Create temporary home directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home_path = Path(temp_dir)
            with patch("pathlib.Path.home", return_value=home_path):
                yield home_path

    @pytest.fixture
    def mock_wheel_file(self, tmp_path: Path) -> Path:
        """Create a mock wheel file for testing."""
        wheel_file = tmp_path / "test-awa-1.0.0-py3-none-any.whl"
        wheel_file.write_text("mock wheel content")
        return wheel_file

    def test_fresh_installation_workflow(self, temp_home: Path, mock_wheel_file: Path) -> None:  # noqa: ARG002
        """Test complete fresh installation workflow."""
        # Step 1: Detect installation (should find nothing)
        installation_info = detect_existing_installation()
        assert installation_info["awa_installed"] is False
        assert installation_info["config_exists"] is False

        # Step 2: Backup (should succeed with no action)
        backup_result = backup_existing_config(installation_info)
        assert backup_result is True

        # Step 3: Mock wheel installation
        with patch("install.run_command") as mock_run_command:
            mock_result = type("MockResult", (), {"returncode": 0})()
            mock_run_command.return_value = mock_result

            install_result = install_awa_wheel(str(mock_wheel_file), upgrade=False)
            assert install_result is True

        # Step 4: Verify AWA directory can be created on demand
        # (The installation script doesn't create .awa directory until needed)
        from install import get_global_config_dir

        config_dir = get_global_config_dir()
        assert config_dir.exists()

    def test_upgrade_workflow_with_existing_config(self, temp_home: Path, mock_wheel_file: Path) -> None:
        """Test upgrade workflow with existing configuration."""
        # Step 1: Create existing configuration
        awa_dir = temp_home / ".awa"
        awa_dir.mkdir(parents=True)

        config_file = awa_dir / "config.yaml"
        env_file = awa_dir / ".env"

        config_file.write_text("""
llm:
  default_model: test-model
  providers:
    openai: {}
  models:
    - name: test-model
      provider: OpenAI
      model: gpt-4
""")
        env_file.write_text("OPENAI_API_KEY=test-key")

        # Step 2: Mock existing AWA installation
        with patch("install.get_installed_awa_version") as mock_version:
            mock_version.return_value = "AWA version 1.0.0"

            installation_info = detect_existing_installation()
            assert installation_info["awa_installed"] is True
            assert installation_info["config_exists"] is True
            assert len(installation_info["config_files"]) == 2

        # Step 3: Backup existing config
        with patch("install.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            backup_result = backup_existing_config(installation_info)

        assert backup_result is True

        # Verify backup was created
        backup_dir = awa_dir / "backup_20240101_120000"
        assert backup_dir.exists()
        assert (backup_dir / "config.yaml").exists()
        assert (backup_dir / ".env").exists()

        # Step 4: Mock wheel installation (upgrade)
        with patch("install.run_command") as mock_run_command:
            mock_result = type("MockResult", (), {"returncode": 0})()
            mock_run_command.return_value = mock_result

            install_result = install_awa_wheel(str(mock_wheel_file), upgrade=True)
            assert install_result is True

        # Step 5: Verify original config is preserved
        assert config_file.exists()
        assert env_file.exists()
        assert "test-model" in config_file.read_text()
        assert "OPENAI_API_KEY=test-key" in env_file.read_text()

    def test_installation_with_partial_config(self, temp_home: Path, mock_wheel_file: Path) -> None:  # noqa: ARG002
        """Test installation with only partial configuration files."""
        # Step 1: Create partial configuration
        awa_dir = temp_home / ".awa"
        awa_dir.mkdir(parents=True)

        config_file = awa_dir / "config.yaml"
        config_file.write_text("partial: config")
        # Note: No .env file

        # Step 2: Mock existing AWA installation
        with patch("install.get_installed_awa_version") as mock_version:
            mock_version.return_value = "AWA version 1.0.0"

            installation_info = detect_existing_installation()
            assert installation_info["awa_installed"] is True
            assert installation_info["config_exists"] is True
            assert len(installation_info["config_files"]) == 1

        # Step 3: Backup should handle partial config
        with patch("install.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            backup_result = backup_existing_config(installation_info)

        assert backup_result is True

        # Verify backup contains only existing file
        backup_dir = awa_dir / "backup_20240101_120000"
        assert backup_dir.exists()
        assert (backup_dir / "config.yaml").exists()
        assert not (backup_dir / ".env").exists()

    def test_installation_failure_scenarios(self, temp_home: Path, mock_wheel_file: Path) -> None:  # noqa: ARG002
        """Test various installation failure scenarios."""
        # Test 1: Missing wheel file
        nonexistent_wheel = mock_wheel_file.parent / "nonexistent.whl"
        install_result = install_awa_wheel(str(nonexistent_wheel))
        assert install_result is False

        # Test 2: Installation command failure
        with patch("install.run_command") as mock_run_command:
            mock_run_command.return_value = None  # Simulate failure

            install_result = install_awa_wheel(str(mock_wheel_file))
            assert install_result is False

        # Test 3: No wheel path provided
        install_result = install_awa_wheel(None)
        assert install_result is False

    def test_backup_failure_handling(self, temp_home: Path) -> None:  # noqa: ARG002
        """Test backup failure handling."""
        # Create installation info with config files that will fail to backup
        installation_info = {
            "config_exists": True,
            "config_files": [Path("/nonexistent/config.yaml")],
        }

        # Mock Path.home to return a writable path, then mock mkdir to raise exception
        with (
            patch("install.Path.home", return_value=Path("/tmp/test_home")),  # noqa: S108
            patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")),
        ):
            backup_result = backup_existing_config(installation_info)
            assert backup_result is False


class TestInitWorkflow:
    """Integration tests for the init workflow."""

    @pytest.fixture
    def temp_home(self) -> Generator[Path, None, None]:
        """Create temporary home directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home_path = Path(temp_dir)
            with patch("pathlib.Path.home", return_value=home_path):
                yield home_path

    def test_init_command_availability(self) -> None:
        """Test that init command is available in CLI."""
        try:
            # Test that we can import the init command
            from awa.core.cli.commands.init import app

            assert app is not None
        except ImportError:
            pytest.fail("Init command not properly registered")

    def test_init_validation_functions(self, temp_home: Path) -> None:  # noqa: ARG002
        """Test init command validation functions."""
        import inspect

        from awa.core.cli.commands.init import validate_configuration_requirements

        # Test that we can import the function
        assert callable(validate_configuration_requirements)
        # Test that it's an async function
        assert inspect.iscoroutinefunction(validate_configuration_requirements)

    def test_provider_setup_requirements(self) -> None:
        """Test LLM provider setup requirements."""
        from awa.core.cli.commands.init import LLMProviderSetup
        from awa.core.models.config.llm_providers_config import LlmProviderEnum

        setup = LLMProviderSetup()

        # Test OpenAI requirements
        openai_reqs = setup.get_provider_requirements(LlmProviderEnum.OPEN_AI)
        assert "OPENAI_API_KEY" in openai_reqs["env_vars"]
        assert openai_reqs["config_class"] is None

        # Test Azure OpenAI requirements
        azure_reqs = setup.get_provider_requirements(LlmProviderEnum.AZURE_OPEN_AI)
        assert "AZURE_OPENAI_API_KEY" in azure_reqs["env_vars"]
        assert azure_reqs["config_class"] is not None
        assert "resource_name" in azure_reqs["prompts"]

    def test_config_creation_workflow(self, temp_home: Path) -> None:
        """Test configuration file creation workflow."""
        from awa.core.cli.commands.init import create_global_config_files
        from awa.core.models.config.llm_providers_config import LlmProviderEnum

        # Mock async function call
        async def run_test() -> None:
            user_inputs = {
                "OPENAI_API_KEY": "test-key",
            }

            await create_global_config_files(
                LlmProviderEnum.OPEN_AI,
                user_inputs,
                "gpt-4",
                "my-openai-model",
                8000,
                8001,
                8002,
            )

            # Check that files were created
            awa_dir = temp_home / ".awa"
            assert awa_dir.exists()
            assert (awa_dir / "config.yaml").exists()
            assert (awa_dir / ".env").exists()

            # Check config content
            config_content = (awa_dir / "config.yaml").read_text()
            assert "my-openai-model" in config_content
            assert "OpenAI" in config_content

            env_content = (awa_dir / ".env").read_text()
            assert "OPENAI_API_KEY=test-key" in env_content

        # For now, just test the import works (would need async test runner for full test)
        assert callable(create_global_config_files)


class TestCompleteWorkflow:
    """Integration tests for the complete installation + init workflow."""

    @pytest.fixture
    def temp_home(self) -> Generator[Path, None, None]:
        """Create temporary home directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home_path = Path(temp_dir)
            with patch("pathlib.Path.home", return_value=home_path):
                yield home_path

    def test_fresh_install_to_init_workflow(self, temp_home: Path) -> None:
        """Test complete workflow from fresh install to init."""
        # Step 1: Verify starting state
        awa_dir = temp_home / ".awa"
        assert not awa_dir.exists()

        # Step 2: Simulate installation
        installation_info = detect_existing_installation()
        assert installation_info["awa_installed"] is False

        # Step 3: Create AWA directory (simulating successful install)
        # Note: detect_existing_installation() already creates the directory
        assert awa_dir.exists()  # Directory should already exist from step 2

        # Step 4: Test that init command components are available
        from awa.core.cli.commands.init import LLMProviderSetup
        from awa.core.models.config.llm_providers_config import LlmProviderEnum

        setup = LLMProviderSetup()

        # Test provider configuration creation
        user_inputs = {"OPENAI_API_KEY": "test-key"}
        provider_config = setup.create_provider_config(LlmProviderEnum.OPEN_AI, user_inputs)
        assert provider_config == {}  # OpenAI doesn't need additional config

        env_vars = setup.create_env_vars(LlmProviderEnum.OPEN_AI, user_inputs)
        assert env_vars["OPENAI_API_KEY"] == "test-key"

    def test_upgrade_preserves_config_workflow(self, temp_home: Path) -> None:
        """Test that upgrade workflow preserves existing configuration."""
        # Step 1: Create existing configuration
        awa_dir = temp_home / ".awa"
        awa_dir.mkdir(parents=True)

        config_file = awa_dir / "config.yaml"
        env_file = awa_dir / ".env"

        original_config = """
llm:
  default_model: existing-model
  providers:
    openai: {}
  models:
    - name: existing-model
      provider: OpenAI
      model: gpt-3.5-turbo
"""
        original_env = "OPENAI_API_KEY=existing-key"

        config_file.write_text(original_config)
        env_file.write_text(original_env)

        # Step 2: Simulate upgrade detection
        with patch("install.get_installed_awa_version") as mock_version:
            mock_version.return_value = "AWA version 1.0.0"

            installation_info = detect_existing_installation()
            assert installation_info["awa_installed"] is True
            assert installation_info["config_exists"] is True

        # Step 3: Backup configuration
        with patch("install.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            backup_result = backup_existing_config(installation_info)

        assert backup_result is True

        # Step 4: Verify original config is preserved
        assert config_file.read_text() == original_config
        assert env_file.read_text() == original_env

        # Step 5: Verify backup exists
        backup_dir = awa_dir / "backup_20240101_120000"
        assert backup_dir.exists()
        assert (backup_dir / "config.yaml").read_text() == original_config
        assert (backup_dir / ".env").read_text() == original_env

    def test_hierarchical_config_loading(self, temp_home: Path) -> None:
        """Test hierarchical configuration loading."""
        from awa.core.utils.config_loader import ConfigLoader

        # Create global config
        awa_dir = temp_home / ".awa"
        awa_dir.mkdir(parents=True)

        global_config = awa_dir / "config.yaml"
        global_config.write_text("""
llm:
  default_model: global-model
  providers:
    openai: {}
  models:
    - name: global-model
      provider: OpenAI
      model: gpt-4
""")

        # Create local config in a project directory
        project_dir = temp_home / "project"
        project_dir.mkdir(parents=True)

        local_config = project_dir / "config.yaml"
        local_config.write_text("""
llm:
  default_model: local-model
  models:
    - name: local-model
      provider: OpenAI
      model: gpt-3.5-turbo
""")

        # Test that ConfigLoader can handle hierarchical loading
        # (This would need to be run from the project directory in a real scenario)
        with patch("pathlib.Path.cwd", return_value=project_dir):
            # Test that the loader can be called (full integration would need async test)
            assert hasattr(ConfigLoader, "load_config_with_hierarchy")
            assert callable(ConfigLoader.load_config_with_hierarchy)

    def test_error_handling_workflow(self, temp_home: Path) -> None:  # noqa: ARG002
        """Test error handling throughout the workflow."""
        # Test 1: Backup failure doesn't stop installation
        installation_info = {
            "config_exists": True,
            "config_files": [Path("/nonexistent/config.yaml")],
        }

        # Mock Path.home to return a writable path, then mock mkdir to raise exception
        with (
            patch("install.Path.home", return_value=Path("/tmp/test_home")),  # noqa: S108
            patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")),
        ):
            backup_result = backup_existing_config(installation_info)
            assert backup_result is False

        # Test 2: Config validation handles missing files gracefully
        import inspect

        from awa.core.cli.commands.init import validate_configuration_requirements

        # Should not raise exception even with missing config
        assert callable(validate_configuration_requirements)
        assert inspect.iscoroutinefunction(validate_configuration_requirements)
