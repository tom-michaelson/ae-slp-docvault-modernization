"""Unit tests for HITL data models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from awa.core.models.api import HITLTaskDetail, HITLTaskInfo
from awa.core.models.hitl import HITLChatMessage, HITLContext, HITLInput, HITLOutput, HITLResponse


class TestHITLInput:
    """Test HITLInput model validation and behavior."""

    def test_minimal_input(self) -> None:
        """Test creating HITLInput with minimal required fields."""
        input_data = HITLInput(
            title="Test Task",
            description="Test Description",
            markdown="# Test",
            input_schema={"type": "object"},
        )

        assert input_data.title == "Test Task"
        assert input_data.attachments == []
        assert input_data.timeout_seconds is None
        assert input_data.non_blocking is False
        assert input_data.chat_mode is False

    def test_full_input(self) -> None:
        """Test creating HITLInput with all fields."""
        input_data = HITLInput(
            title="Test Task",
            description="Test Description",
            markdown="# Test",
            input_schema={"type": "object", "properties": {"name": {"type": "string"}}},
            attachments=["file1.txt", "file2.pdf"],
            timeout_seconds=300,
            non_blocking=True,
            chat_mode=True,
        )

        assert len(input_data.attachments) == 2
        assert input_data.timeout_seconds == 300
        assert input_data.non_blocking is True
        assert input_data.chat_mode is True

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            HITLInput(title="Test")  # Missing description, markdown (input_schema is now optional)

        errors = exc_info.value.errors()
        assert len(errors) == 2
        field_names = {e["loc"][0] for e in errors}
        assert field_names == {"description", "markdown"}


class TestHITLResponse:
    """Test HITLResponse model validation and behavior."""

    def test_minimal_response(self) -> None:
        """Test creating HITLResponse with minimal fields."""
        response = HITLResponse(data={"answer": "yes"})

        assert response.data == {"answer": "yes"}
        assert response.message == ""

    def test_chat_response(self) -> None:
        """Test creating HITLResponse for chat mode."""
        response = HITLResponse(
            data={"action": "continue"},
            message="Please continue with the next step",
        )

        assert response.data["action"] == "continue"
        assert response.message == "Please continue with the next step"


class TestHITLOutput:
    """Test HITLOutput model validation and behavior."""

    def test_timeout_output(self) -> None:
        """Test creating HITLOutput for timeout scenario."""
        output = HITLOutput(response=None, timed_out=True)

        assert output.response is None
        assert output.timed_out is True
        assert output.chat_history == []

    def test_success_output(self) -> None:
        """Test creating HITLOutput with successful response."""
        response = HITLResponse(data={"approved": True})
        output = HITLOutput(response=response, timed_out=False)

        assert output.response.data["approved"] is True
        assert output.timed_out is False

    def test_chat_output(self) -> None:
        """Test creating HITLOutput with chat history."""
        chat_msg = HITLChatMessage(
            message="Hello",
            timestamp=datetime.now(UTC),
            is_human=True,
        )
        response = HITLResponse(data={}, message="Hi there")
        output = HITLOutput(
            response=response,
            timed_out=False,
            chat_history=[chat_msg],
        )

        assert len(output.chat_history) == 1
        assert output.chat_history[0].message == "Hello"


class TestHITLChatMessage:
    """Test HITLChatMessage model validation and behavior."""

    def test_human_message(self) -> None:
        """Test creating a human chat message."""
        timestamp = datetime.now(UTC)
        msg = HITLChatMessage(
            message="What should I do next?",
            timestamp=timestamp,
            is_human=True,
        )

        assert msg.message == "What should I do next?"
        assert msg.timestamp == timestamp
        assert msg.is_human is True
        assert msg.data is None

    def test_system_message_with_data(self) -> None:
        """Test creating a system message with data."""
        msg = HITLChatMessage(
            message="Task updated",
            timestamp=datetime.now(UTC),
            is_human=False,
            data={"status": "in_progress"},
        )

        assert msg.is_human is False
        assert msg.data["status"] == "in_progress"


class TestHITLContext:
    """Test HITLContext model validation and behavior."""

    def test_context_creation(self) -> None:
        """Test creating HITLContext from HITLInput."""
        context = HITLContext(
            title="Review Code",
            description="Please review the code changes",
            markdown="```python\nprint('hello')\n```",
            input_schema={"type": "object"},
            attachments=["changes.diff"],
            chat_mode=True,
        )

        assert context.title == "Review Code"
        assert len(context.attachments) == 1
        assert context.chat_mode is True


class TestHITLTaskInfo:
    """Test HITLTaskInfo model for API responses."""

    def test_task_info_creation(self) -> None:
        """Test creating HITLTaskInfo for task listing."""
        info = HITLTaskInfo(
            id="task-123",
            workflow_id="awa-hitl-12345",
            run_id="run-67890",
            title="Approve Deployment",
            description="Please approve the production deployment",
            start_time=datetime.now(UTC),
            chat_mode=False,
            non_blocking=True,
        )

        assert info.workflow_id == "awa-hitl-12345"
        assert info.non_blocking is True


class TestHITLTaskDetails:
    """Test HITLTaskDetail model for API responses."""

    def test_task_details_creation(self) -> None:
        """Test creating HITLTaskDetail for full task view."""
        details = HITLTaskDetail(
            id="task-123",
            workflow_id="awa-hitl-12345",
            parent_run_id="parent-run-456",
            title="Review",
            description="Review changes",
            start_time=datetime.now(UTC),
            markdown="# Changes",
            input_schema={"type": "object"},
        )

        assert details.workflow_id == "awa-hitl-12345"
        assert details.title == "Review"
        assert details.response_received is False
        assert details.timed_out is False
        assert details.chat_history == []
