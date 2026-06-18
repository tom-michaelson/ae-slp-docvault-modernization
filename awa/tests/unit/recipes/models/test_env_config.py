"""Unit tests for models/env_config.py."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from cookbook.recipes.models.env_config import EnvConfig, Settings


class TestSettings:
    """Test cases for Settings model."""

    @patch.dict(os.environ, {}, clear=True)
    def test_settings_default_values(self) -> None:
        """Test Settings creation with default values."""
        settings = Settings()

        assert settings.config_path == Path("config.yaml")
        assert settings.log_level == "INFO"
        assert settings.log_path == "logs"
        assert settings.log_file_rotation_size == "1 MB"
        assert settings.log_enable_json is False
        assert settings.log_console_enabled is True
        assert settings.log_file_enabled is True

    def test_settings_custom_values(self) -> None:
        """Test Settings creation with custom values."""
        settings = Settings(
            config_path=Path("custom.yaml"),
            log_level="DEBUG",
            log_path="custom_logs",
            log_file_rotation_size="5 MB",
            log_enable_json=True,
            log_console_enabled=False,
            log_file_enabled=False,
        )

        assert settings.config_path == Path("custom.yaml")
        assert settings.log_level == "DEBUG"
        assert settings.log_path == "custom_logs"
        assert settings.log_file_rotation_size == "5 MB"
        assert settings.log_enable_json is True
        assert settings.log_console_enabled is False
        assert settings.log_file_enabled is False

    def test_settings_model_config(self) -> None:
        """Test Settings model configuration."""
        settings = Settings()

        assert hasattr(settings, "model_config")
        assert hasattr(Settings, "model_config")
        assert Settings.model_config["env_file"] == []
        assert Settings.model_config["extra"] == "allow"

    @patch("cookbook.recipes.models.env_config.ConfigPaths.get_config_file_paths")
    def test_load_with_hierarchy_no_existing_files(self, mock_get_paths: Mock) -> None:
        """Test load_with_hierarchy when no config files exist."""
        # Mock config paths with non-existent files
        mock_env_path1 = Mock(spec=Path)
        mock_env_path1.exists.return_value = False
        mock_env_path2 = Mock(spec=Path)
        mock_env_path2.exists.return_value = False

        mock_get_paths.return_value = {
            "env_files": [mock_env_path1, mock_env_path2],
            "yaml_files": [],
        }

        settings = Settings.load_with_hierarchy()

        assert isinstance(settings, Settings)
        mock_get_paths.assert_called_once()
        mock_env_path1.exists.assert_called_once()
        mock_env_path2.exists.assert_called_once()

    @patch("cookbook.recipes.models.env_config.ConfigPaths.get_config_file_paths")
    def test_load_with_hierarchy_with_existing_files(self, mock_get_paths: Mock) -> None:
        """Test load_with_hierarchy when config files exist."""
        # Create temporary files to simulate existing config files
        with (
            tempfile.NamedTemporaryFile(suffix=".env", delete=False) as tmp1,
            tempfile.NamedTemporaryFile(suffix=".env", delete=False) as tmp2,
        ):
            tmp1_path = Path(tmp1.name)
            tmp2_path = Path(tmp2.name)

            # Write some config to files
            tmp1_path.write_text("LOG_LEVEL=DEBUG\n")
            tmp2_path.write_text("LOG_PATH=test_logs\n")

            try:
                mock_get_paths.return_value = {
                    "env_files": [tmp1_path, tmp2_path],
                    "yaml_files": [],
                }

                settings = Settings.load_with_hierarchy()

                assert isinstance(settings, Settings)
                mock_get_paths.assert_called_once()
                # Verify that model_config was updated with env files
                assert "env_file" in Settings.model_config

            finally:
                # Cleanup
                tmp1_path.unlink(missing_ok=True)
                tmp2_path.unlink(missing_ok=True)

    @patch("cookbook.recipes.models.env_config.ConfigPaths.get_config_file_paths")
    def test_load_with_hierarchy_file_precedence(self, mock_get_paths: Mock) -> None:
        """Test load_with_hierarchy respects file precedence order."""
        # Create mock paths that exist
        mock_env_path1 = Mock(spec=Path)
        mock_env_path1.exists.return_value = True
        mock_env_path1.__str__ = Mock(return_value="/path/to/env1")

        mock_env_path2 = Mock(spec=Path)
        mock_env_path2.exists.return_value = True
        mock_env_path2.__str__ = Mock(return_value="/path/to/env2")

        mock_get_paths.return_value = {
            "env_files": [mock_env_path1, mock_env_path2],
            "yaml_files": [],
        }

        settings = Settings.load_with_hierarchy()

        assert isinstance(settings, Settings)
        # Verify the env_files were processed in reverse order (lowest to highest precedence)
        expected_files = ["/path/to/env2", "/path/to/env1"]  # Reversed order
        assert Settings.model_config["env_file"] == expected_files


class TestEnvConfig:
    """Test cases for EnvConfig class."""

    def setup_method(self) -> None:
        """Reset EnvConfig state before each test."""
        EnvConfig._env_config = None

    def test_env_config_initial_state(self) -> None:
        """Test EnvConfig initial state."""
        assert EnvConfig._env_config is None

    @patch("cookbook.recipes.models.env_config.Settings.load_with_hierarchy")
    def test_set_env_config_without_file_path(self, mock_load_hierarchy: Mock) -> None:
        """Test set_env_config without explicit file path uses hierarchical loading."""
        mock_settings = Mock(spec=Settings)
        mock_load_hierarchy.return_value = mock_settings

        EnvConfig.set_env_config()

        assert EnvConfig._env_config == mock_settings
        mock_load_hierarchy.assert_called_once()

    @patch("cookbook.recipes.models.env_config.Settings")
    def test_set_env_config_with_file_path(self, mock_settings_class: Mock) -> None:
        """Test set_env_config with explicit file path."""
        mock_settings = Mock(spec=Settings)
        mock_settings_class.return_value = mock_settings

        EnvConfig.set_env_config("/path/to/config.env")

        assert EnvConfig._env_config == mock_settings
        mock_settings_class.assert_called_once()

    @patch("cookbook.recipes.models.env_config.Settings.load_with_hierarchy")
    @patch("cookbook.recipes.models.env_config.logger")
    def test_set_env_config_validation_error(self, mock_logger: Mock, mock_load_hierarchy: Mock) -> None:
        """Test set_env_config handles ValidationError properly."""
        validation_error = ValidationError.from_exception_data("Settings", [])
        mock_load_hierarchy.side_effect = validation_error

        with pytest.raises(ValidationError):
            EnvConfig.set_env_config()

        mock_logger.error.assert_called_once()
        # Verify the error message contains the validation error
        error_call = mock_logger.error.call_args[0][0]
        assert "EnvConfig validation error:" in error_call

    def test_update_env_config(self) -> None:
        """Test update_env_config calls set_env_config with file path."""
        with patch.object(EnvConfig, "set_env_config") as mock_set:
            EnvConfig.update_env_config("/path/to/config.env")
            mock_set.assert_called_once_with("/path/to/config.env")

    @patch("cookbook.recipes.models.env_config.Settings.load_with_hierarchy")
    def test_get_env_config_initializes_when_none(self, mock_load_hierarchy: Mock) -> None:
        """Test get_env_config initializes config when _env_config is None."""
        mock_settings = Mock(spec=Settings)
        mock_load_hierarchy.return_value = mock_settings

        # Ensure _env_config is None
        EnvConfig._env_config = None

        result = EnvConfig.get_env_config()

        assert result == mock_settings
        assert EnvConfig._env_config == mock_settings
        mock_load_hierarchy.assert_called_once()

    def test_get_env_config_returns_existing(self) -> None:
        """Test get_env_config returns existing config when already set."""
        mock_settings = Mock(spec=Settings)
        EnvConfig._env_config = mock_settings

        with patch.object(EnvConfig, "set_env_config") as mock_set:
            result = EnvConfig.get_env_config()

            assert result == mock_settings
            mock_set.assert_not_called()

    @patch("cookbook.recipes.models.env_config.Settings.load_with_hierarchy")
    def test_get_env_config_runtime_error_when_still_none(self, mock_load_hierarchy: Mock) -> None:
        """Test get_env_config raises RuntimeError when config remains None after initialization."""
        # Mock set_env_config to not set _env_config (simulate failure)
        mock_load_hierarchy.return_value = None

        EnvConfig._env_config = None

        with patch.object(EnvConfig, "set_env_config") as mock_set:
            # Make set_env_config not change _env_config to simulate failure
            def side_effect() -> None:
                EnvConfig._env_config = None

            mock_set.side_effect = side_effect

            with pytest.raises(RuntimeError) as exc_info:
                EnvConfig.get_env_config()

            assert "EnvConfig could not be initialized and is None." in str(exc_info.value)

    @patch("cookbook.recipes.models.env_config.os.environ.get")
    def test_get_env_config_value_with_existing_config(self, mock_env_get: Mock) -> None:
        """Test get_env_config_value when config already exists."""
        mock_settings = Mock(spec=Settings)
        EnvConfig._env_config = mock_settings
        mock_env_get.return_value = "test_value"

        result = EnvConfig.get_env_config_value("TEST_KEY")

        assert result == "test_value"
        mock_env_get.assert_called_once_with("TEST_KEY")

    @patch("cookbook.recipes.models.env_config.os.environ.get")
    @patch("cookbook.recipes.models.env_config.Settings.load_with_hierarchy")
    def test_get_env_config_value_initializes_when_none(self, mock_load_hierarchy: Mock, mock_env_get: Mock) -> None:
        """Test get_env_config_value initializes config when _env_config is None."""
        mock_settings = Mock(spec=Settings)
        mock_load_hierarchy.return_value = mock_settings
        mock_env_get.return_value = "initialized_value"

        EnvConfig._env_config = None

        result = EnvConfig.get_env_config_value("INIT_KEY")

        assert result == "initialized_value"
        assert EnvConfig._env_config == mock_settings
        mock_load_hierarchy.assert_called_once()
        mock_env_get.assert_called_once_with("INIT_KEY")

    @patch("cookbook.recipes.models.env_config.os.environ.get")
    def test_get_env_config_value_returns_none(self, mock_env_get: Mock) -> None:
        """Test get_env_config_value returns None when environment variable doesn't exist."""
        mock_settings = Mock(spec=Settings)
        EnvConfig._env_config = mock_settings
        mock_env_get.return_value = None

        result = EnvConfig.get_env_config_value("NONEXISTENT_KEY")

        assert result is None
        mock_env_get.assert_called_once_with("NONEXISTENT_KEY")

    def test_env_config_class_variable_persistence(self) -> None:
        """Test that _env_config class variable persists across method calls."""
        mock_settings = Mock(spec=Settings)

        # Set config
        EnvConfig._env_config = mock_settings

        # Verify persistence
        assert EnvConfig._env_config == mock_settings

        # Call different methods and verify config persists
        with patch("awa.core.models.config.env_config.os.environ.get", return_value="test"):
            result = EnvConfig.get_env_config_value("KEY")
            assert result == "test"
            assert EnvConfig._env_config == mock_settings

    @patch("cookbook.recipes.models.env_config.Settings")
    @patch("cookbook.recipes.models.env_config.logger")
    def test_set_env_config_with_file_path_validation_error(self, mock_logger: Mock, mock_settings_class: Mock) -> None:
        """Test set_env_config with file path handles ValidationError."""
        validation_error = ValidationError.from_exception_data("Settings", [])
        mock_settings_class.side_effect = validation_error

        with pytest.raises(ValidationError):
            EnvConfig.set_env_config("/invalid/path")

        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        assert "EnvConfig validation error:" in error_call


class TestSettingsFieldValidation:
    """Test cases for Settings field validation and type conversion."""

    def test_settings_path_field_conversion(self) -> None:
        """Test that config_path field accepts string and converts to Path."""
        settings = Settings(config_path="test.yaml")
        assert isinstance(settings.config_path, Path)
        assert settings.config_path == Path("test.yaml")

    def test_settings_boolean_field_conversion(self) -> None:
        """Test boolean field type conversion."""
        # Test string to boolean conversion
        settings = Settings(
            log_enable_json="true",
            log_console_enabled="false",
            log_file_enabled="1",
        )

        assert settings.log_enable_json is True
        assert settings.log_console_enabled is False
        assert settings.log_file_enabled is True

    def test_settings_extra_allow_configuration(self) -> None:
        """Test that extra='allow' permits additional fields."""
        # This should not raise an error due to extra="allow"
        settings = Settings(extra_field="extra_value")

        # Verify the extra field is available
        assert hasattr(settings, "extra_field")
        assert settings.extra_field == "extra_value"


class TestIntegrationScenarios:
    """Integration test scenarios for EnvConfig usage patterns."""

    def setup_method(self) -> None:
        """Reset EnvConfig state before each test."""
        EnvConfig._env_config = None

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG", "LOG_PATH": "integration_logs"})
    @patch("cookbook.recipes.models.env_config.ConfigPaths.get_config_file_paths")
    def test_full_workflow_with_environment_variables(self, mock_get_paths: Mock) -> None:
        """Test complete workflow with environment variables set."""
        # Mock no config files exist
        mock_env_path = Mock(spec=Path)
        mock_env_path.exists.return_value = False

        mock_get_paths.return_value = {
            "env_files": [mock_env_path],
            "yaml_files": [],
        }

        # Initialize config
        EnvConfig.set_env_config()

        # Get config and verify environment variables are accessible
        config = EnvConfig.get_env_config()
        assert isinstance(config, Settings)

        # Verify environment variable access
        log_level = EnvConfig.get_env_config_value("LOG_LEVEL")
        assert log_level == "DEBUG"

        log_path = EnvConfig.get_env_config_value("LOG_PATH")
        assert log_path == "integration_logs"

    def test_multiple_env_config_calls_singleton_behavior(self) -> None:
        """Test that multiple calls maintain singleton-like behavior."""
        with patch("cookbook.recipes.models.env_config.Settings.load_with_hierarchy") as mock_load:
            mock_settings = Mock(spec=Settings)
            mock_load.return_value = mock_settings

            # First call should initialize
            config1 = EnvConfig.get_env_config()
            assert config1 == mock_settings

            # Second call should return same instance without re-initializing
            config2 = EnvConfig.get_env_config()
            assert config2 == mock_settings
            assert config1 is config2

            # load_with_hierarchy should only be called once
            mock_load.assert_called_once()

    def test_update_env_config_replaces_existing(self) -> None:
        """Test that update_env_config replaces existing configuration."""
        # Set initial config
        with patch("cookbook.recipes.models.env_config.Settings.load_with_hierarchy") as mock_load1:
            mock_settings1 = Mock(spec=Settings)
            mock_load1.return_value = mock_settings1

            EnvConfig.set_env_config()
            assert EnvConfig._env_config == mock_settings1

        # Update with new file path
        with patch("cookbook.recipes.models.env_config.Settings") as mock_settings_class:
            mock_settings2 = Mock(spec=Settings)
            mock_settings_class.return_value = mock_settings2

            EnvConfig.update_env_config("/new/config.env")
            assert EnvConfig._env_config == mock_settings2
            assert EnvConfig._env_config != mock_settings1
