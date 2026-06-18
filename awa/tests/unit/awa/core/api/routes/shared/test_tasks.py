"""Unit tests for HITL task API endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from awa.core.api.routes.shared import tasks
from awa.core.models.api import HITLTaskDetail, HITLTaskInfo


class TestListHITLTasks:
    """Test cases for list_hitl_tasks endpoint."""

    @pytest.mark.asyncio
    async def test_list_hitl_tasks_success(self) -> None:
        """Test successful listing of HITL tasks."""
        # Arrange
        mock_client = AsyncMock()

        mock_tasks = [
            HITLTaskInfo(
                id="task-1",
                workflow_id="workflow-1",
                title="Task 1",
                description="Description 1",
                start_time=datetime.now(UTC),
                chat_mode=False,
                non_blocking=False,
            ),
            HITLTaskInfo(
                id="task-2",
                workflow_id="workflow-2",
                title="Task 2",
                description="Description 2",
                start_time=datetime.now(UTC),
                chat_mode=True,
                non_blocking=True,
            ),
        ]
        mock_client.list_pending_tasks = AsyncMock(return_value=mock_tasks)

        current_user = {"sub": "test-user"}

        # Act
        result = await tasks.list_hitl_tasks(current_user, mock_client)

        # Assert
        assert len(result) == 2
        assert result[0].id == "task-1"
        assert result[1].id == "task-2"
        mock_client.list_pending_tasks.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_hitl_tasks_empty_list(self) -> None:
        """Test listing when no HITL tasks exist."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.list_pending_tasks = AsyncMock(return_value=[])

        current_user = {"sub": "test-user"}

        # Act
        result = await tasks.list_hitl_tasks(current_user, mock_client)

        # Assert
        assert result == []
        mock_client.list_pending_tasks.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_hitl_tasks_temporal_error(self) -> None:
        """Test error handling when Temporal client fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.list_pending_tasks = AsyncMock(side_effect=Exception("Connection failed"))
        current_user = {"sub": "test-user"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.list_hitl_tasks(current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Failed to list HITL tasks" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_hitl_tasks_with_anonymous_user(self) -> None:
        """Test listing tasks with anonymous user (empty current_user)."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.list_pending_tasks = AsyncMock(return_value=[])

        current_user = {}  # No 'sub' field

        # Act
        result = await tasks.list_hitl_tasks(current_user, mock_client)

        # Assert
        assert result == []
        mock_client.list_pending_tasks.assert_called_once()


class TestGetHITLTask:
    """Test cases for get_hitl_task endpoint."""

    @pytest.mark.asyncio
    async def test_get_hitl_task_success(self) -> None:
        """Test successful retrieval of a HITL task."""
        # Arrange
        mock_client = AsyncMock()

        mock_task_detail = HITLTaskDetail(
            workflow_id="workflow-1",
            id="task-1",
            parent_run_id="parent-run-1",
            title="Test Task",
            description="Test Description",
            start_time=datetime.now(UTC),
            markdown="## Test Markdown",
            input_schema={"type": "object"},
            attachments=[],
            chat_mode=False,
            chat_history=[],
            response_received=False,
            timed_out=False,
        )
        mock_client.get_hitl_task_details = AsyncMock(return_value=mock_task_detail)

        current_user = {"sub": "test-user"}

        # Act
        result = await tasks.get_hitl_task("task-1", current_user, mock_client)

        # Assert
        assert result.id == "task-1"
        assert result.title == "Test Task"
        assert result.markdown == "## Test Markdown"
        mock_client.get_hitl_task_details.assert_called_once_with("task-1")

    @pytest.mark.asyncio
    async def test_get_hitl_task_not_found(self) -> None:
        """Test retrieval when task is not found."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get_hitl_task_details = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Task not found"),
        )

        current_user = {"sub": "test-user"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.get_hitl_task("nonexistent-task", current_user, mock_client)

        assert exc_info.value.status_code == 404
        assert "Task not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_hitl_task_temporal_error(self) -> None:
        """Test error handling when Temporal client fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get_hitl_task_details = AsyncMock(side_effect=Exception("Database error"))

        current_user = {"sub": "test-user"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.get_hitl_task("task-1", current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Failed to get HITL task" in str(exc_info.value.detail)


class TestSubmitHITLTask:
    """Test cases for submit_hitl_task endpoint."""

    @pytest.mark.asyncio
    async def test_submit_hitl_task_success(self) -> None:
        """Test successful submission of a HITL task response."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.submit_hitl_response = AsyncMock()

        current_user = {"sub": "test-user"}
        response_data = {"name": "John Doe", "age": 30}

        # Act
        result = await tasks.submit_hitl_task("task-1", response_data, current_user, mock_client)

        # Assert
        assert result == {"data": "success"}
        mock_client.submit_hitl_response.assert_called_once_with(
            task_id="task-1",
            response_data=response_data,
        )

    @pytest.mark.asyncio
    async def test_submit_hitl_task_empty_response(self) -> None:
        """Test submission with empty response data."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.submit_hitl_response = AsyncMock()

        current_user = {"sub": "test-user"}
        response_data = {}

        # Act
        result = await tasks.submit_hitl_task("task-1", response_data, current_user, mock_client)

        # Assert
        assert result == {"data": "success"}
        mock_client.submit_hitl_response.assert_called_once_with(
            task_id="task-1",
            response_data={},
        )

    @pytest.mark.asyncio
    async def test_submit_hitl_task_complex_response(self) -> None:
        """Test submission with complex nested response data."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.submit_hitl_response = AsyncMock()

        current_user = {"sub": "test-user"}
        response_data = {
            "user": {
                "name": "Jane Doe",
                "preferences": {
                    "theme": "dark",
                    "notifications": True,
                },
            },
            "items": ["item1", "item2", "item3"],
        }

        # Act
        result = await tasks.submit_hitl_task("task-1", response_data, current_user, mock_client)

        # Assert
        assert result == {"data": "success"}
        mock_client.submit_hitl_response.assert_called_once_with(
            task_id="task-1",
            response_data=response_data,
        )

    @pytest.mark.asyncio
    async def test_submit_hitl_task_workflow_not_found(self) -> None:
        """Test submission when workflow is not found."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.submit_hitl_response = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Workflow not found"),
        )

        current_user = {"sub": "test-user"}
        response_data = {"test": "data"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.submit_hitl_task("nonexistent-task", response_data, current_user, mock_client)

        assert exc_info.value.status_code == 404
        assert "Workflow not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_submit_hitl_task_temporal_error(self) -> None:
        """Test error handling when Temporal client fails during submission."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.submit_hitl_response = AsyncMock(side_effect=Exception("Signal failed"))

        current_user = {"sub": "test-user"}
        response_data = {"test": "data"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.submit_hitl_task("task-1", response_data, current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Failed to submit HITL task" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_submit_hitl_task_with_anonymous_user(self) -> None:
        """Test submission with anonymous user."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.submit_hitl_response = AsyncMock()

        current_user = {}  # No 'sub' field
        response_data = {"name": "Anonymous"}

        # Act
        result = await tasks.submit_hitl_task("task-1", response_data, current_user, mock_client)

        # Assert
        assert result == {"data": "success"}
        mock_client.submit_hitl_response.assert_called_once()


class TestSendHITLMessage:
    """Test cases for send_hitl_message endpoint."""

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.tasks.emit_hitl_system_message")
    async def test_send_hitl_message_success_system_message(
        self,
        mock_emit: AsyncMock,
    ) -> None:
        """Test successful sending of system message to HITL task."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.send_hitl_message = AsyncMock()
        mock_emit.return_value = None

        current_user = {"sub": "test-user"}
        message_payload = {
            "message": "System message",
            "is_human": False,
            "data": {"type": "system"},
        }

        # Act
        result = await tasks.send_hitl_message("workflow-1", message_payload, current_user, mock_client)

        # Assert
        assert result == {"status": "success"}
        mock_client.send_hitl_message.assert_called_once_with(
            task_id="workflow-1",
            message="System message",
        )
        mock_emit.assert_called_once_with(
            task_id="workflow-1",
            message="System message",
            data={"type": "system"},
        )

    @pytest.mark.asyncio
    async def test_send_hitl_message_success_human_message(
        self,
    ) -> None:
        """Test successful sending of human message to HITL task."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.send_hitl_human_message = AsyncMock()
        mock_client.get_workflow_parent_id = AsyncMock(return_value="parent-workflow-1")
        mock_client.signal_workflow = AsyncMock()

        current_user = {"sub": "test-user"}
        message_payload = {
            "message": "User message",
            "is_human": True,
            "data": {"user_id": "123"},
        }

        # Act
        result = await tasks.send_hitl_message("workflow-1", message_payload, current_user, mock_client)

        # Assert
        assert result == {"status": "success"}
        mock_client.send_hitl_human_message.assert_called_once_with(
            task_id="workflow-1",
            message="User message",
            data={"user_id": "123"},
        )
        mock_client.signal_workflow.assert_called_once_with(
            "parent-workflow-1",
            "notify_user_message_received",
            "User message",
        )

    @pytest.mark.asyncio
    async def test_send_hitl_message_missing_message(
        self,
    ) -> None:
        """Test error when message field is missing."""
        # Arrange
        mock_client = AsyncMock()

        current_user = {"sub": "test-user"}
        message_payload = {"data": {"type": "empty"}}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.send_hitl_message("workflow-1", message_payload, current_user, mock_client)

        assert exc_info.value.status_code == 400
        assert "Message field is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_hitl_message_parent_signal_failure(
        self,
    ) -> None:
        """Test error when parent workflow signaling fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.send_hitl_human_message = AsyncMock()
        mock_client.get_workflow_parent_id = AsyncMock(return_value="parent-workflow-1")
        mock_client.signal_workflow = AsyncMock(side_effect=Exception("Signal failed"))

        current_user = {"sub": "test-user"}
        message_payload = {"message": "User message", "is_human": True}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.send_hitl_message("workflow-1", message_payload, current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Signal failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_hitl_message_temporal_error(
        self,
    ) -> None:
        """Test error handling when Temporal client fails."""
        # Arrange
        mock_client = AsyncMock()
        # Simulate client method failure - this message will be treated as human message by default
        mock_client.send_hitl_human_message = AsyncMock(side_effect=Exception("Connection failed"))
        current_user = {"sub": "test-user"}
        message_payload = {"message": "Test message"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.send_hitl_message("workflow-1", message_payload, current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Failed to send message to HITL task" in str(exc_info.value.detail)


class TestGetHITLChatHistory:
    """Test cases for get_hitl_chat_history endpoint."""

    @pytest.mark.asyncio
    async def test_get_hitl_chat_history_success(self) -> None:
        """Test successful retrieval of chat history."""
        # Arrange
        from awa.core.models.hitl import HITLChatMessage

        mock_client = AsyncMock()

        mock_chat_messages = [
            HITLChatMessage(
                message="Hello",
                timestamp=datetime.now(UTC),
                is_human=True,
                data={"user_id": "123"},
            ),
            HITLChatMessage(
                message="Hi there!",
                timestamp=datetime.now(UTC),
                is_human=False,
                data={"type": "greeting"},
            ),
        ]

        mock_task_detail = HITLTaskDetail(
            workflow_id="workflow-1",
            id="task-1",
            parent_run_id="parent-run-1",
            title="Test Task",
            description="Test Description",
            start_time=datetime.now(UTC),
            markdown="## Test Markdown",
            input_schema={"type": "object"},
            attachments=[],
            chat_mode=True,
            chat_history=mock_chat_messages,
            response_received=False,
            timed_out=False,
        )
        mock_client.get_hitl_task_details = AsyncMock(return_value=mock_task_detail)

        current_user = {"sub": "test-user"}

        # Act
        result = await tasks.get_hitl_chat_history("workflow-1", current_user, mock_client)

        # Assert
        assert len(result) == 2
        assert result[0]["message"] == "Hello"
        assert result[0]["isHuman"] is True
        assert result[0]["data"]["user_id"] == "123"
        assert result[1]["message"] == "Hi there!"
        assert result[1]["isHuman"] is False
        assert result[1]["data"]["type"] == "greeting"

    @pytest.mark.asyncio
    async def test_get_hitl_chat_history_empty(self) -> None:
        """Test retrieval when no chat history exists."""
        # Arrange
        mock_client = AsyncMock()

        mock_task_detail = HITLTaskDetail(
            workflow_id="workflow-1",
            id="task-1",
            parent_run_id="parent-run-1",
            title="Test Task",
            description="Test Description",
            start_time=datetime.now(UTC),
            markdown="## Test Markdown",
            input_schema={"type": "object"},
            attachments=[],
            chat_mode=True,
            chat_history=[],
            response_received=False,
            timed_out=False,
        )
        mock_client.get_hitl_task_details = AsyncMock(return_value=mock_task_detail)

        current_user = {"sub": "test-user"}

        # Act
        result = await tasks.get_hitl_chat_history("workflow-1", current_user, mock_client)

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_hitl_chat_history_task_not_found(self) -> None:
        """Test error when task is not found."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get_hitl_task_details = AsyncMock(return_value=None)

        current_user = {"sub": "test-user"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.get_hitl_chat_history("workflow-1", current_user, mock_client)

        assert exc_info.value.status_code == 404
        assert "HITL task not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_hitl_chat_history_temporal_error(self) -> None:
        """Test error handling when Temporal client fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get_hitl_task_details = AsyncMock(side_effect=Exception("Connection failed"))
        current_user = {"sub": "test-user"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.get_hitl_chat_history("workflow-1", current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Connection failed" in str(exc_info.value.detail)


class TestSendHITLUserMessage:
    """Test cases for send_hitl_user_message endpoint."""

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.tasks.emit_hitl_system_message")
    async def test_send_hitl_user_message_success(
        self,
        mock_emit: AsyncMock,
    ) -> None:
        """Test successful sending of user message."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.send_hitl_human_message = AsyncMock()
        mock_client.get_workflow_parent_id = AsyncMock(return_value="parent-workflow-1")
        mock_client.signal_workflow = AsyncMock()
        mock_emit.return_value = None

        current_user = {"sub": "test-user"}
        message_payload = {
            "message": "User question",
            "user_info": {"name": "John", "id": "123"},
        }

        # Act
        result = await tasks.send_hitl_user_message("workflow-1", message_payload, current_user, mock_client)

        # Assert
        assert result == {"status": "User message sent successfully"}
        mock_client.send_hitl_human_message.assert_called_once_with(
            task_id="workflow-1",
            message="User question",
            data={"name": "John", "id": "123"},
        )
        mock_client.signal_workflow.assert_called_once_with(
            "parent-workflow-1",
            "notify_user_message_received",
            "User question",
        )
        mock_emit.assert_called_once_with(
            task_id="workflow-1",
            message="User question",
            data={"name": "John", "id": "123"},
        )

    @pytest.mark.asyncio
    async def test_send_hitl_user_message_no_parent(
        self,
    ) -> None:
        """Test sending user message when no parent workflow exists."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.send_hitl_human_message = AsyncMock()
        mock_client.get_workflow_parent_id = AsyncMock(return_value=None)

        current_user = {"sub": "test-user"}
        message_payload = {"message": "User question"}

        # Act
        result = await tasks.send_hitl_user_message("workflow-1", message_payload, current_user, mock_client)

        # Assert
        assert result == {"status": "User message sent successfully"}
        mock_client.signal_workflow.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_hitl_user_message_empty_message(
        self,
    ) -> None:
        """Test error when message is empty."""
        # Arrange
        mock_client = AsyncMock()

        current_user = {"sub": "test-user"}
        message_payload = {"message": "   "}  # Whitespace only

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.send_hitl_user_message("workflow-1", message_payload, current_user, mock_client)

        assert exc_info.value.status_code == 400
        assert "Message is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_hitl_user_message_missing_message_field(
        self,
    ) -> None:
        """Test error when message field is missing."""
        # Arrange
        mock_client = AsyncMock()

        current_user = {"sub": "test-user"}
        message_payload = {"user_info": {"id": "123"}}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.send_hitl_user_message("workflow-1", message_payload, current_user, mock_client)

        assert exc_info.value.status_code == 400
        assert "Message is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_send_hitl_user_message_temporal_error(
        self,
    ) -> None:
        """Test error handling when Temporal client fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.send_hitl_human_message = AsyncMock(side_effect=Exception("Connection failed"))
        current_user = {"sub": "test-user"}
        message_payload = {"message": "Test message"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.send_hitl_user_message("workflow-1", message_payload, current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Connection failed" in str(exc_info.value.detail)


class TestListHITLTasksForWorkflow:
    """Test cases for list_hitl_tasks_for_workflow endpoint."""

    @pytest.mark.asyncio
    async def test_list_hitl_tasks_for_workflow_success(self) -> None:
        """Test successful listing of HITL tasks for a specific workflow."""
        # Arrange
        mock_client = AsyncMock()

        mock_tasks = [
            HITLTaskInfo(
                id="task-1",
                workflow_id="child-workflow-1",
                title="Task 1",
                description="Description 1",
                start_time=datetime.now(UTC),
                chat_mode=False,
                non_blocking=False,
            ),
            HITLTaskInfo(
                id="task-2",
                workflow_id="child-workflow-2",
                title="Task 2",
                description="Description 2",
                start_time=datetime.now(UTC),
                chat_mode=True,
                non_blocking=True,
            ),
        ]
        mock_client.list_pending_tasks_for_workflow = AsyncMock(return_value=mock_tasks)

        current_user = {"sub": "test-user"}

        # Act
        result = await tasks.list_hitl_tasks_for_workflow("parent-workflow-1", current_user, mock_client)

        # Assert
        assert len(result) == 2
        assert result[0].id == "task-1"
        assert result[1].id == "task-2"
        mock_client.list_pending_tasks_for_workflow.assert_called_once_with("parent-workflow-1")

    @pytest.mark.asyncio
    async def test_list_hitl_tasks_for_workflow_empty_list(self) -> None:
        """Test listing when no HITL tasks exist for the workflow."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.list_pending_tasks_for_workflow = AsyncMock(return_value=[])

        current_user = {"sub": "test-user"}

        # Act
        result = await tasks.list_hitl_tasks_for_workflow("parent-workflow-1", current_user, mock_client)

        # Assert
        assert result == []
        mock_client.list_pending_tasks_for_workflow.assert_called_once_with("parent-workflow-1")

    @pytest.mark.asyncio
    async def test_list_hitl_tasks_for_workflow_temporal_error(self) -> None:
        """Test error handling when Temporal client fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.list_pending_tasks_for_workflow = AsyncMock(side_effect=Exception("Connection failed"))
        current_user = {"sub": "test-user"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.list_hitl_tasks_for_workflow("parent-workflow-1", current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Failed to list HITL tasks for workflow" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_hitl_tasks_for_workflow_with_anonymous_user(self) -> None:
        """Test listing tasks for a workflow with anonymous user."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.list_pending_tasks_for_workflow = AsyncMock(return_value=[])

        current_user = {}  # No 'sub' field

        # Act
        result = await tasks.list_hitl_tasks_for_workflow("parent-workflow-1", current_user, mock_client)

        # Assert
        assert result == []
        mock_client.list_pending_tasks_for_workflow.assert_called_once_with("parent-workflow-1")

    @pytest.mark.asyncio
    async def test_list_hitl_tasks_for_workflow_client_error(self) -> None:
        """Test error handling when list_pending_tasks_for_workflow fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.list_pending_tasks_for_workflow = AsyncMock(side_effect=Exception("Query failed"))

        current_user = {"sub": "test-user"}

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tasks.list_hitl_tasks_for_workflow("parent-workflow-1", current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Failed to list HITL tasks for workflow" in str(exc_info.value.detail)
