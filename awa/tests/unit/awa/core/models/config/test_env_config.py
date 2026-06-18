"""Test cases for environment configuration."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from awa.core.models.config.env_config import EnvConfig, Settings
from tests.utils.platform_test_utils import mock_home_directory


class TestSettings:
    """Test cases for Settings class."""

    @patch.dict(os.environ, {}, clear=True)
    def test_settings_default_values(self) -> None:
        """Test Settings initialization with default values."""
        # Act
        settings = Settings(_env_file=[])  # Explicitly avoid loading any env files

        # Assert
        assert settings.awa_ui_host == "localhost"
        assert settings.awa_ui_port == 8000
        assert settings.awa_api_host == "localhost"
        assert settings.awa_api_port == 8001
        assert settings.temporal_ui_host == "localhost"
        assert settings.temporal_ui_port == 8002
        assert settings.temporal_server_host == "localhost"
        assert settings.temporal_server_port == 7233
        assert settings.temporal_metrics_port == 8004
        assert settings.temporal_namespace == "default"
        assert settings.temporal_version == "1.27.2"
        assert settings.temporal_admintools_version == "1.27.2-tctl-1.18.2-cli-1.3.0"
        assert settings.temporal_ui_version == "2.34.0"
        assert settings.postgresql_version == "16"
        assert settings.postgres_password == "temporal"
        assert settings.postgres_user == "temporal"
        assert settings.postgres_default_port == 5432
        assert settings.openai_api_key == ""
        assert settings.azure_openai_api_key == ""
        assert settings.google_application_credentials == ""
        assert settings.lite_llm_api_key == ""
        assert settings.github_copilot_api_key == ""
        assert settings.anthropic_api_key == ""
        assert settings.jira_api_key == ""
        assert settings.pythonpycacheprefix == ".cache/pycache"
        assert settings.llm_cache_path == "./.cache/llm"
        assert settings.debug_mode is True
        assert settings.log_level == "DEBUG"
        assert settings.log_path == "logs"
        assert settings.log_file_rotation_size == "1 MB"
        assert settings.log_enable_json is False
        assert settings.log_workflow_dir == "logs/workflows"
        assert settings.log_console_enabled is True
        assert settings.log_file_enabled is True

    @patch.dict(os.environ, {}, clear=True)
    def test_settings_with_custom_values(self) -> None:
        """Test Settings initialization with custom values."""
        # Arrange
        custom_values = {
            "awa_ui_host": "0.0.0.0",  # noqa: S104
            "awa_ui_port": "9000",
            "anthropic_api_key": "test-anthropic-key-123",
            "openai_api_key": "test-openai-key-456",
            "debug_mode": "false",
            "log_level": "INFO",
        }

        # Act
        settings = Settings(_env_file=[], **custom_values)

        # Assert
        assert settings.awa_ui_host == "0.0.0.0"  # noqa: S104
        assert settings.awa_ui_port == 9000
        assert settings.anthropic_api_key == "test-anthropic-key-123"
        assert settings.openai_api_key == "test-openai-key-456"
        assert settings.debug_mode is False
        assert settings.log_level == "INFO"

    @patch.dict(os.environ, {}, clear=True)
    def test_settings_from_env_file(self) -> None:
        """Test Settings loading from environment file."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("AWA_UI_HOST=test.example.com\n")
            f.write("AWA_UI_PORT=8080\n")
            f.write("ANTHROPIC_API_KEY=env-anthropic-key\n")
            f.write("OPENAI_API_KEY=env-openai-key\n")
            f.write("DEBUG_MODE=false\n")
            env_file_path = f.name

        try:
            # Act
            settings = Settings(_env_file=env_file_path)

            # Assert
            assert settings.awa_ui_host == "test.example.com"
            assert settings.awa_ui_port == 8080
            assert settings.anthropic_api_key == "env-anthropic-key"
            assert settings.openai_api_key == "env-openai-key"
            assert settings.debug_mode is False
        finally:
            Path(env_file_path).unlink()

    @patch.dict(os.environ, {}, clear=True)
    @patch("awa.core.models.config.env_config.ConfigPaths.get_config_file_paths")
    def test_settings_load_with_hierarchy(self, mock_get_config_paths: Mock) -> None:
        """Test Settings.load_with_hierarchy method."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("ANTHROPIC_API_KEY=hierarchy-anthropic-key\n")
            f.write("AWA_UI_PORT=9999\n")
            env_file_path = f.name

        mock_get_config_paths.return_value = {
            "env_files": [Path(env_file_path)],
        }

        try:
            # Act
            settings = Settings.load_with_hierarchy()

            # Assert
            assert settings.anthropic_api_key == "hierarchy-anthropic-key"
            assert settings.awa_ui_port == 9999
            mock_get_config_paths.assert_called_once()
        finally:
            Path(env_file_path).unlink()

    @patch.dict(os.environ, {}, clear=True)
    def test_settings_type_validation(self) -> None:
        """Test Settings type validation for different field types."""
        # Test integer validation
        with pytest.raises(ValidationError):
            Settings(_env_file=[], awa_ui_port="invalid_port")

        # Test boolean validation
        settings_true = Settings(_env_file=[], debug_mode="true")
        assert settings_true.debug_mode is True

        settings_false = Settings(_env_file=[], debug_mode="false")
        assert settings_false.debug_mode is False

        # Test string fields accept empty strings
        settings = Settings(_env_file=[], anthropic_api_key="", openai_api_key="")
        assert settings.anthropic_api_key == ""
        assert settings.openai_api_key == ""


class TestEnvConfig:
    """Test cases for EnvConfig class."""

    def setup_method(self) -> None:
        """Reset EnvConfig state before each test."""
        EnvConfig._env_config = None

    def teardown_method(self) -> None:
        """Clean up EnvConfig state after each test."""
        EnvConfig._env_config = None

    @patch.dict(os.environ, {}, clear=True)
    def test_env_config_singleton_behavior(self) -> None:
        """Test EnvConfig singleton-like behavior."""
        # Arrange & Act
        with mock_home_directory():
            config1 = EnvConfig.get_env_config()
            config2 = EnvConfig.get_env_config()

            # Assert
            assert config1 is config2

    @patch.dict(os.environ, {}, clear=True)
    def test_env_config_set_and_get(self) -> None:
        """Test EnvConfig set and get functionality."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("ANTHROPIC_API_KEY=test-anthropic-key\n")
            f.write("AWA_UI_PORT=8888\n")
            env_file_path = f.name

        try:
            # Act
            EnvConfig.set_env_config(env_file_path)
            config = EnvConfig.get_env_config()

            # Assert
            assert config.anthropic_api_key == "test-anthropic-key"
            assert config.awa_ui_port == 8888
        finally:
            Path(env_file_path).unlink()

    @patch.dict(os.environ, {}, clear=True)
    def test_env_config_update(self) -> None:
        """Test EnvConfig update functionality."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f1:
            f1.write("ANTHROPIC_API_KEY=initial-key\n")
            env_file_path1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f2:
            f2.write("ANTHROPIC_API_KEY=updated-key\n")
            f2.write("OPENAI_API_KEY=new-openai-key\n")
            env_file_path2 = f2.name

        try:
            # Act
            EnvConfig.set_env_config(env_file_path1)
            initial_config = EnvConfig.get_env_config()
            assert initial_config.anthropic_api_key == "initial-key"

            EnvConfig.update_env_config(env_file_path2)
            updated_config = EnvConfig.get_env_config()

            # Assert
            assert updated_config.anthropic_api_key == "updated-key"
            assert updated_config.openai_api_key == "new-openai-key"
        finally:
            Path(env_file_path1).unlink()
            Path(env_file_path2).unlink()

    @patch.dict(os.environ, {}, clear=True)
    @patch("awa.core.models.config.env_config.Settings.load_with_hierarchy")
    def test_env_config_hierarchical_loading(self, mock_load_hierarchy: Mock) -> None:
        """Test EnvConfig uses hierarchical loading when no file path provided."""
        # Arrange
        mock_settings = Mock()
        mock_load_hierarchy.return_value = mock_settings

        # Act
        EnvConfig.set_env_config()
        config = EnvConfig.get_env_config()

        # Assert
        assert config is mock_settings
        mock_load_hierarchy.assert_called_once()

    @patch.dict(os.environ, {"TEST_ENV_VAR": "test-value"})
    def test_env_config_get_env_config_value(self) -> None:
        """Test EnvConfig.get_env_config_value method."""
        # Arrange
        EnvConfig.set_env_config()

        # Act
        value = EnvConfig.get_env_config_value("TEST_ENV_VAR")

        # Assert
        assert value == "test-value"

    @patch.dict(os.environ, {}, clear=True)
    def test_env_config_get_env_config_value_none(self) -> None:
        """Test EnvConfig.get_env_config_value returns None for non-existent key."""
        # Arrange
        with mock_home_directory():
            EnvConfig.set_env_config()

            # Act
            value = EnvConfig.get_env_config_value("NON_EXISTENT_KEY")

            # Assert
            assert value is None

    @patch.dict(os.environ, {}, clear=True)
    @patch("awa.core.models.config.env_config.logger")
    def test_env_config_validation_error_handling(self, mock_logger: Mock) -> None:
        """Test EnvConfig handles ValidationError properly."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("AWA_UI_PORT=invalid_port_number\n")
            env_file_path = f.name

        try:
            # Act & Assert
            with pytest.raises(ValidationError):
                EnvConfig.set_env_config(env_file_path)

            # Verify error was logged
            mock_logger.error.assert_called_once()
        finally:
            Path(env_file_path).unlink()

    @patch.dict(os.environ, {}, clear=True)
    @patch("awa.core.models.config.env_config.Settings.load_with_hierarchy")
    def test_env_config_reset_state(self, mock_load_hierarchy: Mock) -> None:
        """Test that EnvConfig can be reset and reconfigured."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("ANTHROPIC_API_KEY=first-key\n")
            env_file_path = f.name

        # Mock the hierarchy loading to return a settings instance with empty anthropic_api_key
        mock_settings = Mock()
        mock_settings.anthropic_api_key = ""
        mock_load_hierarchy.return_value = mock_settings

        try:
            # Act
            EnvConfig.set_env_config(env_file_path)
            first_config = EnvConfig.get_env_config()
            assert first_config.anthropic_api_key == "first-key"

            # Reset by setting to None and reconfiguring
            EnvConfig._env_config = None
            EnvConfig.set_env_config()  # Should use default hierarchical loading
            second_config = EnvConfig.get_env_config()

            # Assert
            assert second_config is not None
            # Should use defaults since no hierarchy file exists
            assert second_config.anthropic_api_key == ""
            mock_load_hierarchy.assert_called_once()
        finally:
            Path(env_file_path).unlink()
