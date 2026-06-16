"""Unit tests for agent streaming API endpoints."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from awa.core.api.routes.shared.agent_streaming import (
    StreamEventRequest,
    StreamEventResponse,
    emit_stream_event,
    get_workflow_agent_sessions,
)
from awa.core.models.api import AgentSessionType


class TestStreamEventRequest:
    """Test cases for StreamEventRequest Pydantic model."""

    def test_valid_request_with_all_fields(self) -> None:
        """Test valid request with all fields provided."""
        request = StreamEventRequest(
            session_id="test-session-123",
            event_type="message",
            event_data={"content": "Test message"},
            timestamp="2024-01-15T10:30:00Z",
        )

        assert request.session_id == "test-session-123"
        assert request.event_type == "message"
        assert request.event_data == {"content": "Test message"}
        assert request.timestamp == "2024-01-15T10:30:00Z"

    def test_valid_request_without_timestamp(self) -> None:
        """Test valid request without timestamp (optional field)."""
        request = StreamEventRequest(
            session_id="test-session-456",
            event_type="step",
            event_data={"step_name": "initialization"},
        )

        assert request.session_id == "test-session-456"
        assert request.event_type == "step"
        assert request.event_data == {"step_name": "initialization"}
        assert request.timestamp is None

    def test_empty_event_data(self) -> None:
        """Test request with empty event data dictionary."""
        request = StreamEventRequest(
            session_id="test-session-789",
            event_type="start",
            event_data={},
        )

        assert request.session_id == "test-session-789"
        assert request.event_type == "start"
        assert request.event_data == {}


class TestStreamEventResponse:
    """Test cases for StreamEventResponse Pydantic model."""

    def test_valid_response_with_all_fields(self) -> None:
        """Test valid response with all fields."""
        response = StreamEventResponse(
            success=True,
            message="Event emitted successfully",
            event_count=5,
        )

        assert response.success is True
        assert response.message == "Event emitted successfully"
        assert response.event_count == 5

    def test_valid_response_without_event_count(self) -> None:
        """Test valid response without optional event_count."""
        response = StreamEventResponse(
            success=False,
            message="Event emission failed",
        )

        assert response.success is False
        assert response.message == "Event emission failed"
        assert response.event_count is None


class TestEmitStreamEvent:
    """Test cases for emit_stream_event endpoint."""

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_message_event(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test emitting a message event."""
        session_events = []
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-123",
            event_type="message",
            event_data={"content": "Hello world"},
            timestamp="2024-01-15T10:30:00+00:00",
        )

        auth = {"service": "temporal"}
        result = await emit_stream_event(request, auth)

        assert result.success is True
        assert "session-123" in result.message
        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        assert call_args.args[0] == "agent_stream_message"
        assert call_args.kwargs["room"] == "agent-stream-session-123"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_step_event(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test emitting a step event."""
        session_events = []
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-456",
            event_type="step",
            event_data={"step_name": "processing", "step_number": 2},
        )

        auth = {"service": "temporal"}
        result = await emit_stream_event(request, auth)

        assert result.success is True
        call_args = mock_sio.emit.call_args
        assert call_args.args[0] == "agent_stream_step"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_start_event(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test emitting a start event."""
        session_events = []
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-789",
            event_type="start",
            event_data={"agent_type": "claude"},
        )

        auth = {"service": "temporal"}
        result = await emit_stream_event(request, auth)

        assert result.success is True
        call_args = mock_sio.emit.call_args
        assert call_args.args[0] == "agent_stream_start"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_complete_event(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test emitting a complete event."""
        session_events = []
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-complete",
            event_type="complete",
            event_data={"status": "success"},
        )

        auth = {"service": "temporal"}
        result = await emit_stream_event(request, auth)

        assert result.success is True
        call_args = mock_sio.emit.call_args
        assert call_args.args[0] == "agent_stream_complete"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_error_event(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test emitting an error event."""
        session_events = []
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-error",
            event_type="error",
            event_data={"error_message": "Something went wrong"},
        )

        auth = {"service": "temporal"}
        result = await emit_stream_event(request, auth)

        assert result.success is True
        call_args = mock_sio.emit.call_args
        assert call_args.args[0] == "agent_stream_error"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_output_event(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test emitting an output event."""
        session_events = []
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-output",
            event_type="output",
            event_data={"output": "Final result"},
        )

        auth = {"service": "temporal"}
        result = await emit_stream_event(request, auth)

        assert result.success is True
        call_args = mock_sio.emit.call_args
        assert call_args.args[0] == "agent_stream_output"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_unknown_event_type_defaults_to_message(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test that unknown event types default to agent_stream_message."""
        session_events = []
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-unknown",
            event_type="unknown_type",
            event_data={"data": "test"},
        )

        auth = {"service": "temporal"}
        result = await emit_stream_event(request, auth)

        assert result.success is True
        call_args = mock_sio.emit.call_args
        assert call_args.args[0] == "agent_stream_message"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_event_without_timestamp_uses_current_time(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test that events without timestamp use current time."""
        session_events = []
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-notimestamp",
            event_type="message",
            event_data={"content": "No timestamp"},
            timestamp=None,
        )

        auth = {"service": "temporal"}
        result = await emit_stream_event(request, auth)

        assert result.success is True
        # Verify timestamp was added to payload
        call_args = mock_sio.emit.call_args
        event_payload = call_args.args[1]
        assert "timestamp" in event_payload
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(event_payload["timestamp"])

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_event_stores_in_session_storage(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test that events are stored in agent_session_storage."""
        session_events = []
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-storage",
            event_type="message",
            event_data={"content": "Stored event"},
        )

        auth = {"service": "temporal"}
        await emit_stream_event(request, auth)

        # Verify storage was accessed
        mock_storage.__getitem__.assert_called_with("session-storage")

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_event_returns_event_count(
        self,
        mock_storage: MagicMock,
        mock_sio: AsyncMock,
    ) -> None:
        """Test that emit_stream_event returns the current event count."""
        session_events = [{"type": "start"}, {"type": "message"}]
        mock_storage.__getitem__ = MagicMock(return_value=session_events)
        mock_sio.emit = AsyncMock()

        request = StreamEventRequest(
            session_id="session-count",
            event_type="message",
            event_data={"content": "Event 3"},
        )

        auth = {"service": "temporal"}
        result = await emit_stream_event(request, auth)

        assert result.event_count == 3  # Count after append

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    async def test_emit_event_handles_socketio_error(
        self,
        mock_storage: MagicMock,
        mock_sio: MagicMock,
    ) -> None:
        """Test that socket.io errors are handled gracefully."""
        mock_storage.__getitem__ = MagicMock(return_value=[])
        # Make sio.emit raise an exception
        mock_sio.emit = AsyncMock(side_effect=Exception("Socket.IO connection failed"))

        request = StreamEventRequest(
            session_id="session-error",
            event_type="message",
            event_data={"content": "Error test"},
        )

        auth = {"service": "temporal"}

        with pytest.raises(HTTPException) as exc_info:
            await emit_stream_event(request, auth)

        assert exc_info.value.status_code == 500
        assert "Failed to emit stream event" in exc_info.value.detail


class TestGetWorkflowAgentSessions:
    """Test cases for get_workflow_agent_sessions endpoint."""

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.TemporalClient")
    async def test_get_sessions_success(self, mock_temporal_client_class: MagicMock) -> None:
        """Test successful retrieval of agent sessions via query-based discovery."""
        from datetime import datetime

        # Mock workflow info for discovered ExecuteAgent workflows
        mock_workflow_info_1 = MagicMock()
        mock_workflow_info_1.id = "TestGenerator-path_to_file-workflow-123"
        mock_workflow_info_1.start_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)

        mock_workflow_info_2 = MagicMock()
        mock_workflow_info_2.id = "TestLinter-another_file-workflow-123"
        mock_workflow_info_2.start_time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=UTC)

        # Mock parent workflow handle
        mock_parent_handle = AsyncMock()
        mock_parent_handle.describe = AsyncMock()

        # Mock ExecuteAgent workflow handles
        mock_agent_handle_1 = AsyncMock()
        mock_agent_handle_1.query = AsyncMock(return_value="workflow-123")

        mock_agent_handle_2 = AsyncMock()
        mock_agent_handle_2.query = AsyncMock(return_value="workflow-123")

        # Mock Temporal client
        mock_client = AsyncMock()

        def get_workflow_handle(workflow_id: str) -> AsyncMock:
            if workflow_id == "workflow-123":
                return mock_parent_handle
            if workflow_id == "TestGenerator-path_to_file-workflow-123":
                return mock_agent_handle_1
            if workflow_id == "TestLinter-another_file-workflow-123":
                return mock_agent_handle_2
            return AsyncMock()

        mock_client.get_workflow_handle = MagicMock(side_effect=get_workflow_handle)

        # Mock list_workflows to return async iterator
        async def mock_list_workflows(query: str) -> AsyncGenerator:  # noqa: ARG001
            yield mock_workflow_info_1
            yield mock_workflow_info_2

        mock_client.list_workflows = mock_list_workflows

        mock_temporal_instance = AsyncMock()
        mock_temporal_instance.ensure_initialized = AsyncMock()
        mock_temporal_instance.get_client = AsyncMock(return_value=mock_client)

        mock_temporal_client_class.create = AsyncMock(return_value=mock_temporal_instance)

        current_user = {"sub": "user-123"}
        result = await get_workflow_agent_sessions("workflow-123", current_user)

        assert result.workflow_id == "workflow-123"
        # When there are 2+ agent sessions, a parent session is also added
        assert result.count == 3
        assert len(result.sessions) == 3

        # Verify agent sessions
        session_1 = result.sessions[0]
        assert session_1.session_id == "TestGenerator-path_to_file-workflow-123"
        assert session_1.session_type == AgentSessionType.AGENT

        session_2 = result.sessions[1]
        assert session_2.session_id == "TestLinter-another_file-workflow-123"
        assert session_2.session_type == AgentSessionType.AGENT

        # Verify parent session was added
        parent_session = result.sessions[2]
        assert parent_session.session_id == "workflow-123"
        assert parent_session.session_type == AgentSessionType.PARENT

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.TemporalClient")
    async def test_get_sessions_workflow_with_no_agents(
        self,
        mock_temporal_client_class: MagicMock,
    ) -> None:
        """Test handling of workflows with no ExecuteAgent child workflows."""
        # Mock parent workflow handle
        mock_parent_handle = AsyncMock()
        mock_parent_handle.describe = AsyncMock()

        mock_client = AsyncMock()
        mock_client.get_workflow_handle = MagicMock(return_value=mock_parent_handle)

        # Mock list_workflows to return empty iterator
        async def mock_list_workflows(query: str) -> AsyncGenerator:  # noqa: ARG001
            return
            yield  # Make it an async generator

        mock_client.list_workflows = mock_list_workflows

        mock_temporal_instance = AsyncMock()
        mock_temporal_instance.ensure_initialized = AsyncMock()
        mock_temporal_instance.get_client = AsyncMock(return_value=mock_client)

        mock_temporal_client_class.create = AsyncMock(return_value=mock_temporal_instance)

        current_user = {"sub": "user-123"}
        result = await get_workflow_agent_sessions("workflow-no-agents", current_user)

        assert result.workflow_id == "workflow-no-agents"
        assert result.count == 0
        assert result.sessions == []

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.TemporalClient")
    async def test_get_sessions_parent_workflow_not_found(
        self,
        mock_temporal_client_class: MagicMock,
    ) -> None:
        """Test handling when parent workflow doesn't exist."""
        mock_parent_handle = AsyncMock()
        mock_parent_handle.describe = AsyncMock(side_effect=Exception("Workflow not found"))

        mock_client = AsyncMock()
        mock_client.get_workflow_handle = MagicMock(return_value=mock_parent_handle)

        mock_temporal_instance = AsyncMock()
        mock_temporal_instance.ensure_initialized = AsyncMock()
        mock_temporal_instance.get_client = AsyncMock(return_value=mock_client)

        mock_temporal_client_class.create = AsyncMock(return_value=mock_temporal_instance)

        current_user = {"sub": "user-123"}

        with pytest.raises(HTTPException) as exc_info:
            await get_workflow_agent_sessions("workflow-not-found", current_user)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.TemporalClient")
    async def test_get_sessions_temporal_client_error(
        self,
        mock_temporal_client_class: MagicMock,
    ) -> None:
        """Test handling of Temporal client errors."""
        mock_temporal_client_class.create = AsyncMock(side_effect=Exception("Connection failed"))

        current_user = {"sub": "user-123"}

        with pytest.raises(HTTPException) as exc_info:
            await get_workflow_agent_sessions("workflow-error", current_user)

        assert exc_info.value.status_code == 500
        assert "Failed to get agent sessions" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.agent_streaming.TemporalClient")
    async def test_get_sessions_with_anonymous_user(
        self,
        mock_temporal_client_class: MagicMock,
    ) -> None:
        """Test getting sessions with anonymous user (None current_user)."""
        # Mock parent workflow handle
        mock_parent_handle = AsyncMock()
        mock_parent_handle.describe = AsyncMock()

        mock_client = AsyncMock()
        mock_client.get_workflow_handle = MagicMock(return_value=mock_parent_handle)

        # Mock list_workflows to return empty iterator
        async def mock_list_workflows(query: str) -> AsyncGenerator:  # noqa: ARG001
            return
            yield  # Make it an async generator

        mock_client.list_workflows = mock_list_workflows

        mock_temporal_instance = AsyncMock()
        mock_temporal_instance.ensure_initialized = AsyncMock()
        mock_temporal_instance.get_client = AsyncMock(return_value=mock_client)

        mock_temporal_client_class.create = AsyncMock(return_value=mock_temporal_instance)

        current_user = None
        result = await get_workflow_agent_sessions("workflow-anon", current_user)

        assert result.workflow_id == "workflow-anon"
        assert result.count == 0
