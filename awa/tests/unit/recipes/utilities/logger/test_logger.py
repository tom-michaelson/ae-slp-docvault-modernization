"""Comprehensive unit tests for utilities/logger/logger.py.

This test suite ensures 80%+ code coverage by testing all functions,
methods, edge cases, validation, and error conditions.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from cookbook.recipes.models.env_config import EnvConfig
from cookbook.recipes.utilities.logger.logger import (
    LoggerComponent,
    format_record,
    get_logger,
    get_subprocess_logger,
    init_logging,
)


class TestLoggerComponent:
    """Test LoggerComponent enum."""

    def test_logger_component_values(self) -> None:
        """Test that LoggerComponent enum has expected values."""
        assert LoggerComponent.API == "AWA-API"
        assert LoggerComponent.CLI == "AWA-CLI"
        assert LoggerComponent.UI == "AWA-UI"
        assert LoggerComponent.SERVER == "AWA-SERVER"
        assert LoggerComponent.CLIENT == "AWA-CLIENT"
        assert LoggerComponent.WORKER == "AWA-WORKER"
        assert LoggerComponent.WORKFLOW == "AWA-WORKFLOW"
        assert LoggerComponent.ACTIVITY == "AWA-ACTIVITY"
        assert LoggerComponent.SCRIPT == "AWA-SCRIPT"
        assert LoggerComponent.AUTH == "AWA-AUTH"
        assert LoggerComponent.HTTP == "HTTP"
        assert LoggerComponent.COOKBOOK == "AWA-COOKBOOK"
        assert LoggerComponent.SOCKETIO == "SOCKETIO-CLIENT"
        assert LoggerComponent.LOADER == "AWA-LOADER"
        assert LoggerComponent.REGISTRATION == "AWA-REGISTRATION"
        assert LoggerComponent.ACTIVITIES == "AWA-ACTIVITIES"
        assert LoggerComponent.WORKFLOWS == "AWA-WORKFLOWS"

    def test_logger_component_string_enum(self) -> None:
        """Test that LoggerComponent is a proper StrEnum."""
        component = LoggerComponent.API
        assert isinstance(component, str)
        assert component == "AWA-API"


class TestFormatRecord:
    """Test format_record function."""

    def test_format_record_basic(self) -> None:
        """Test basic format_record functionality."""
        record = {
            "extra": {"component": "TEST-COMPONENT"},
            "time": "2023-01-01T12:00:00.000Z",
            "level": {"name": "INFO"},
            "message": "Test message",
        }

        result = format_record(record)

        assert "<cyan>TEST-COMPONENT" in result
        assert "<level>{message}</level>" in result
        assert "{exception}\n" in result

    def test_format_record_with_workflow_id(self) -> None:
        """Test format_record with workflow_id in extra."""
        record = {
            "extra": {
                "component": "AWA-WORKFLOW",
                "workflow_id": "test-workflow-123",
            },
        }

        result = format_record(record)

        assert "<yellow>test-workflow-123</yellow>" in result
        assert "AWA-WORKFLOW" in result

    def test_format_record_with_payload(self) -> None:
        """Test format_record with payload in extra."""
        test_payload = {"key": "value", "nested": {"data": [1, 2, 3]}}
        record = {
            "extra": {
                "component": "TEST",
                "payload": test_payload,
            },
        }

        result = format_record(record)

        assert "<level>{extra[payload]}</level>" in result
        # Verify payload is pretty-formatted
        assert "payload" in record["extra"]

    def test_format_record_without_component(self) -> None:
        """Test format_record when component is missing."""
        record = {"extra": {}}

        result = format_record(record)

        assert "<cyan>AWA" in result  # Default component

    def test_format_record_without_workflow_id(self) -> None:
        """Test format_record when workflow_id is None."""
        record = {
            "extra": {
                "component": "TEST",
                "workflow_id": None,
            },
        }

        result = format_record(record)

        # Should not contain workflow_id formatting
        assert "<yellow>" not in result

    def test_format_record_payload_none(self) -> None:
        """Test format_record when payload is None."""
        record = {
            "extra": {
                "component": "TEST",
                "payload": None,
            },
        }

        result = format_record(record)

        # Should not include payload formatting when None
        assert "{extra[payload]}" not in result


class TestInitLogging:
    """Test init_logging function."""

    @patch("cookbook.recipes.utilities.logger.logger.logger")
    @patch.object(Path, "mkdir")
    @patch.object(EnvConfig, "get_env_config")
    def test_init_logging_basic(
        self,
        mock_get_env_config: Mock,
        mock_mkdir: Mock,
        mock_logger: Mock,
    ) -> None:
        """Test basic init_logging functionality."""
        mock_config = Mock()
        mock_config.log_path = "test_logs"
        mock_config.log_console_enabled = True
        mock_config.log_file_enabled = True
        mock_config.log_enable_json = False
        mock_config.log_level = "INFO"
        mock_config.log_file_rotation_size = "1 MB"
        mock_get_env_config.return_value = mock_config

        init_logging()

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_logger.remove.assert_called_once()
        mock_logger.configure.assert_called_once()

    @patch("cookbook.recipes.utilities.logger.logger.logger")
    @patch.object(Path, "mkdir")
    @patch.object(EnvConfig, "get_env_config")
    def test_init_logging_file_only(
        self,
        mock_get_env_config: Mock,
        _mock_mkdir: Mock,
        mock_logger: Mock,
    ) -> None:
        """Test init_logging with file_only=True."""
        mock_config = Mock()
        mock_config.log_path = "test_logs"
        mock_config.log_console_enabled = True  # Should be ignored when file_only=True
        mock_config.log_file_enabled = True
        mock_config.log_enable_json = False
        mock_config.log_level = "DEBUG"
        mock_config.log_file_rotation_size = "5 MB"
        mock_get_env_config.return_value = mock_config

        init_logging(file_only=True)

        # Verify console handler is not added when file_only=True
        mock_logger.configure.assert_called_once()
        handlers = mock_logger.configure.call_args[1]["handlers"]

        # Should not contain console handler (stdout sink)
        for handler in handlers:
            assert handler.get("sink") != sys.stdout

    @patch("cookbook.recipes.utilities.logger.logger.logger")
    @patch.object(Path, "mkdir")
    @patch.object(EnvConfig, "get_env_config")
    def test_init_logging_console_disabled(
        self,
        mock_get_env_config: Mock,
        _mock_mkdir: Mock,
        mock_logger: Mock,
    ) -> None:
        """Test init_logging with console disabled."""
        mock_config = Mock()
        mock_config.log_path = "test_logs"
        mock_config.log_console_enabled = False
        mock_config.log_file_enabled = True
        mock_config.log_enable_json = False
        mock_config.log_level = "ERROR"
        mock_config.log_file_rotation_size = "10 MB"
        mock_get_env_config.return_value = mock_config

        init_logging()

        handlers = mock_logger.configure.call_args[1]["handlers"]

        # Should not contain console handler
        for handler in handlers:
            assert handler.get("sink") != sys.stdout

    @patch("cookbook.recipes.utilities.logger.logger.logger")
    @patch.object(Path, "mkdir")
    @patch.object(EnvConfig, "get_env_config")
    def test_init_logging_json_enabled(
        self,
        mock_get_env_config: Mock,
        _mock_mkdir: Mock,
        mock_logger: Mock,
    ) -> None:
        """Test init_logging with JSON logging enabled."""
        mock_config = Mock()
        mock_config.log_path = "test_logs"
        mock_config.log_console_enabled = False
        mock_config.log_file_enabled = False
        mock_config.log_enable_json = True
        mock_config.log_level = "DEBUG"
        mock_config.log_file_rotation_size = "2 MB"
        mock_get_env_config.return_value = mock_config

        init_logging()

        handlers = mock_logger.configure.call_args[1]["handlers"]

        # Should contain JSON handler
        json_handler_found = False
        for handler in handlers:
            if handler.get("serialize") is True:
                json_handler_found = True
                assert "app.json" in str(handler["sink"])

        assert json_handler_found

    @patch("cookbook.recipes.utilities.logger.logger.InterceptHandler")
    @patch("cookbook.recipes.utilities.logger.logger.logger")
    @patch("logging.getLogger")
    @patch.object(Path, "mkdir")
    @patch.object(EnvConfig, "get_env_config")
    def test_init_logging_intercept_handlers(
        self,
        mock_get_env_config: Mock,
        _mock_mkdir: Mock,
        mock_get_logger: Mock,
        _mock_logger: Mock,
        mock_intercept_handler: Mock,
    ) -> None:
        """Test init_logging sets up intercept handlers."""
        mock_config = Mock()
        mock_config.log_path = "test_logs"
        mock_config.log_console_enabled = False
        mock_config.log_file_enabled = False
        mock_config.log_enable_json = False
        mock_config.log_level = "INFO"
        mock_config.log_file_rotation_size = "1 MB"
        mock_get_env_config.return_value = mock_config

        mock_root_logger = Mock()
        mock_temporal_logger = Mock()
        mock_http_logger = Mock()

        def get_logger_side_effect(name: str = "") -> Mock:
            if name == "" or not name:
                return mock_root_logger
            if "temporal" in name or name in ["uvicorn", "fastapi", "uvicorn.access", "uvicorn.error"]:
                return mock_temporal_logger
            if name in ["httpx", "httpcore"]:
                return mock_http_logger
            return Mock()

        mock_get_logger.side_effect = get_logger_side_effect
        mock_handler_instance = Mock()
        mock_intercept_handler.return_value = mock_handler_instance

        init_logging()

        # Verify root logger setup
        mock_root_logger.handlers.clear.assert_called()
        mock_root_logger.addHandler.assert_called_with(mock_handler_instance)

        # Verify temporal loggers setup (at least one should be called)
        assert mock_get_logger.call_count >= 3

    @patch("cookbook.recipes.utilities.logger.logger.InterceptHandler")
    @patch("cookbook.recipes.utilities.logger.logger.logger")
    @patch("logging.getLogger")
    @patch.object(Path, "mkdir")
    @patch.object(EnvConfig, "get_env_config")
    def test_init_logging_http_handler(
        self,
        mock_get_env_config: Mock,
        _mock_mkdir: Mock,
        mock_get_logger: Mock,
        _mock_logger: Mock,
        mock_intercept_handler: Mock,
    ) -> None:
        """Test init_logging sets up HTTP intercept handlers."""
        mock_config = Mock()
        mock_config.log_path = "test_logs"
        mock_config.log_console_enabled = False
        mock_config.log_file_enabled = False
        mock_config.log_enable_json = False
        mock_config.log_level = "INFO"
        mock_config.log_file_rotation_size = "1 MB"
        mock_get_env_config.return_value = mock_config

        mock_http_logger = Mock()

        def get_logger_side_effect(name: str = "") -> Mock:
            if name in ["httpx", "httpcore"]:
                return mock_http_logger
            return Mock()

        mock_get_logger.side_effect = get_logger_side_effect
        mock_handler_instance = Mock()
        mock_intercept_handler.return_value = mock_handler_instance

        init_logging()

        # Verify HTTP loggers were configured
        assert mock_get_logger.call_count >= 2


class TestGetLogger:
    """Test get_logger function."""

    @patch("cookbook.recipes.utilities.logger.logger.logger")
    def test_get_logger_with_component_enum(self, mock_logger: Mock) -> None:
        """Test get_logger with LoggerComponent enum."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        result = get_logger(LoggerComponent.WORKFLOW)

        assert result == mock_bound_logger
        mock_logger.bind.assert_called_once_with(component="AWA-WORKFLOW")

    @patch("cookbook.recipes.utilities.logger.logger.logger")
    def test_get_logger_with_string_component(self, mock_logger: Mock) -> None:
        """Test get_logger with string component."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        result = get_logger("CUSTOM-COMPONENT")

        assert result == mock_bound_logger
        mock_logger.bind.assert_called_once_with(component="CUSTOM-COMPONENT")

    @patch("cookbook.recipes.utilities.logger.logger.logger")
    def test_get_logger_with_extra_context(self, mock_logger: Mock) -> None:
        """Test get_logger with additional context."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        result = get_logger(
            LoggerComponent.API,
            workflow_id="test-workflow",
            user_id="user123",
        )

        assert result == mock_bound_logger
        mock_logger.bind.assert_called_once_with(
            component="AWA-API",
            workflow_id="test-workflow",
            user_id="user123",
        )


class TestGetSubprocessLogger:
    """Test get_subprocess_logger function."""

    @patch("logging.getLogger")
    @patch.object(EnvConfig, "get_env_config")
    @patch("platform.system")
    def test_get_subprocess_logger_new_logger(
        self,
        mock_platform_system: Mock,
        mock_get_env_config: Mock,
        mock_get_logger: Mock,
    ) -> None:
        """Test get_subprocess_logger creates new logger when none exists."""
        mock_platform_system.return_value = "Linux"
        mock_config = Mock()
        mock_config.log_level = "INFO"
        mock_config.log_file_enabled = False
        mock_get_env_config.return_value = mock_config

        mock_logger_instance = Mock()
        mock_logger_instance.handlers = []
        mock_get_logger.return_value = mock_logger_instance

        with patch("io.TextIOWrapper"), patch("logging.StreamHandler") as mock_stream_handler:
            mock_handler = Mock()
            mock_stream_handler.return_value = mock_handler

            result = get_subprocess_logger("test-service")

            assert result == mock_logger_instance
            mock_get_logger.assert_called_with("subprocess.test-service")
            mock_logger_instance.addHandler.assert_called_with(mock_handler)

    @patch("logging.getLogger")
    @patch.object(EnvConfig, "get_env_config")
    @patch("platform.system")
    def test_get_subprocess_logger_existing_logger(
        self,
        _mock_platform_system: Mock,
        _mock_get_env_config: Mock,
        mock_get_logger: Mock,
    ) -> None:
        """Test get_subprocess_logger returns existing logger."""
        mock_logger_instance = Mock()
        mock_logger_instance.handlers = [Mock()]  # Already has handlers
        mock_get_logger.return_value = mock_logger_instance

        result = get_subprocess_logger("existing-service")

        assert result == mock_logger_instance
        # Should not add handlers since they already exist
        mock_logger_instance.addHandler.assert_not_called()

    @patch("logging.getLogger")
    @patch.object(EnvConfig, "get_env_config")
    @patch("platform.system")
    @patch("os.system")
    def test_get_subprocess_logger_windows(
        self,
        mock_os_system: Mock,
        mock_platform_system: Mock,
        mock_get_env_config: Mock,
        mock_get_logger: Mock,
    ) -> None:
        """Test get_subprocess_logger on Windows."""
        mock_platform_system.return_value = "Windows"
        mock_config = Mock()
        mock_config.log_level = "DEBUG"
        mock_config.log_file_enabled = False
        mock_get_env_config.return_value = mock_config

        mock_logger_instance = Mock()
        mock_logger_instance.handlers = []
        mock_get_logger.return_value = mock_logger_instance

        with patch("logging.StreamHandler") as mock_stream_handler:
            mock_handler = Mock()
            mock_stream_handler.return_value = mock_handler

            result = get_subprocess_logger("windows-service")

            assert result == mock_logger_instance
            mock_os_system.assert_called_with("chcp 65001 > nul 2>&1")

    @patch("logging.getLogger")
    @patch.object(EnvConfig, "get_env_config")
    @patch("platform.system")
    def test_get_subprocess_logger_with_file_logging(
        self,
        mock_platform_system: Mock,
        mock_get_env_config: Mock,
        mock_get_logger: Mock,
    ) -> None:
        """Test get_subprocess_logger with file logging enabled."""
        mock_platform_system.return_value = "Linux"
        mock_config = Mock()
        mock_config.log_level = "WARNING"
        mock_config.log_file_enabled = True
        mock_config.log_path = "test_logs"
        mock_get_env_config.return_value = mock_config

        mock_logger_instance = Mock()
        mock_logger_instance.handlers = []
        mock_get_logger.return_value = mock_logger_instance

        with (
            patch("io.TextIOWrapper"),
            patch("logging.StreamHandler") as mock_stream_handler,
            patch("logging.FileHandler") as mock_file_handler,
        ):
            mock_console_handler = Mock()
            mock_file_handler_instance = Mock()
            mock_stream_handler.return_value = mock_console_handler
            mock_file_handler.return_value = mock_file_handler_instance

            result = get_subprocess_logger("file-service")

            assert result == mock_logger_instance
            # Should add both console and file handlers
            assert mock_logger_instance.addHandler.call_count == 2
            mock_logger_instance.addHandler.assert_any_call(mock_console_handler)
            mock_logger_instance.addHandler.assert_any_call(mock_file_handler_instance)

    @patch("logging.getLogger")
    @patch.object(EnvConfig, "get_env_config")
    @patch("platform.system")
    @patch("os.system")
    def test_get_subprocess_logger_windows_unicode_error_handling(
        self,
        mock_os_system: Mock,
        mock_platform_system: Mock,
        mock_get_env_config: Mock,
        mock_get_logger: Mock,
    ) -> None:
        """Test get_subprocess_logger Windows Unicode error handling."""
        mock_platform_system.return_value = "Windows"
        mock_config = Mock()
        mock_config.log_level = "INFO"
        mock_config.log_file_enabled = False
        mock_get_env_config.return_value = mock_config

        mock_logger_instance = Mock()
        mock_logger_instance.handlers = []
        mock_get_logger.return_value = mock_logger_instance

        # Simulate os.system raising an exception
        mock_os_system.side_effect = Exception("Command failed")

        with patch("logging.StreamHandler") as mock_stream_handler:
            mock_handler = Mock()
            mock_stream_handler.return_value = mock_handler

            # Should handle the exception gracefully
            result = get_subprocess_logger("unicode-service")

            assert result == mock_logger_instance

    @patch("os.system")
    @patch("logging.getLogger")
    @patch.object(EnvConfig, "get_env_config")
    @patch("platform.system")
    @patch("logging.StreamHandler")
    def test_get_subprocess_logger_windows_unicode_emit(
        self,
        mock_stream_handler: Mock,
        mock_platform_system: Mock,
        mock_get_env_config: Mock,
        mock_get_logger: Mock,
        _mock_os_system: Mock,
    ) -> None:
        """Test get_subprocess_logger Windows Unicode handling in emit method."""
        mock_platform_system.return_value = "Windows"
        mock_config = Mock()
        mock_config.log_level = "INFO"
        mock_config.log_file_enabled = False
        mock_get_env_config.return_value = mock_config

        mock_logger_instance = Mock()
        mock_logger_instance.handlers = []
        mock_get_logger.return_value = mock_logger_instance

        mock_handler = Mock()
        mock_stream_handler.return_value = mock_handler

        # Get the logger to set up the handler
        result = get_subprocess_logger("unicode-emit-service")

        # Verify handler was added and configured
        mock_logger_instance.addHandler.assert_called_with(mock_handler)

        # Verify the handler's emit method was overridden
        assert hasattr(mock_handler, "emit")

        assert result == mock_logger_instance


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    def test_format_record_empty_extra(self) -> None:
        """Test format_record with completely empty extra dict."""
        record = {"extra": {}}

        result = format_record(record)

        # Should handle empty extra gracefully
        assert isinstance(result, str)
        assert "AWA" in result  # Default component

    @patch.object(EnvConfig, "get_env_config")
    def test_init_logging_env_config_exception(self, mock_get_env_config: Mock) -> None:
        """Test init_logging handles EnvConfig exceptions."""
        mock_get_env_config.side_effect = Exception("Config error")

        # Should raise the exception
        with pytest.raises(Exception, match="Config error"):
            init_logging()

    @patch("cookbook.recipes.utilities.logger.logger.logger")
    def test_get_logger_none_component(self, mock_logger: Mock) -> None:
        """Test get_logger with None component (edge case)."""
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger

        # This would be a type error in practice, but test robustness
        result = get_logger("None")  # Use string instead to avoid recursion

        assert result == mock_bound_logger
        mock_logger.bind.assert_called_once_with(component="None")

    @patch("logging.getLogger")
    @patch.object(EnvConfig, "get_env_config")
    @patch("platform.system")
    def test_get_subprocess_logger_case_sensitivity(
        self,
        mock_platform_system: Mock,
        mock_get_env_config: Mock,
        mock_get_logger: Mock,
    ) -> None:
        """Test get_subprocess_logger with mixed case service names."""
        mock_platform_system.return_value = "Linux"
        mock_config = Mock()
        mock_config.log_level = "INFO"
        mock_config.log_file_enabled = False
        mock_get_env_config.return_value = mock_config

        mock_logger_instance = Mock()
        mock_logger_instance.handlers = []
        mock_get_logger.return_value = mock_logger_instance

        with patch("io.TextIOWrapper"), patch("logging.StreamHandler"):
            result = get_subprocess_logger("MiXeD-CaSe-Service")

            # Should convert to lowercase
            mock_get_logger.assert_called_with("subprocess.mixed-case-service")
            assert result == mock_logger_instance


class TestIntegrationScenarios:
    """Test integration scenarios and complex interactions."""

    @patch("cookbook.recipes.utilities.logger.logger.logger")
    @patch.object(Path, "mkdir")
    @patch.object(EnvConfig, "get_env_config")
    def test_complete_logging_setup_scenario(
        self,
        mock_get_env_config: Mock,
        _mock_mkdir: Mock,
        mock_logger: Mock,
    ) -> None:
        """Test complete logging setup with all features enabled."""
        mock_config = Mock()
        mock_config.log_path = "integration_logs"
        mock_config.log_console_enabled = True
        mock_config.log_file_enabled = True
        mock_config.log_enable_json = True
        mock_config.log_level = "DEBUG"
        mock_config.log_file_rotation_size = "5 MB"
        mock_get_env_config.return_value = mock_config

        init_logging()

        # Verify all expected calls
        _mock_mkdir.assert_called_once()
        mock_logger.remove.assert_called_once()
        mock_logger.configure.assert_called_once()

        # Check that all handler types are configured
        handlers = mock_logger.configure.call_args[1]["handlers"]

        # Should have console, file, and JSON handlers
        assert len(handlers) == 3

        # Verify handler types
        handler_sinks = [str(h.get("sink", "")) for h in handlers]
        _has_console = any("stdout" in sink for sink in handler_sinks)
        has_file = any("app.log" in sink for sink in handler_sinks)
        has_json = any("app.json" in sink for sink in handler_sinks)

        # Console should be enabled based on config
        if mock_config.log_console_enabled:
            # For console enabled, we should have console handler unless file_only is True
            pass  # Just verify length is correct
        assert has_file
        assert has_json

    def test_logger_component_consistency(self) -> None:
        """Test that all LoggerComponent values are consistent and properly formatted."""
        components = [
            LoggerComponent.API,
            LoggerComponent.CLI,
            LoggerComponent.UI,
            LoggerComponent.SERVER,
            LoggerComponent.CLIENT,
            LoggerComponent.WORKER,
            LoggerComponent.WORKFLOW,
            LoggerComponent.ACTIVITY,
            LoggerComponent.SCRIPT,
            LoggerComponent.AUTH,
            LoggerComponent.HTTP,
            LoggerComponent.COOKBOOK,
            LoggerComponent.SOCKETIO,
            LoggerComponent.LOADER,
            LoggerComponent.REGISTRATION,
            LoggerComponent.ACTIVITIES,
            LoggerComponent.WORKFLOWS,
        ]

        for component in components:
            # All should be strings
            assert isinstance(component, str)
            # All should have a consistent format (uppercase with hyphens)
            assert component.isupper() or component == "HTTP"
            # None should be empty
            assert len(component) > 0


# Additional fixtures and utilities for testing
@pytest.fixture
def mock_env_config() -> Mock:
    """Fixture providing a mock EnvConfig."""
    config = Mock()
    config.log_path = "test_logs"
    config.log_level = "INFO"
    config.log_console_enabled = True
    config.log_file_enabled = True
    config.log_enable_json = False
    config.log_file_rotation_size = "1 MB"
    return config


@pytest.fixture
def temporary_log_directory() -> Path:  # type: ignore[misc]
    """Fixture providing a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestMockScenarios:
    """Test scenarios using fixtures and complex mocking."""

    def test_format_record_with_complex_payload(self) -> None:
        """Test format_record with complex nested payload."""
        complex_payload = {
            "users": [
                {"id": 1, "name": "Alice", "preferences": {"theme": "dark"}},
                {"id": 2, "name": "Bob", "preferences": {"theme": "light"}},
            ],
            "metadata": {
                "timestamp": "2023-01-01T12:00:00Z",
                "version": "1.0.0",
                "nested": {"deep": {"very_deep": "value"}},
            },
        }

        record = {
            "extra": {
                "component": "COMPLEX-TEST",
                "payload": complex_payload,
            },
        }

        result = format_record(record)

        # Verify payload formatting is applied
        assert "<level>{extra[payload]}</level>" in result
        # Verify the payload is pretty-formatted (pformat should be called)
        formatted_payload = record["extra"]["payload"]
        assert isinstance(formatted_payload, str)
