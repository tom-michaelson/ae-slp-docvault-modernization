"""Unit tests for HITLTaskClient."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from awa.core.engine.hitl_task_client import HITLTaskClient
from awa.core.models.api import HITLTaskDetail, HITLTaskInfo
from awa.core.models.hitl import HITLResponse


class TestHITLTaskClient:
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_temporal_client = AsyncMock()
        self.client = HITLTaskClient(self.mock_temporal_client)

    @pytest.mark.asyncio
    async def test_list_pending_tasks_with_pending_hitl_workflows(self) -> None:
        """Test listing pending HITL tasks returns tasks correctly."""

        # Create mock workflow instances
        class MockWorkflow:
            def __init__(self, workflow_id: str, parent_id: str | None, workflow_type: str) -> None:
                self.id = workflow_id
                self.parent_id = parent_id
                self.workflow_type = workflow_type
                self.execution_time = datetime.now(UTC)

        # Create mock workflow handle
        mock_handle = AsyncMock()
        mock_handle.query = AsyncMock()

        # Set up query responses for HITL child workflow
        async def query_side_effect(query_name: str) -> Any:  # noqa: ANN401
            if query_name == "get_context":
                return {
                    "title": "Test Task",
                    "description": "Test Description",
                    "chat_mode": True,
                }
            if query_name == "is_response_received":
                return False
            return None

        mock_handle.query.side_effect = query_side_effect

        # Mock client methods
        self.mock_temporal_client.get_workflow_handle = Mock(return_value=mock_handle)

        # Create workflows to return from list_workflows
        workflows = [
            MockWorkflow("parent-1", None, "ParentWorkflow"),  # Parent workflow - should be skipped
            MockWorkflow("child-1", "parent-1", "awa-hitl-child-workflow"),  # HITL child - should be included
            MockWorkflow("child-2", "parent-1", "OtherChildWorkflow"),  # Non-HITL child - should be skipped
        ]

        async def list_workflows_generator(_query: str) -> AsyncGenerator:
            for workflow in workflows:
                yield workflow

        self.mock_temporal_client.list_workflows = list_workflows_generator

        # Execute the method
        tasks = await self.client.list_pending_tasks()

        # Verify results
        assert len(tasks) == 1
        assert isinstance(tasks[0], HITLTaskInfo)
        assert tasks[0].id == "child-1"
        assert tasks[0].workflow_id == "parent-1"
        assert tasks[0].title == "Test Task"
        assert tasks[0].description == "Test Description"
        assert tasks[0].chat_mode is True

    @pytest.mark.asyncio
    async def test_list_pending_tasks_filters_out_completed_tasks(self) -> None:
        """Test that tasks with received responses are filtered out."""

        class MockWorkflow:
            def __init__(self, workflow_id: str, parent_id: str) -> None:
                self.id = workflow_id
                self.parent_id = parent_id
                self.workflow_type = "awa-hitl-child-workflow"
                self.execution_time = datetime.now(UTC)

        mock_handle = AsyncMock()

        # Set up query responses - this task has already received a response
        async def query_side_effect(query_name: str) -> Any:  # noqa: ANN401
            if query_name == "get_context":
                return {"title": "Completed Task", "description": "Already responded"}
            if query_name == "is_response_received":
                return True  # Response already received
            return None

        mock_handle.query.side_effect = query_side_effect
        self.mock_temporal_client.get_workflow_handle = Mock(return_value=mock_handle)

        workflows = [MockWorkflow("child-1", "parent-1")]

        async def list_workflows_generator(_query: str) -> AsyncGenerator:
            for workflow in workflows:
                yield workflow

        self.mock_temporal_client.list_workflows = list_workflows_generator

        tasks = await self.client.list_pending_tasks()
        assert len(tasks) == 0  # Should be empty since response was received

    @pytest.mark.asyncio
    async def test_get_task_details_returns_full_details(self) -> None:
        """Test getting detailed task information."""
        task_id = "test-task-123"

        # Mock workflow handle
        mock_handle = AsyncMock()

        # Mock describe response for HITL task
        class MockDescription:
            parent_id = "parent-workflow-id"
            start_time = datetime.now(UTC)
            run_id = "hitl-run-123"

        mock_handle.describe = AsyncMock(return_value=MockDescription())

        # Mock parent workflow handle for getting parent run ID
        mock_parent_handle = AsyncMock()

        class MockParentDescription:
            run_id = "parent-run-456"

        mock_parent_handle.describe = AsyncMock(return_value=MockParentDescription())

        # Mock query responses
        async def query_side_effect(query_name: str) -> Any:  # noqa: ANN401
            if query_name == "get_context":
                return {
                    "title": "Detailed Task",
                    "description": "Task with full details",
                    "markdown": "# Task Content",
                    "input_schema": {"type": "object", "properties": {"field": {"type": "string"}}},
                    "attachments": ["file1.txt", "file2.pdf"],
                    "chat_mode": True,
                }
            if query_name == "get_chat_history":
                return [
                    {"message": "Hello", "timestamp": "2024-01-01T00:00:00Z", "is_human": True},
                    {"message": "Hi there", "timestamp": "2024-01-01T00:01:00Z", "is_human": False},
                ]
            if query_name == "is_response_received":
                return False
            return None

        mock_handle.query.side_effect = query_side_effect

        def get_workflow_handle_side_effect(workflow_id: str) -> AsyncMock:
            if workflow_id == "parent-workflow-id":
                return mock_parent_handle
            return mock_handle

        self.mock_temporal_client.get_workflow_handle = Mock(side_effect=get_workflow_handle_side_effect)

        # Execute the method
        details = await self.client.get_task_details(task_id)

        # Verify results
        assert details is not None
        assert isinstance(details, HITLTaskDetail)
        assert details.id == task_id
        assert details.workflow_id == "parent-workflow-id"
        assert details.parent_run_id == "parent-run-456"
        assert details.title == "Detailed Task"
        assert details.description == "Task with full details"
        assert details.markdown == "# Task Content"
        assert details.input_schema == {"type": "object", "properties": {"field": {"type": "string"}}}
        assert len(details.attachments) == 2
        assert details.chat_mode is True
        assert len(details.chat_history) == 2
        assert details.response_received is False
        assert details.timed_out is False

    @pytest.mark.asyncio
    async def test_get_task_details_returns_none_when_no_context(self) -> None:
        """Test that None is returned when task has no context."""
        task_id = "test-task-no-context"

        mock_handle = AsyncMock()

        class MockDescription:
            parent_id = "parent-workflow-id"
            start_time = datetime.now(UTC)

        mock_handle.describe = AsyncMock(return_value=MockDescription())

        # Return None for context query
        async def query_side_effect(query_name: str) -> None:
            pass

        mock_handle.query.side_effect = query_side_effect
        self.mock_temporal_client.get_workflow_handle = Mock(return_value=mock_handle)

        details = await self.client.get_task_details(task_id)
        assert details is None

    @pytest.mark.asyncio
    async def test_submit_response_sends_signal_correctly(self) -> None:
        """Test submitting a response to a HITL task."""
        task_id = "test-task-submit"
        response_data = {"field1": "value1", "field2": 42}

        # Mock workflow handle
        mock_handle = AsyncMock()
        mock_handle.id = task_id
        mock_handle.run_id = "run-123"
        mock_handle.signal = AsyncMock()

        # Mock the describe method to return parent_id for signaling
        mock_description = AsyncMock()
        mock_description.parent_id = "parent-workflow-id"
        mock_handle.describe = AsyncMock(return_value=mock_description)

        # Mock parent workflow handle
        mock_parent_handle = AsyncMock()
        mock_parent_handle.signal = AsyncMock()

        def get_workflow_handle_side_effect(workflow_id: str) -> None:
            if workflow_id == task_id:
                return mock_handle
            if workflow_id == "parent-workflow-id":
                return mock_parent_handle
            return AsyncMock()

        self.mock_temporal_client.get_workflow_handle = Mock(side_effect=get_workflow_handle_side_effect)

        # Execute the method
        await self.client.submit_response(task_id, response_data)

        # Verify child workflow signal was called once for submit_response
        mock_handle.signal.assert_called_once_with("submit_response", HITLResponse(data=response_data))

        # Verify parent workflow signal was called once for mark_conversation_complete
        mock_parent_handle.signal.assert_called_once_with("mark_conversation_complete")

    @pytest.mark.asyncio
    async def test_extract_task_info_handles_missing_fields(self) -> None:
        """Test that _extract_task_info handles missing optional fields gracefully."""

        class MockWorkflow:
            def __init__(self) -> None:
                self.id = "child-minimal"
                self.parent_id = "parent-minimal"
                self.workflow_type = "awa-hitl-child-workflow"
                self.execution_time = datetime.now(UTC)

        mock_handle = AsyncMock()

        # Minimal context with missing optional fields but still truthy
        async def query_side_effect(query_name: str) -> Any:  # noqa: ANN401
            if query_name == "get_context":
                return {"some_field": "value"}  # Minimal context but truthy
            if query_name == "is_response_received":
                return False
            return None

        mock_handle.query.side_effect = query_side_effect
        self.mock_temporal_client.get_workflow_handle = Mock(return_value=mock_handle)

        workflow = MockWorkflow()
        task_info = await self.client._extract_task_info(workflow)

        assert task_info is not None
        assert task_info.id == "child-minimal"
        assert task_info.workflow_id == "parent-minimal"
        assert task_info.title == "Untitled Task"  # Default value
        assert task_info.description == ""  # Default value
        assert task_info.chat_mode is False  # Default value
        assert task_info.non_blocking is False  # Default value

    @pytest.mark.asyncio
    async def test_extract_task_info_returns_none_when_no_context(self) -> None:
        """Test that _extract_task_info returns None when context is empty."""

        class MockWorkflow:
            def __init__(self) -> None:
                self.id = "child-no-context"
                self.parent_id = "parent-no-context"
                self.workflow_type = "awa-hitl-child-workflow"
                self.execution_time = datetime.now(UTC)

        mock_handle = AsyncMock()

        async def query_side_effect(query_name: str) -> Any:  # noqa: ANN401
            if query_name == "get_context":
                return {}  # Empty context - should be filtered out
            if query_name == "is_response_received":
                return False
            return None

        mock_handle.query.side_effect = query_side_effect
        self.mock_temporal_client.get_workflow_handle = Mock(return_value=mock_handle)

        workflow = MockWorkflow()
        task_info = await self.client._extract_task_info(workflow)
        assert task_info is None  # Empty context should return None

    @pytest.mark.asyncio
    async def test_extract_task_info_returns_none_when_response_received(self) -> None:
        """Test that _extract_task_info returns None when response is already received."""

        class MockWorkflow:
            def __init__(self) -> None:
                self.id = "child-responded"
                self.parent_id = "parent-responded"
                self.workflow_type = "awa-hitl-child-workflow"
                self.execution_time = datetime.now(UTC)

        mock_handle = AsyncMock()

        async def query_side_effect(query_name: str) -> Any:  # noqa: ANN401
            if query_name == "get_context":
                return {"title": "Task"}
            if query_name == "is_response_received":
                return True  # Response already received
            return None

        mock_handle.query.side_effect = query_side_effect
        self.mock_temporal_client.get_workflow_handle = Mock(return_value=mock_handle)

        workflow = MockWorkflow()
        task_info = await self.client._extract_task_info(workflow)
        assert task_info is None

    @pytest.mark.asyncio
    async def test_list_pending_tasks_for_workflow_success(self) -> None:
        """Test listing pending tasks for a specific workflow."""
        workflow_id = "parent-workflow-123"

        # Create mock workflow instances
        class MockWorkflow:
            def __init__(self, wid: str, parent_id: str | None, wtype: str) -> None:
                self.id = wid
                self.run_id = wid  # For tests, use same value for id and run_id
                self.parent_id = parent_id
                self.workflow_type = wtype
                self.execution_time = datetime.now(UTC)

        # Create workflows - one parent, two HITL children, one other child
        workflows = [
            MockWorkflow("parent-workflow-123", None, "ParentWorkflow"),  # Parent (should be skipped)
            MockWorkflow("child-hitl-1", "parent-workflow-123", "awa-hitl-child-workflow"),  # HITL child
            MockWorkflow("child-hitl-2", "parent-workflow-123", "awa-hitl-child-workflow"),  # HITL child
            MockWorkflow("child-other", "parent-workflow-123", "OtherChildWorkflow"),  # Non-HITL child
            MockWorkflow("unrelated-child", "other-parent", "awa-hitl-child-workflow"),  # Different parent
        ]

        async def mock_list_workflows(_query: str) -> AsyncGenerator:
            for workflow in workflows:
                yield workflow

        self.mock_temporal_client.list_workflows = mock_list_workflows

        # Mock workflow handles for HITL children
        def create_mock_handle(wid: str, should_have_context: bool) -> AsyncMock:
            mock_handle = AsyncMock()
            if should_have_context:

                async def query_side_effect(query_name: str) -> Any:  # noqa: ANN401
                    if query_name == "get_context":
                        return {
                            "title": f"Task for {wid}",
                            "description": f"Description for {wid}",
                            "chat_mode": False,
                        }
                    if query_name == "is_response_received":
                        return False
                    return None

                mock_handle.query.side_effect = query_side_effect
            else:
                mock_handle.query.return_value = None
            return mock_handle

        mock_handles = {}
        for workflow in workflows:
            if workflow.workflow_type == "awa-hitl-child-workflow":
                should_have_context = workflow.parent_id == workflow_id
                mock_handles[workflow.id] = create_mock_handle(workflow.id, should_have_context)

        self.mock_temporal_client.get_workflow_handle = Mock(side_effect=lambda wid: mock_handles.get(wid))

        # Execute the method
        result = await self.client.list_pending_tasks_for_workflow(workflow_id)

        # Verify results
        assert len(result) == 2
        assert all(isinstance(task, HITLTaskInfo) for task in result)
        assert result[0].workflow_id == "parent-workflow-123"
        assert result[1].workflow_id == "parent-workflow-123"
        assert "child-hitl-1" in result[0].title or "child-hitl-2" in result[0].title
        assert "child-hitl-1" in result[1].title or "child-hitl-2" in result[1].title

    @pytest.mark.asyncio
    async def test_list_pending_tasks_for_workflow_empty(self) -> None:
        """Test listing pending tasks for workflow with no HITL children."""
        workflow_id = "parent-no-children"

        class MockWorkflow:
            def __init__(self, wid: str, parent_id: str | None, wtype: str) -> None:
                self.id = wid
                self.run_id = wid  # For tests, use same value for id and run_id
                self.parent_id = parent_id
                self.workflow_type = wtype
                self.execution_time = datetime.now(UTC)

        # Only parent workflow, no children
        workflows = [
            MockWorkflow("parent-no-children", None, "ParentWorkflow"),
        ]

        async def mock_list_workflows(_query: str) -> AsyncGenerator:
            for workflow in workflows:
                yield workflow

        self.mock_temporal_client.list_workflows = mock_list_workflows

        # Execute the method
        result = await self.client.list_pending_tasks_for_workflow(workflow_id)

        # Verify empty result
        assert result == []

    @pytest.mark.asyncio
    async def test_list_pending_tasks_for_workflow_filters_completed_tasks(self) -> None:
        """Test that completed tasks are filtered out."""
        workflow_id = "parent-workflow-456"

        class MockWorkflow:
            def __init__(self, wid: str, parent_id: str | None, wtype: str) -> None:
                self.id = wid
                self.run_id = wid  # For tests, use same value for id and run_id
                self.parent_id = parent_id
                self.workflow_type = wtype
                self.execution_time = datetime.now(UTC)

        workflows = [
            MockWorkflow("child-pending", "parent-workflow-456", "awa-hitl-child-workflow"),
            MockWorkflow("child-completed", "parent-workflow-456", "awa-hitl-child-workflow"),
        ]

        async def mock_list_workflows(_query: str) -> AsyncGenerator:
            for workflow in workflows:
                yield workflow

        self.mock_temporal_client.list_workflows = mock_list_workflows

        # Mock handles
        mock_handle_pending = AsyncMock()

        async def query_pending(query_name: str) -> Any:  # noqa: ANN401
            if query_name == "get_context":
                return {"title": "Pending Task", "description": "Still waiting"}
            if query_name == "is_response_received":
                return False  # Not completed
            return None

        mock_handle_pending.query.side_effect = query_pending

        mock_handle_completed = AsyncMock()

        async def query_completed(query_name: str) -> Any:  # noqa: ANN401
            if query_name == "get_context":
                return {"title": "Completed Task", "description": "Already done"}
            if query_name == "is_response_received":
                return True  # Already completed
            return None

        mock_handle_completed.query.side_effect = query_completed

        def get_handle(wid: str) -> AsyncMock:
            if wid == "child-pending":
                return mock_handle_pending
            if wid == "child-completed":
                return mock_handle_completed
            return AsyncMock()

        self.mock_temporal_client.get_workflow_handle = Mock(side_effect=get_handle)

        # Execute the method
        result = await self.client.list_pending_tasks_for_workflow(workflow_id)

        # Verify only pending task is returned
        assert len(result) == 1
        assert result[0].title == "Pending Task"
        assert result[0].id == "child-pending"

    @pytest.mark.asyncio
    async def test_list_pending_tasks_for_workflow_skips_parent_workflows(self) -> None:
        """Test that parent workflows are skipped."""
        workflow_id = "parent-workflow-789"

        class MockWorkflow:
            def __init__(self, wid: str, parent_id: str | None, wtype: str) -> None:
                self.id = wid
                self.run_id = wid  # For tests, use same value for id and run_id
                self.parent_id = parent_id
                self.workflow_type = wtype
                self.execution_time = datetime.now(UTC)

        workflows = [
            MockWorkflow("parent-workflow-789", None, "awa-hitl-child-workflow"),  # Parent (should be skipped)
            MockWorkflow("child-hitl", "parent-workflow-789", "awa-hitl-child-workflow"),  # Child
        ]

        async def mock_list_workflows(_query: str) -> AsyncGenerator:
            for workflow in workflows:
                yield workflow

        self.mock_temporal_client.list_workflows = mock_list_workflows

        # Mock handle for child
        mock_handle = AsyncMock()

        async def query_side_effect(query_name: str) -> Any:  # noqa: ANN401
            if query_name == "get_context":
                return {"title": "Child Task", "description": "Valid child"}
            if query_name == "is_response_received":
                return False
            return None

        mock_handle.query.side_effect = query_side_effect

        self.mock_temporal_client.get_workflow_handle = Mock(return_value=mock_handle)

        # Execute the method
        result = await self.client.list_pending_tasks_for_workflow(workflow_id)

        # Verify only child is returned
        assert len(result) == 1
        assert result[0].id == "child-hitl"
        assert result[0].title == "Child Task"
