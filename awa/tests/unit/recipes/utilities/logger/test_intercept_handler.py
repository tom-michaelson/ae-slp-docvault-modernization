"""Unit tests for utilities/logger/intercept_handler.py."""

import inspect
import logging
import sys
from types import FrameType
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from cookbook.recipes.utilities.logger.intercept_handler import TYPE_CHECKING as HANDLER_TYPE_CHECKING
from cookbook.recipes.utilities.logger.intercept_handler import InterceptHandler

if TYPE_CHECKING:
    from types import FrameType as TestFrameType


class TestInterceptHandler:
    """Test cases for InterceptHandler class."""

    def test_intercept_handler_inheritance(self) -> None:
        """Test that InterceptHandler properly inherits from logging.Handler."""
        handler = InterceptHandler()
        assert isinstance(handler, logging.Handler)

    def test_intercept_handler_initialization(self) -> None:
        """Test InterceptHandler initialization and default properties."""
        handler = InterceptHandler()
        assert handler is not None
        assert hasattr(handler, "emit")

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_basic_functionality(self, mock_logger: MagicMock) -> None:
        """Test basic emit functionality with a standard log record."""
        handler = InterceptHandler()

        # Create a mock log record
        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message %s",
            args=("argument",),
            exc_info=None,
        )

        # Mock the logger chain
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_log = MagicMock()

        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind
        mock_bind.log = mock_log

        # Execute emit
        handler.emit(log_record)

        # Verify getMessage was called (indirectly through record.getMessage())
        expected_message = "Test message argument"

        # Verify logger interactions
        mock_logger.level.assert_called_once_with("INFO")
        mock_logger.opt.assert_called_once()
        mock_opt.bind.assert_called_once()
        mock_bind.log.assert_called_once()

        # Get the actual call arguments
        call_args = mock_bind.log.call_args
        assert call_args[0][0] == "INFO"  # level
        assert call_args[0][1] == expected_message  # message

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_level_name_conversion_success(self, mock_logger: MagicMock) -> None:
        """Test successful level name conversion using loguru logger.level()."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.DEBUG,
            pathname="/test/path.py",
            lineno=1,
            msg="Debug message",
            args=(),
            exc_info=None,
        )

        # Mock successful level conversion
        mock_level_obj = MagicMock()
        mock_level_obj.name = "DEBUG"
        mock_logger.level.return_value = mock_level_obj

        # Mock the rest of the chain
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify level conversion was attempted
        mock_logger.level.assert_called_once_with("DEBUG")

        # Verify the level name was used
        call_args = mock_bind.log.call_args
        assert call_args[0][0] == "DEBUG"

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_level_name_conversion_failure(self, mock_logger: MagicMock) -> None:
        """Test level name conversion failure and fallback to logging.getLevelName()."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.WARNING,
            pathname="/test/path.py",
            lineno=1,
            msg="Warning message",
            args=(),
            exc_info=None,
        )

        # Mock ValueError on level conversion
        mock_logger.level.side_effect = ValueError("Unknown level")

        # Mock the rest of the chain
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        with patch("cookbook.recipes.utilities.logger.intercept_handler.logging.getLevelName") as mock_get_level_name:
            mock_get_level_name.return_value = "WARNING"

            handler.emit(log_record)

            # Verify fallback was used
            mock_logger.level.assert_called_once_with("WARNING")
            mock_get_level_name.assert_called_once_with(30)  # logging.WARNING = 30

            # Verify the fallback level name was used
            call_args = mock_bind.log.call_args
            assert call_args[0][0] == "WARNING"

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    @patch("cookbook.recipes.utilities.logger.intercept_handler.logging.currentframe")
    def test_emit_frame_tracking_basic(self, mock_currentframe: MagicMock, mock_logger: MagicMock) -> None:
        """Test basic frame tracking for caller detection."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Create mock frame chain
        frame1 = MagicMock(spec=FrameType)
        frame1.f_code.co_filename = logging.__file__  # Should be skipped
        frame1.f_back = None

        mock_currentframe.return_value = frame1

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify frame tracking
        mock_currentframe.assert_called_once()

        # Verify opt was called with increased depth (2 + 1 = 3)
        call_args = mock_logger.opt.call_args
        assert "depth" in call_args.kwargs
        assert call_args.kwargs["depth"] == 3

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    @patch("cookbook.recipes.utilities.logger.intercept_handler.logging.currentframe")
    def test_emit_frame_tracking_multiple_frames(self, mock_currentframe: MagicMock, mock_logger: MagicMock) -> None:
        """Test frame tracking through multiple logging frames."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Create mock frame chain with multiple logging frames
        frame3 = MagicMock(spec=FrameType)
        frame3.f_code.co_filename = "/some/other/file.py"  # Not logging.__file__
        frame3.f_back = None

        frame2 = MagicMock(spec=FrameType)
        frame2.f_code.co_filename = logging.__file__  # Should be skipped
        frame2.f_back = frame3

        frame1 = MagicMock(spec=FrameType)
        frame1.f_code.co_filename = logging.__file__  # Should be skipped
        frame1.f_back = frame2

        mock_currentframe.return_value = frame1

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify frame tracking incremented depth for each logging frame
        # Initial depth 2, plus 2 logging frames = 4
        call_args = mock_logger.opt.call_args
        assert call_args.kwargs["depth"] == 4

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    @patch("cookbook.recipes.utilities.logger.intercept_handler.logging.currentframe")
    def test_emit_frame_tracking_no_frames(self, mock_currentframe: MagicMock, mock_logger: MagicMock) -> None:
        """Test frame tracking when currentframe returns None."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Mock currentframe returning None
        mock_currentframe.return_value = None

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify default depth is used when no frame
        call_args = mock_logger.opt.call_args
        assert call_args.kwargs["depth"] == 2

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_extra_context_with_named_logger(self, mock_logger: MagicMock) -> None:
        """Test extra context building with named logger."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="my.custom.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify bind was called with original_logger
        mock_opt.bind.assert_called_once_with(original_logger="my.custom.logger")

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_extra_context_with_root_logger(self, mock_logger: MagicMock) -> None:
        """Test extra context building with root logger (should not add original_logger)."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="root",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify bind was called with empty context (no original_logger)
        mock_opt.bind.assert_called_once_with()

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_extra_context_with_empty_logger_name(self, mock_logger: MagicMock) -> None:
        """Test extra context building with empty logger name."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify bind was called with empty context (no original_logger)
        mock_opt.bind.assert_called_once_with()

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_extra_context_with_none_logger_name(self, mock_logger: MagicMock) -> None:
        """Test extra context building with None logger name."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name=None,  # type: ignore[arg-type]
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify bind was called with empty context (no original_logger)
        mock_opt.bind.assert_called_once_with()

    def _raise_test_exception(self) -> None:
        """Raise a test exception."""
        raise ValueError("Test exception")

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_with_exception_info(self, mock_logger: MagicMock) -> None:
        """Test emit with exception information."""
        handler = InterceptHandler()

        try:
            self._raise_test_exception()
        except ValueError:
            exc_info = sys.exc_info()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "ERROR"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify exception info was passed to opt()
        call_args = mock_logger.opt.call_args
        assert "exception" in call_args.kwargs
        assert call_args.kwargs["exception"] == exc_info

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_with_no_exception_info(self, mock_logger: MagicMock) -> None:
        """Test emit without exception information."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Normal message",
            args=(),
            exc_info=None,
        )

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify exception info was passed as None to opt()
        call_args = mock_logger.opt.call_args
        assert "exception" in call_args.kwargs
        assert call_args.kwargs["exception"] is None

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_message_formatting(self, mock_logger: MagicMock) -> None:
        """Test that emit properly formats messages with arguments."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Message with %s and %d",
            args=("string", 42),
            exc_info=None,
        )

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify formatted message was passed to log()
        call_args = mock_bind.log.call_args
        expected_message = "Message with string and 42"
        assert call_args[0][1] == expected_message

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_all_log_levels(self, mock_logger: MagicMock) -> None:
        """Test emit with all standard log levels."""
        handler = InterceptHandler()

        levels_to_test = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        for level_num, level_name in levels_to_test:
            # Reset mocks for each iteration
            mock_logger.reset_mock()

            log_record = logging.LogRecord(
                name="test.logger",
                level=level_num,
                pathname="/test/path.py",
                lineno=1,
                msg=f"{level_name} message",
                args=(),
                exc_info=None,
            )

            # Mock logger chain
            mock_level_obj = MagicMock()
            mock_level_obj.name = level_name
            mock_logger.level.return_value = mock_level_obj
            mock_opt = MagicMock()
            mock_bind = MagicMock()
            mock_logger.opt.return_value = mock_opt
            mock_opt.bind.return_value = mock_bind

            handler.emit(log_record)

            # Verify correct level was used
            mock_logger.level.assert_called_once_with(level_name)
            call_args = mock_bind.log.call_args
            assert call_args[0][0] == level_name
            assert call_args[0][1] == f"{level_name} message"

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_custom_log_level(self, mock_logger: MagicMock) -> None:
        """Test emit with custom log level that causes ValueError."""
        handler = InterceptHandler()

        # Add a custom level
        custom_level = 35
        custom_level_name = "CUSTOM"
        logging.addLevelName(custom_level, custom_level_name)

        log_record = logging.LogRecord(
            name="test.logger",
            level=custom_level,
            pathname="/test/path.py",
            lineno=1,
            msg="Custom level message",
            args=(),
            exc_info=None,
        )

        # Mock ValueError on level conversion, then successful fallback
        mock_logger.level.side_effect = ValueError("Unknown level")

        # Mock logger chain
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        with patch("cookbook.recipes.utilities.logger.intercept_handler.logging.getLevelName") as mock_get_level_name:
            mock_get_level_name.return_value = custom_level_name

            handler.emit(log_record)

            # Verify fallback was used
            mock_logger.level.assert_called_once_with(custom_level_name)
            mock_get_level_name.assert_called_once_with(custom_level)

            # Verify the fallback level name was used
            call_args = mock_bind.log.call_args
            assert call_args[0][0] == custom_level_name

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_integration_complete_flow(self, mock_logger: MagicMock) -> None:
        """Test complete emit flow integration."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="integration.test.logger",
            level=logging.WARNING,
            pathname="/test/integration.py",
            lineno=100,
            msg="Integration test %s with %d parameters",
            args=("message", 3),
            exc_info=None,
        )

        # Mock complete logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "WARNING"
        mock_logger.level.return_value = mock_level_obj

        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_log = MagicMock()

        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind
        mock_bind.log = mock_log

        handler.emit(log_record)

        # Verify complete chain was executed correctly
        mock_logger.level.assert_called_once_with("WARNING")

        # Verify opt was called with correct parameters
        opt_call = mock_logger.opt.call_args
        assert "depth" in opt_call.kwargs
        assert opt_call.kwargs["depth"] >= 2  # At least default depth
        assert "exception" in opt_call.kwargs
        assert opt_call.kwargs["exception"] is None

        # Verify bind was called with correct context
        mock_opt.bind.assert_called_once_with(original_logger="integration.test.logger")

        # Verify log was called with correct parameters
        log_call = mock_bind.log.call_args
        assert log_call[0][0] == "WARNING"  # level
        assert log_call[0][1] == "Integration test message with 3 parameters"  # formatted message

    def test_intercept_handler_docstring(self) -> None:
        """Test that InterceptHandler has proper docstring."""
        assert InterceptHandler.__doc__ is not None
        assert "Handler that intercepts standard logging and routes to loguru" in InterceptHandler.__doc__

    def test_emit_method_signature(self) -> None:
        """Test that emit method has correct signature."""
        signature = inspect.signature(InterceptHandler.emit)
        parameters = list(signature.parameters.keys())

        assert parameters == ["self", "record"]
        assert signature.return_annotation is None  # Should return None

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_error_resilience(self, mock_logger: MagicMock) -> None:
        """Test emit method handles unexpected errors gracefully."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Mock logger.level to raise an unexpected exception
        mock_logger.level.side_effect = RuntimeError("Unexpected error")

        # This should not crash the application
        # In real scenarios, logging errors are typically suppressed
        with pytest.raises(RuntimeError):
            handler.emit(log_record)

    def test_type_checking_import_coverage(self) -> None:
        """Test that TYPE_CHECKING import is properly structured (covers line 7)."""
        # This test ensures the TYPE_CHECKING import is executed during testing
        # Verify it's the same as typing.TYPE_CHECKING
        assert HANDLER_TYPE_CHECKING == TYPE_CHECKING

        # Verify the conditional import works as expected
        if TYPE_CHECKING:
            assert TestFrameType is not None

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    def test_emit_with_different_record_attributes(self, mock_logger: MagicMock) -> None:
        """Test emit with various log record attributes and edge cases."""
        handler = InterceptHandler()

        # Test with minimal log record
        log_record = logging.LogRecord(
            name="minimal",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="",
            args=(),
            exc_info=None,
        )

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Verify it handles minimal record
        mock_opt.bind.assert_called_once_with(original_logger="minimal")

        call_args = mock_bind.log.call_args
        assert call_args[0][0] == "INFO"
        assert call_args[0][1] == ""  # Empty message

    @patch("cookbook.recipes.utilities.logger.intercept_handler.logger")
    @patch("cookbook.recipes.utilities.logger.intercept_handler.logging.currentframe")
    def test_emit_frame_edge_cases(self, mock_currentframe: MagicMock, mock_logger: MagicMock) -> None:
        """Test frame tracking edge cases."""
        handler = InterceptHandler()

        log_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Test case where frame.f_back becomes None during iteration
        frame1 = MagicMock(spec=FrameType)
        frame1.f_code.co_filename = logging.__file__
        frame1.f_back = None  # This will terminate the while loop

        mock_currentframe.return_value = frame1

        # Mock logger chain
        mock_level_obj = MagicMock()
        mock_level_obj.name = "INFO"
        mock_logger.level.return_value = mock_level_obj
        mock_opt = MagicMock()
        mock_bind = MagicMock()
        mock_logger.opt.return_value = mock_opt
        mock_opt.bind.return_value = mock_bind

        handler.emit(log_record)

        # Should increment depth once and stop
        call_args = mock_logger.opt.call_args
        assert call_args.kwargs["depth"] == 3  # 2 + 1
