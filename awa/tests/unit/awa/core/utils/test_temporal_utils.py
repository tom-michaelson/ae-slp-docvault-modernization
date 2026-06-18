import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from temporalio.activity import Info
from temporalio.client import Client, WorkflowExecutionDescription, WorkflowHandle

from awa.core.models.api import WorkflowRunStatus
from awa.core.utils.temporal_utils import TemporalUtils, _get_active_worker_pollers, map_temporal_status

# Constants for test expectations
EXPECTED_ACTIVE_WORKERS = 2


class TestTemporalUtils:
    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_no_parent(self) -> None:
        """Test getting task queue when there is no parent workflow."""
        # Arrange
        mock_client = Mock(spec=Client)
        mock_activity_info = Mock(spec=Info)
        mock_activity_info.task_queue = "child-task-queue"
        mock_activity_info.workflow_id = "workflow-123"

        mock_workflow_handle = Mock(spec=WorkflowHandle)
        mock_client.get_workflow_handle.return_value = mock_workflow_handle

        mock_description = Mock(spec=WorkflowExecutionDescription)
        mock_description.task_queue = "parent-task-queue"
        mock_description.parent_id = None  # No parent
        mock_workflow_handle.describe = AsyncMock(return_value=mock_description)

        # Act
        result = await TemporalUtils.get_parent_workflow_task_queue_for_activity(mock_client, mock_activity_info)

        # Assert
        assert result == "parent-task-queue"
        mock_client.get_workflow_handle.assert_called_once_with("workflow-123")
        mock_workflow_handle.describe.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_single_parent(self) -> None:
        """Test getting task queue when there is one parent workflow."""
        # Arrange
        expected_call_count = 2
        mock_client = Mock(spec=Client)
        mock_activity_info = Mock(spec=Info)
        mock_activity_info.task_queue = "child-task-queue"
        mock_activity_info.workflow_id = "child-workflow-123"

        # Mock child workflow
        mock_child_handle = Mock(spec=WorkflowHandle)
        mock_child_description = Mock(spec=WorkflowExecutionDescription)
        mock_child_description.task_queue = "child-task-queue"
        mock_child_description.parent_id = "parent-workflow-456"
        mock_child_handle.describe = AsyncMock(return_value=mock_child_description)

        # Mock parent workflow
        mock_parent_handle = Mock(spec=WorkflowHandle)
        mock_parent_description = Mock(spec=WorkflowExecutionDescription)
        mock_parent_description.task_queue = "parent-task-queue"
        mock_parent_description.parent_id = None  # Top-level parent
        mock_parent_handle.describe = AsyncMock(return_value=mock_parent_description)

        # Configure client to return appropriate handles
        def get_workflow_handle(workflow_id: str) -> Mock:
            if workflow_id == "child-workflow-123":
                return mock_child_handle
            if workflow_id == "parent-workflow-456":
                return mock_parent_handle
            return Mock()

        mock_client.get_workflow_handle.side_effect = get_workflow_handle

        # Act
        result = await TemporalUtils.get_parent_workflow_task_queue_for_activity(mock_client, mock_activity_info)

        # Assert
        assert result == "parent-task-queue"
        assert mock_client.get_workflow_handle.call_count == expected_call_count
        mock_client.get_workflow_handle.assert_any_call("child-workflow-123")
        mock_client.get_workflow_handle.assert_any_call("parent-workflow-456")

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_multiple_parents(self) -> None:
        """Test getting task queue when there are multiple levels of parent workflows."""
        # Arrange
        expected_call_count = 3
        mock_client = Mock(spec=Client)
        mock_activity_info = Mock(spec=Info)
        mock_activity_info.task_queue = "child-task-queue"
        mock_activity_info.workflow_id = "child-workflow-123"

        # Mock child workflow
        mock_child_handle = Mock(spec=WorkflowHandle)
        mock_child_description = Mock(spec=WorkflowExecutionDescription)
        mock_child_description.task_queue = "child-task-queue"
        mock_child_description.parent_id = "parent-workflow-456"
        mock_child_handle.describe = AsyncMock(return_value=mock_child_description)

        # Mock middle parent workflow
        mock_middle_handle = Mock(spec=WorkflowHandle)
        mock_middle_description = Mock(spec=WorkflowExecutionDescription)
        mock_middle_description.task_queue = "middle-task-queue"
        mock_middle_description.parent_id = "grandparent-workflow-789"
        mock_middle_handle.describe = AsyncMock(return_value=mock_middle_description)

        # Mock top-level parent workflow
        mock_grandparent_handle = Mock(spec=WorkflowHandle)
        mock_grandparent_description = Mock(spec=WorkflowExecutionDescription)
        mock_grandparent_description.task_queue = "grandparent-task-queue"
        mock_grandparent_description.parent_id = None  # Top-level parent
        mock_grandparent_handle.describe = AsyncMock(return_value=mock_grandparent_description)

        # Configure client to return appropriate handles
        def get_workflow_handle(workflow_id: str) -> Mock:
            if workflow_id == "child-workflow-123":
                return mock_child_handle
            if workflow_id == "parent-workflow-456":
                return mock_middle_handle
            if workflow_id == "grandparent-workflow-789":
                return mock_grandparent_handle
            return Mock()

        mock_client.get_workflow_handle.side_effect = get_workflow_handle

        # Act
        result = await TemporalUtils.get_parent_workflow_task_queue_for_activity(mock_client, mock_activity_info)

        # Assert
        assert result == "grandparent-task-queue"
        assert mock_client.get_workflow_handle.call_count == expected_call_count
        mock_client.get_workflow_handle.assert_any_call("child-workflow-123")
        mock_client.get_workflow_handle.assert_any_call("parent-workflow-456")
        mock_client.get_workflow_handle.assert_any_call("grandparent-workflow-789")

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_empty_workflow_id(self) -> None:
        """Test getting task queue when workflow_id is None or empty."""
        # Arrange
        mock_client = Mock(spec=Client)
        mock_activity_info = Mock(spec=Info)
        mock_activity_info.task_queue = "initial-task-queue"
        mock_activity_info.workflow_id = None  # No workflow ID

        # Act
        result = await TemporalUtils.get_parent_workflow_task_queue_for_activity(mock_client, mock_activity_info)

        # Assert
        assert result == "initial-task-queue"
        mock_client.get_workflow_handle.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_temporal_client_exception(self) -> None:
        """Test that exceptions from temporal client are propagated."""
        # Arrange
        mock_client = Mock(spec=Client)
        mock_activity_info = Mock(spec=Info)
        mock_activity_info.task_queue = "child-task-queue"
        mock_activity_info.workflow_id = "workflow-123"

        mock_workflow_handle = Mock(spec=WorkflowHandle)
        mock_client.get_workflow_handle.return_value = mock_workflow_handle
        mock_workflow_handle.describe = AsyncMock(side_effect=Exception("Temporal service error"))

        # Act & Assert
        with pytest.raises(Exception, match="Temporal service error"):
            await TemporalUtils.get_parent_workflow_task_queue_for_activity(mock_client, mock_activity_info)

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_preserves_task_queue_changes(self) -> None:
        """Test that the method returns the final parent's task queue, not the initial one."""
        # Arrange
        mock_client = Mock(spec=Client)
        mock_activity_info = Mock(spec=Info)
        mock_activity_info.task_queue = "original-task-queue"
        mock_activity_info.workflow_id = "child-workflow-123"

        # Mock child workflow with different task queue
        mock_child_handle = Mock(spec=WorkflowHandle)
        mock_child_description = Mock(spec=WorkflowExecutionDescription)
        mock_child_description.task_queue = "updated-task-queue"
        mock_child_description.parent_id = None  # No parent
        mock_child_handle.describe = AsyncMock(return_value=mock_child_description)

        mock_client.get_workflow_handle.return_value = mock_child_handle

        # Act
        result = await TemporalUtils.get_parent_workflow_task_queue_for_activity(mock_client, mock_activity_info)

        # Assert
        assert result == "updated-task-queue"
        assert result != mock_activity_info.task_queue  # Verify it's not the original

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_with_active_workers(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers with active workers."""
        # Arrange
        task_queue = "test_queue"
        current_time = datetime.now(tz=UTC)
        recent_time = current_time - timedelta(seconds=30)  # Within 66 second threshold

        mock_response = {
            "pollers": [
                {
                    "identity": "worker-1@host-1",
                    "lastAccessTime": recent_time.isoformat() + "Z",
                },
                {
                    "identity": "worker-2@host-2",
                    "lastAccessTime": recent_time.isoformat() + "Z",
                },
            ],
        }

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.return_value = (True, json.dumps(mock_response))

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert len(result) == EXPECTED_ACTIVE_WORKERS
            assert "worker-1@host-1" in result
            assert "worker-2@host-2" in result
            mock_command.assert_called_once_with(
                f"temporal task-queue describe --task-queue {task_queue} --output json",
            )

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_no_active_workers(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers with old workers."""
        # Arrange
        task_queue = "test_queue"
        current_time = datetime.now(tz=UTC)
        old_time = current_time - timedelta(minutes=5)  # Beyond 66 second threshold

        mock_response = {
            "pollers": [
                {
                    "identity": "worker-1@host-1",
                    "lastAccessTime": old_time.isoformat() + "Z",
                },
            ],
        }

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.return_value = (True, json.dumps(mock_response))

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert result == []
            mock_command.assert_called_once_with(
                f"temporal task-queue describe --task-queue {task_queue} --output json",
            )

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_empty_pollers_list(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers with empty pollers list."""
        # Arrange
        task_queue = "test_queue"
        mock_response = {"pollers": []}

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.return_value = (True, json.dumps(mock_response))

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_null_pollers(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers with null pollers."""
        # Arrange
        task_queue = "test_queue"
        mock_response = {"pollers": None}

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.return_value = (True, json.dumps(mock_response))

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_command_failure(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers when command fails."""
        # Arrange
        task_queue = "test_queue"

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.return_value = (False, "Command failed")

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert result == []
            mock_command.assert_called_once_with(
                f"temporal task-queue describe --task-queue {task_queue} --output json",
            )

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_invalid_json(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers with invalid JSON response."""
        # Arrange
        task_queue = "test_queue"

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.return_value = (True, "invalid json response")

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert result == []
            mock_command.assert_called_once_with(
                f"temporal task-queue describe --task-queue {task_queue} --output json",
            )

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_invalid_timestamp(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers with invalid timestamp."""
        # Arrange
        task_queue = "test_queue"
        mock_response = {
            "pollers": [
                {
                    "identity": "worker-1@host-1",
                    "lastAccessTime": "invalid-timestamp",
                },
            ],
        }

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.return_value = (True, json.dumps(mock_response))

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_missing_identity(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers with missing identity."""
        # Arrange
        task_queue = "test_queue"
        current_time = datetime.now(tz=UTC)
        recent_time = current_time - timedelta(seconds=30)

        mock_response = {
            "pollers": [
                {
                    "lastAccessTime": recent_time.isoformat() + "Z",
                },
            ],
        }

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.return_value = (True, json.dumps(mock_response))

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_duplicate_identities(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers filters duplicate identities."""
        # Arrange
        task_queue = "test_queue"
        current_time = datetime.now(tz=UTC)
        recent_time = current_time - timedelta(seconds=30)

        mock_response = {
            "pollers": [
                {
                    "identity": "worker-1@host-1",
                    "lastAccessTime": recent_time.isoformat() + "Z",
                },
                {
                    "identity": "worker-1@host-1",  # Duplicate
                    "lastAccessTime": recent_time.isoformat() + "Z",
                },
            ],
        }

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.return_value = (True, json.dumps(mock_response))

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert len(result) == 1
            assert "worker-1@host-1" in result

    @pytest.mark.asyncio
    async def test_get_active_worker_pollers_exception_handling(self) -> None:
        """Test TemporalUtils.get_active_worker_pollers handles unexpected exceptions."""
        # Arrange
        task_queue = "test_queue"

        with patch(
            "awa.core.utils.temporal_utils.CommandUtils.run_command_async",
            new_callable=AsyncMock,
        ) as mock_command:
            mock_command.side_effect = Exception("Unexpected error")

            # Act
            result = await _get_active_worker_pollers(task_queue)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_map_temporal_status(self) -> None:
        """Test TemporalUtils.map_temporal_status maps temporal statuses to readable strings."""
        assert map_temporal_status(0) is WorkflowRunStatus.UNSPECIFIED
        assert map_temporal_status(1) is WorkflowRunStatus.RUNNING
        assert map_temporal_status(2) is WorkflowRunStatus.COMPLETED
        assert map_temporal_status(3) is WorkflowRunStatus.FAILED
        assert map_temporal_status(4) is WorkflowRunStatus.CANCELED
        assert map_temporal_status(5) is WorkflowRunStatus.TERMINATED
        assert map_temporal_status(6) is WorkflowRunStatus.CONTINUED_AS_NEW
        assert map_temporal_status(7) is WorkflowRunStatus.TIMED_OUT
