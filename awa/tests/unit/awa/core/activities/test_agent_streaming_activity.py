"""Unit tests for agent streaming activities."""

from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.agent_streaming_activity import (
    emit_stream_message_activity,
    emit_stream_step_activity,
)


class TestEmitStreamMessageActivity:
    """Test cases for emit_stream_message_activity."""

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_message_with_data(self, mock_emit: AsyncMock) -> None:
        """Test emitting a message with data."""
        mock_emit.return_value = None

        await emit_stream_message_activity(
            session_id="test-session-123",
            message="Test message",
            data={"key": "value"},
        )

        mock_emit.assert_called_once_with(
            session_id="test-session-123",
            event_type="message",
            event_data={
                "message": "Test message",
                "data": {"key": "value"},
            },
        )

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_message_without_data(self, mock_emit: AsyncMock) -> None:
        """Test emitting a message without data (None)."""
        mock_emit.return_value = None

        await emit_stream_message_activity(
            session_id="test-session-456",
            message="Simple message",
            data=None,
        )

        mock_emit.assert_called_once_with(
            session_id="test-session-456",
            event_type="message",
            event_data={
                "message": "Simple message",
                "data": {},
            },
        )

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_message_default_data(self, mock_emit: AsyncMock) -> None:
        """Test emitting a message with default data parameter."""
        mock_emit.return_value = None

        await emit_stream_message_activity(
            session_id="test-session-789",
            message="Message with defaults",
        )

        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert call_args.kwargs["event_data"]["data"] == {}

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_message_handles_error_gracefully(self, mock_emit: AsyncMock) -> None:
        """Test that errors during emission don't raise exceptions."""
        mock_emit.side_effect = Exception("Network error")

        # Should not raise - errors are caught and logged
        await emit_stream_message_activity(
            session_id="test-session-error",
            message="Error test",
            data={"test": "data"},
        )

        mock_emit.assert_called_once()

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_message_with_complex_data(self, mock_emit: AsyncMock) -> None:
        """Test emitting a message with complex nested data."""
        mock_emit.return_value = None

        complex_data = {
            "nested": {
                "level1": {
                    "level2": "value",
                },
            },
            "list": [1, 2, 3],
            "mixed": {"a": [1, 2], "b": {"c": 3}},
        }

        await emit_stream_message_activity(
            session_id="test-session-complex",
            message="Complex data message",
            data=complex_data,
        )

        mock_emit.assert_called_once_with(
            session_id="test-session-complex",
            event_type="message",
            event_data={
                "message": "Complex data message",
                "data": complex_data,
            },
        )


class TestEmitStreamStepActivity:
    """Test cases for emit_stream_step_activity."""

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_step_start(self, mock_emit: AsyncMock) -> None:
        """Test emitting a step start event."""
        mock_emit.return_value = None

        await emit_stream_step_activity(
            session_id="test-session-123",
            step_name="initialization",
            step_type="start",
            description="Starting initialization",
            result=None,
            metadata={"priority": "high"},
        )

        mock_emit.assert_called_once_with(
            session_id="test-session-123",
            event_type="step",
            event_data={
                "type": "step_start",
                "step_name": "initialization",
                "description": "Starting initialization",
                "result": None,
                "metadata": {"priority": "high"},
            },
        )

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_step_complete(self, mock_emit: AsyncMock) -> None:
        """Test emitting a step complete event."""
        mock_emit.return_value = None

        await emit_stream_step_activity(
            session_id="test-session-456",
            step_name="processing",
            step_type="complete",
            description=None,
            result="Successfully processed 10 items",
            metadata=None,
        )

        mock_emit.assert_called_once_with(
            session_id="test-session-456",
            event_type="step",
            event_data={
                "type": "step_complete",
                "step_name": "processing",
                "description": None,
                "result": "Successfully processed 10 items",
                "metadata": {},
            },
        )

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_step_error(self, mock_emit: AsyncMock) -> None:
        """Test emitting a step error event."""
        mock_emit.return_value = None

        await emit_stream_step_activity(
            session_id="test-session-error",
            step_name="validation",
            step_type="error",
            description="Validating input",
            result="Validation failed: missing required field",
            metadata={"error_code": "VALIDATION_ERROR"},
        )

        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert call_args.kwargs["event_data"]["type"] == "step_error"
        assert call_args.kwargs["event_data"]["result"] == "Validation failed: missing required field"

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_step_with_all_fields(self, mock_emit: AsyncMock) -> None:
        """Test emitting a step event with all fields populated."""
        mock_emit.return_value = None

        await emit_stream_step_activity(
            session_id="test-session-full",
            step_name="deployment",
            step_type="complete",
            description="Deploying application",
            result="Deployed to production",
            metadata={
                "version": "1.2.3",
                "environment": "production",
                "timestamp": "2024-01-15T10:00:00Z",
            },
        )

        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        event_data = call_args.kwargs["event_data"]

        assert event_data["type"] == "step_complete"
        assert event_data["step_name"] == "deployment"
        assert event_data["description"] == "Deploying application"
        assert event_data["result"] == "Deployed to production"
        assert event_data["metadata"]["version"] == "1.2.3"

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_step_with_minimal_fields(self, mock_emit: AsyncMock) -> None:
        """Test emitting a step event with minimal fields."""
        mock_emit.return_value = None

        await emit_stream_step_activity(
            session_id="test-session-minimal",
            step_name="cleanup",
            step_type="start",
        )

        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        event_data = call_args.kwargs["event_data"]

        assert event_data["type"] == "step_start"
        assert event_data["step_name"] == "cleanup"
        assert event_data["description"] is None
        assert event_data["result"] is None
        assert event_data["metadata"] == {}

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_step_handles_error_gracefully(self, mock_emit: AsyncMock) -> None:
        """Test that errors during step emission don't raise exceptions."""
        mock_emit.side_effect = RuntimeError("Connection failed")

        # Should not raise - errors are caught and logged
        await emit_stream_step_activity(
            session_id="test-session-fail",
            step_name="failing_step",
            step_type="start",
            description="This will fail",
        )

        mock_emit.assert_called_once()

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_step_event_type_formatting(self, mock_emit: AsyncMock) -> None:
        """Test that step_type is correctly formatted as 'step_{type}'."""
        mock_emit.return_value = None

        step_types = ["start", "complete", "error"]

        for step_type in step_types:
            await emit_stream_step_activity(
                session_id=f"test-session-{step_type}",
                step_name="test_step",
                step_type=step_type,
            )

        # Verify all calls
        assert mock_emit.call_count == 3

        for i, step_type in enumerate(step_types):
            call_args = mock_emit.call_args_list[i]
            assert call_args.kwargs["event_data"]["type"] == f"step_{step_type}"

    @pytest.mark.asyncio
    @patch("awa.core.activities.agent_streaming_activity.emit_streaming_event_via_http")
    async def test_emit_step_with_empty_metadata(self, mock_emit: AsyncMock) -> None:
        """Test emitting a step with explicitly empty metadata."""
        mock_emit.return_value = None

        await emit_stream_step_activity(
            session_id="test-session-empty-meta",
            step_name="step_with_empty_meta",
            step_type="complete",
            metadata={},
        )

        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert call_args.kwargs["event_data"]["metadata"] == {}
