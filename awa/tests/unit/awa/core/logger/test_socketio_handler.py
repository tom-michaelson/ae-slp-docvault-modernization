"""Tests for SocketIO handler exception message enhancement."""

import json
from unittest.mock import Mock, patch

from awa.core.logger.socketio_handler import SocketIOLogHandler


class TestSocketIOHandlerExceptionEnhancement:
    """Test cases for SocketIO handler exception message enhancement."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Mock the SocketIO client to prevent network calls
        with patch("awa.core.logger.socketio_handler.socketio_client.Client"):
            self.handler = SocketIOLogHandler(server_url="http://localhost:8001", source_name="test")
        # Mock the connection to prevent actual network calls
        self.handler.connected = False
        self.handler._send_log = Mock()
        # Stop the background thread to prevent connection attempts
        self.handler.stop_event.set()

    def test_exception_message_enhancement_basic(self) -> None:
        """Test basic exception message enhancement."""
        # Arrange - Simulate a loguru record with exception (as it would be serialized)
        test_record = {
            "record": {
                "time": "2025-09-19T16:50:00.000Z",
                "level": {"name": "ERROR"},
                "message": "Failed to execute BAML function",
                "extra": {"component": "AWA-ACTIVITY", "workflow_id": "test_workflow_123"},
                "exception": {
                    "type": "ValueError",
                    "value": "Azure OpenAI API key is required when use_entra_auth is False",
                    "traceback": "some_traceback_data",
                },
            },
            "text": "formatted log text",  # This triggers the record extraction logic
        }

        # Act
        self.handler.emit(json.dumps(test_record))

        # Assert
        self.handler._send_log.assert_called_once()
        sent_log = self.handler._send_log.call_args[0][0]

        expected_message = (
            "Failed to execute BAML function: Azure OpenAI API key is required when use_entra_auth is False"
        )
        assert sent_log["message"] == expected_message

    def test_exception_message_enhancement_baml_http_error(self) -> None:
        """Test exception message enhancement with BAML HTTP error."""
        # Arrange - Simulate BAML client HTTP error
        baml_error_msg = (
            'BamlClientHttpError(client_name=AWA_azure-openai, message=Request failed with status code: "400 Bad '
            ' Request. {"error":{"message":"Unsupported parameter: max_tokens","type":"invalid_request_error"}},'
            " status_code=400)"
        )

        test_record = {
            "record": {
                "time": "2025-09-19T16:50:00.000Z",
                "level": {"name": "ERROR"},
                "message": "Failed to execute BAML function",
                "extra": {"component": "AWA-ACTIVITY", "workflow_id": "test_workflow_123"},
                "exception": {
                    "type": "AwaLlmInvalidRequestError",
                    "value": baml_error_msg,
                    "traceback": "some_traceback_data",
                },
            },
            "text": "formatted log text",
        }

        # Act
        self.handler.emit(json.dumps(test_record))

        # Assert
        self.handler._send_log.assert_called_once()
        sent_log = self.handler._send_log.call_args[0][0]

        expected_message = f"Failed to execute BAML function: {baml_error_msg}"
        assert sent_log["message"] == expected_message

    def test_exception_message_no_duplication(self) -> None:
        """Test that exception message is not duplicated if already in base message."""
        # Arrange - Base message already contains the exception details
        test_record = {
            "record": {
                "time": "2025-09-19T16:50:00.000Z",
                "level": {"name": "ERROR"},
                "message": "Failed to execute: API key required",
                "extra": {"component": "AWA-ACTIVITY", "workflow_id": "test_workflow_123"},
                "exception": {"type": "ValueError", "value": "API key required", "traceback": "some_traceback_data"},
            },
            "text": "formatted log text",
        }

        # Act
        self.handler.emit(json.dumps(test_record))

        # Assert
        self.handler._send_log.assert_called_once()
        sent_log = self.handler._send_log.call_args[0][0]

        # Should not append duplicate message
        assert sent_log["message"] == "Failed to execute: API key required"

    def test_exception_message_no_exception(self) -> None:
        """Test that normal logs without exceptions are unchanged."""
        # Arrange - Normal log without exception
        test_record = {
            "record": {
                "time": "2025-09-19T16:50:00.000Z",
                "level": {"name": "INFO"},
                "message": "Normal log message",
                "extra": {"component": "AWA-ACTIVITY", "workflow_id": "test_workflow_123"},
                "exception": None,
            },
            "text": "formatted log text",
        }

        # Act
        self.handler.emit(json.dumps(test_record))

        # Assert
        self.handler._send_log.assert_called_once()
        sent_log = self.handler._send_log.call_args[0][0]

        # Should remain unchanged
        assert sent_log["message"] == "Normal log message"

    def test_exception_message_malformed_exception(self) -> None:
        """Test handling of malformed exception data."""
        # Arrange - Malformed exception data
        test_record = {
            "record": {
                "time": "2025-09-19T16:50:00.000Z",
                "level": {"name": "ERROR"},
                "message": "Failed to execute BAML function",
                "extra": {"component": "AWA-ACTIVITY", "workflow_id": "test_workflow_123"},
                "exception": {
                    "type": "ValueError",
                    "value": None,  # Malformed - value is None
                    "traceback": "some_traceback_data",
                },
            },
            "text": "formatted log text",
        }

        # Act
        self.handler.emit(json.dumps(test_record))

        # Assert - Should not crash and should not append exception message
        self.handler._send_log.assert_called_once()
        sent_log = self.handler._send_log.call_args[0][0]

        assert sent_log["message"] == "Failed to execute BAML function"

    def test_exception_message_empty_value(self) -> None:
        """Test handling of exception with empty value."""
        # Arrange - Exception with empty string value
        test_record = {
            "record": {
                "time": "2025-09-19T16:50:00.000Z",
                "level": {"name": "ERROR"},
                "message": "Failed to execute BAML function",
                "extra": {"component": "AWA-ACTIVITY", "workflow_id": "test_workflow_123"},
                "exception": {
                    "type": "ValueError",
                    "value": "",  # Empty string
                    "traceback": "some_traceback_data",
                },
            },
            "text": "formatted log text",
        }

        # Act
        self.handler.emit(json.dumps(test_record))

        # Assert - Should not append empty exception message
        self.handler._send_log.assert_called_once()
        sent_log = self.handler._send_log.call_args[0][0]

        assert sent_log["message"] == "Failed to execute BAML function"
