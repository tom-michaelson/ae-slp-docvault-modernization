import re
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from awa.core.logger.logger import LoggerComponent, format_record


# We need to import the real logger module directly, bypassing the global patches
# This is done by temporarily removing the module from sys.modules and reimporting
def get_real_logger_module() -> Any:  # noqa: ANN401
    """Get the real logger module by temporarily bypassing global patches."""
    import sys

    # Temporarily remove the module from cache if it exists
    if "awa.core.logger.logger" in sys.modules:
        del sys.modules["awa.core.logger.logger"]

    # Import the real module
    import awa.core.logger.logger as real_logger_module

    return real_logger_module


_real_logger_module = get_real_logger_module()
_real_init_logging = _real_logger_module.init_logging


class TestFormatRecord:
    """Test cases for format_record function."""

    def test_format_record_basic(self) -> None:
        """Test format_record with basic record."""
        record = {
            "extra": {"component": "AWA"},
            "time": "2023-01-01T12:00:00.000Z",
            "level": {"name": "INFO"},
            "message": "Test message",
        }

        result = format_record(record)

        # Should include component-based format with new color scheme
        assert "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>" in result
        assert "<level>{level: <8}</level>" in result  # Uses level tag
        assert "<cyan>AWA" in result
        assert "<level>{message}</level>" in result  # Uses level tag for message
        assert "{exception}\n" in result

    def test_format_record_with_component(self) -> None:
        """Test format_record with component in extra."""
        record = {
            "extra": {"component": LoggerComponent.API},
            "time": "2023-01-01T12:00:00.000Z",
            "level": {"name": "INFO"},
            "message": "Test message",
        }

        result = format_record(record)

        # Should include component-based format with new color scheme
        assert "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>" in result
        assert "<level>{level: <8}</level>" in result  # Uses level tag
        assert "<cyan>AWA-API" in result
        assert "<level>{message}</level>" in result  # Uses level tag for message
        assert "{exception}\n" in result

    def test_format_record_with_workflow_id(self) -> None:
        """Test format_record with workflow_id in extra."""
        record = {
            "extra": {"component": "AWA-WORKER", "workflow_id": "test-workflow-123"},
            "time": "2023-01-01T12:00:00.000Z",
            "level": {"name": "DEBUG"},
            "message": "Test message",
        }

        result = format_record(record)

        # Should include workflow ID in format with new color scheme
        assert "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>" in result
        assert "<level>{level: <8}</level>" in result  # Uses level tag
        assert "<cyan>AWA-WORKER" in result
        assert "<yellow>test-workflow-123</yellow>" in result  # Workflow ID now yellow
        assert "<level>{message}</level>" in result  # Uses level tag for message
        assert "{exception}\n" in result

    def test_format_record_with_payload(self) -> None:
        """Test format_record with payload in extra."""
        test_payload = {"users": [{"name": "John", "age": 30}], "count": 1}
        record = {
            "extra": {"component": LoggerComponent.CLI, "payload": test_payload},
            "time": "2023-01-01T12:00:00.000Z",
            "level": {"name": "DEBUG"},
            "message": "Test message",
        }

        result = format_record(record)

        # Should format payload with pformat and include in format string with new color scheme
        assert "<level>{extra[payload]}</level>" in result  # Uses level tag for payload
        assert "{exception}\n" in result
        # Payload should be formatted nicely
        assert "users" in str(record["extra"]["payload"])


class TestInitLogging:
    """Test cases for init_logging function."""

    def teardown_method(self) -> None:
        """Clean up after each test to prevent InterceptHandler from persisting."""
        import logging

        from loguru import logger

        # Remove all loguru handlers
        logger.remove()

        # Clear all logging handlers to remove any InterceptHandlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Reset logging level
        root_logger.setLevel(logging.WARNING)

    @patch("awa.core.logger.logger.Path")
    @patch("awa.core.logger.logger.logger")
    @patch("awa.core.logger.logger.logging.getLogger")
    @patch("awa.core.logger.logger.InterceptHandler")
    @patch("awa.core.logger.logger.EnvConfig.get_env_config")
    def test_init_logging_default(
        self,
        mock_get_env_config: Mock,
        mock_intercept_handler_class: Mock,
        mock_get_logger: Mock,
        mock_logger: Mock,
        mock_path_class: Mock,
    ) -> None:
        """Test init_logging with default parameters."""
        # Setup
        mock_get_env_config().log_path = "/logs"
        mock_get_env_config().log_workflow_dir = "/logs/workflows"
        mock_get_env_config().log_level = "INFO"
        mock_get_env_config().log_console_enabled = True
        mock_get_env_config().log_file_enabled = True
        mock_get_env_config().log_enable_json = False
        mock_get_env_config().log_file_rotation_size = "1 MB"

        mock_path = Mock()
        mock_path_class.return_value = mock_path
        mock_path.mkdir = Mock()
        mock_path.__truediv__ = Mock(return_value=mock_path)

        # Mock root logger
        mock_root_logger = Mock()
        mock_root_logger.handlers = []

        # Mock specific loggers
        mock_temporal_workflow_logger = Mock()
        mock_temporal_workflow_logger.handlers = []
        mock_temporal_activity_logger = Mock()
        mock_temporal_activity_logger.handlers = []
        mock_temporal_logger = Mock()
        mock_temporal_logger.handlers = []

        def mock_logger_side_effect(name: str = "") -> Mock:
            if name == "":
                return mock_root_logger
            if name == "temporalio.workflow":
                return mock_temporal_workflow_logger
            if name == "temporalio.activity":
                return mock_temporal_activity_logger
            if name == "temporalio":
                return mock_temporal_logger
            return Mock()

        mock_get_logger.side_effect = mock_logger_side_effect

        mock_intercept_handler = Mock()
        mock_intercept_handler_class.return_value = mock_intercept_handler

        # Act - Use the real init_logging function directly
        _real_init_logging()

        # Assert
        mock_path.mkdir.assert_called()
        mock_logger.remove.assert_called_once()
        mock_logger.configure.assert_called_once()

        # Check that temporal loggers were configured
        assert mock_temporal_workflow_logger.propagate is False
        assert mock_temporal_activity_logger.propagate is False
        assert mock_temporal_logger.propagate is False


class TestLogFileRegression:
    """Regression tests for log file creation and format."""

    def teardown_method(self) -> None:
        """Clean up after each test to prevent InterceptHandler from persisting."""
        import logging

        from loguru import logger

        # Remove all loguru handlers
        logger.remove()

        # Clear all logging handlers to remove any InterceptHandlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Reset logging level
        root_logger.setLevel(logging.WARNING)

    @pytest.fixture
    def patched_env_config(self, tmp_path: Path) -> Generator[Path, None, None]:
        """Patch EnvConfig.get_env_config() to use a temp log dir and enable file logging."""
        from awa.core.models.config.env_config import EnvConfig

        mock_env = Mock()
        mock_env.log_path = str(tmp_path)
        mock_env.log_workflow_dir = str(tmp_path / "workflows")
        mock_env.log_level = "INFO"
        mock_env.log_console_enabled = False
        mock_env.log_file_enabled = True
        mock_env.log_enable_json = False
        mock_env.log_file_rotation_size = "1 MB"
        with patch.object(EnvConfig, "get_env_config", return_value=mock_env):
            yield tmp_path

    def test_app_log_created_and_not_empty(self, patched_env_config: Path) -> None:
        """Test that app.log is created and not empty after logging."""
        # Arrange
        _real_init_logging()
        logger = _real_logger_module.get_logger(_real_logger_module.LoggerComponent.API)
        logger.info("Test log line for file creation")

        log_path = Path(patched_env_config) / "app.log"
        assert log_path.exists(), "app.log should be created after logging."
        content = log_path.read_text().strip()
        assert content, "app.log should not be empty after logging."

    def test_app_log_line_format(self, patched_env_config: Path) -> None:
        """Test that app.log lines match the expected format."""
        # Arrange
        _real_init_logging()
        logger = _real_logger_module.get_logger(_real_logger_module.LoggerComponent.CLI)
        logger.info("Test log format line")

        log_path = Path(patched_env_config) / "app.log"
        assert log_path.exists(), "app.log should be created."
        content = log_path.read_text().strip()
        assert content, "app.log should not be empty."

        # Example expected format: 2023-01-01 12:00:00.000 | INFO     | AWA-CLI     | Test log format line
        # We'll use a regex to check for the timestamp, level, component, and message
        log_line_regex = re.compile(
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| INFO\s+\| AWA-CLI\s+\| Test log format line",
        )
        # Remove color codes if present
        clean_content = re.sub(r"\x1b\[[0-9;]*m", "", content)
        assert any(log_line_regex.search(line) for line in clean_content.splitlines()), "Log line format is incorrect."
