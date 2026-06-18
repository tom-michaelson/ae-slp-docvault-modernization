from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio.activity import Info as ActivityInfo
from temporalio.client import WorkflowHandle
from temporalio.common import Priority
from temporalio.testing import ActivityEnvironment

from awa.core.activities.get_parent_workflow_task_queue import GetParentWorkflowTaskQueueActivity
from awa.sdk import constants as sdk_constants


class TestGetParentWorkflowTaskQueueActivity:
    @pytest.fixture
    def mock_temporal_client(self) -> MagicMock:
        """Create a mock temporal client for testing."""
        return MagicMock()

    @pytest.fixture
    def activity_instance(self, mock_temporal_client: MagicMock) -> GetParentWorkflowTaskQueueActivity:
        """Create a GetParentWorkflowTaskQueueActivity instance with mocked client."""
        return GetParentWorkflowTaskQueueActivity(mock_temporal_client)

    @pytest.fixture
    def mock_activity_info(self) -> MagicMock:
        """Create a mock activity info for testing."""
        mock_info = MagicMock(spec=ActivityInfo)
        mock_info.activity_id = "test_activity_id"
        mock_info.activity_type = "test_activity_type"
        mock_info.attempt = 1
        mock_info.current_attempt_scheduled_time = datetime.now(UTC)
        mock_info.heartbeat_details = []
        mock_info.heartbeat_timeout = timedelta(seconds=30)
        mock_info.is_local = False
        mock_info.schedule_to_close_timeout = timedelta(seconds=60)
        mock_info.scheduled_time = datetime.now(UTC)
        mock_info.start_to_close_timeout = timedelta(seconds=30)
        mock_info.started_time = datetime.now(UTC)
        mock_info.task_queue = "test_task_queue"
        mock_info.task_token = b"test_token"
        mock_info.workflow_id = "test_workflow_id"
        mock_info.workflow_namespace = "test_namespace"
        mock_info.workflow_run_id = "test_run_id"
        mock_info.workflow_type = "test_workflow_type"
        mock_info.priority = Priority(priority_key=1)
        return mock_info

    def test_activity_name_constant(self) -> None:
        """Test that the activity name constant is correctly defined."""
        assert sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE == "awa-get-parent-workflow-task-queue"

    def test_init_stores_temporal_client(self, mock_temporal_client: MagicMock) -> None:
        """Test that the constructor properly stores the temporal client."""
        # Act
        activity = GetParentWorkflowTaskQueueActivity(mock_temporal_client)

        # Assert
        assert activity._temporal_client is mock_temporal_client

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_success(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
        mock_activity_info: MagicMock,
    ) -> None:
        """Test successful retrieval of parent workflow task queue."""
        # Arrange
        expected_task_queue = "parent_task_queue"

        with (
            patch("awa.core.activities.get_parent_workflow_task_queue.activity.info", return_value=mock_activity_info),
            patch(
                "awa.core.activities.get_parent_workflow_task_queue.TemporalUtils.get_parent_workflow_task_queue_for_activity",
            ) as mock_temporal_utils,
        ):
            mock_temporal_utils.return_value = expected_task_queue

            # Act
            result = await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)

            # Assert
            assert result == expected_task_queue
            mock_temporal_utils.assert_called_once_with(
                activity_instance._temporal_client,
                mock_activity_info,
            )

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_temporal_utils_exception(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
        mock_activity_info: MagicMock,
    ) -> None:
        """Test that exceptions from TemporalUtils are properly propagated."""
        # Arrange
        expected_error_message = "Temporal client error"

        with (
            patch("awa.core.activities.get_parent_workflow_task_queue.activity.info", return_value=mock_activity_info),
            patch(
                "awa.core.activities.get_parent_workflow_task_queue.TemporalUtils.get_parent_workflow_task_queue_for_activity",
            ) as mock_temporal_utils,
        ):
            mock_temporal_utils.side_effect = Exception(expected_error_message)

            # Act & Assert
            with pytest.raises(Exception, match=expected_error_message):
                await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_with_complex_task_queue(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
        mock_activity_info: MagicMock,
    ) -> None:
        """Test with a complex task queue name containing special characters."""
        # Arrange
        expected_task_queue = "my-complex_task.queue:with-special@chars"

        with (
            patch("awa.core.activities.get_parent_workflow_task_queue.activity.info", return_value=mock_activity_info),
            patch(
                "awa.core.activities.get_parent_workflow_task_queue.TemporalUtils.get_parent_workflow_task_queue_for_activity",
            ) as mock_temporal_utils,
        ):
            mock_temporal_utils.return_value = expected_task_queue

            # Act
            result = await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)

            # Assert
            assert result == expected_task_queue
            mock_temporal_utils.assert_called_once_with(
                activity_instance._temporal_client,
                mock_activity_info,
            )

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_with_empty_task_queue(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
        mock_activity_info: MagicMock,
    ) -> None:
        """Test with an empty task queue name."""
        # Arrange
        expected_task_queue = ""

        with (
            patch("awa.core.activities.get_parent_workflow_task_queue.activity.info", return_value=mock_activity_info),
            patch(
                "awa.core.activities.get_parent_workflow_task_queue.TemporalUtils.get_parent_workflow_task_queue_for_activity",
            ) as mock_temporal_utils,
        ):
            mock_temporal_utils.return_value = expected_task_queue

            # Act
            result = await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)

            # Assert
            assert result == expected_task_queue
            mock_temporal_utils.assert_called_once_with(
                activity_instance._temporal_client,
                mock_activity_info,
            )

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_calls_correct_temporal_utils_method(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
        mock_activity_info: MagicMock,
    ) -> None:
        """Test that the correct TemporalUtils method is called with correct parameters."""
        # Arrange
        expected_task_queue = "test_queue"

        with (
            patch("awa.core.activities.get_parent_workflow_task_queue.activity.info", return_value=mock_activity_info),
            patch(
                "awa.core.activities.get_parent_workflow_task_queue.TemporalUtils.get_parent_workflow_task_queue_for_activity",
            ) as mock_temporal_utils,
        ):
            mock_temporal_utils.return_value = expected_task_queue

            # Act
            result = await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)

            # Assert
            assert result == expected_task_queue
            # Verify that the method was called exactly once
            mock_temporal_utils.assert_called_once()
            # Verify the arguments passed
            args, _kwargs = mock_temporal_utils.call_args
            assert len(args) == 2
            assert args[0] is activity_instance._temporal_client
            assert args[1] is mock_activity_info

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_uses_activity_info_correctly(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
    ) -> None:
        """Test that activity.info() is called and used correctly."""
        # Arrange
        expected_task_queue = "activity_info_test_queue"

        with (
            patch("awa.core.activities.get_parent_workflow_task_queue.activity.info") as mock_activity_info_func,
            patch(
                "awa.core.activities.get_parent_workflow_task_queue.TemporalUtils.get_parent_workflow_task_queue_for_activity",
            ) as mock_temporal_utils,
        ):
            # Create a mock activity info to return
            mock_info = MagicMock()
            mock_activity_info_func.return_value = mock_info
            mock_temporal_utils.return_value = expected_task_queue

            # Act
            result = await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)

            # Assert
            assert result == expected_task_queue
            # Verify activity.info() was called
            mock_activity_info_func.assert_called_once()
            # Verify TemporalUtils was called with the mock info
            mock_temporal_utils.assert_called_once_with(
                activity_instance._temporal_client,
                mock_info,
            )

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_multiple_calls(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
        mock_activity_info: MagicMock,
    ) -> None:
        """Test multiple calls to the activity method work correctly."""
        # Arrange
        expected_task_queues = ["queue1", "queue2", "queue3"]

        with (
            patch("awa.core.activities.get_parent_workflow_task_queue.activity.info", return_value=mock_activity_info),
            patch(
                "awa.core.activities.get_parent_workflow_task_queue.TemporalUtils.get_parent_workflow_task_queue_for_activity",
            ) as mock_temporal_utils,
        ):
            # Configure the mock to return different values on each call
            mock_temporal_utils.side_effect = expected_task_queues

            # Act & Assert
            for expected_queue in expected_task_queues:
                result = await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)
                assert result == expected_queue

            # Verify the method was called the expected number of times
            assert mock_temporal_utils.call_count == len(expected_task_queues)

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_with_none_return(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
        mock_activity_info: MagicMock,
    ) -> None:
        """Test behavior when TemporalUtils returns None."""
        # Arrange
        with (
            patch("awa.core.activities.get_parent_workflow_task_queue.activity.info", return_value=mock_activity_info),
            patch(
                "awa.core.activities.get_parent_workflow_task_queue.TemporalUtils.get_parent_workflow_task_queue_for_activity",
            ) as mock_temporal_utils,
        ):
            mock_temporal_utils.return_value = None

            # Act
            result = await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)

            # Assert
            assert result is None
            mock_temporal_utils.assert_called_once_with(
                activity_instance._temporal_client,
                mock_activity_info,
            )

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_integration_with_temporal_utils(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
        mock_activity_info: MagicMock,
    ) -> None:
        """Test integration with TemporalUtils without mocking the utility method."""
        # Arrange
        expected_task_queue = "integration_test_queue"

        # Create a mock workflow handle and workflow description
        mock_workflow_handle = AsyncMock(spec=WorkflowHandle)
        mock_workflow_description = MagicMock()
        mock_workflow_description.task_queue = expected_task_queue
        mock_workflow_description.parent_id = None  # No parent workflow
        mock_workflow_handle.describe.return_value = mock_workflow_description

        # Mock the client to return the workflow handle
        activity_instance._temporal_client.get_workflow_handle.return_value = mock_workflow_handle

        with patch("awa.core.activities.get_parent_workflow_task_queue.activity.info", return_value=mock_activity_info):
            # Act
            result = await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)

            # Assert
            assert result == expected_task_queue

            # Verify that the client was called with the correct workflow ID
            activity_instance._temporal_client.get_workflow_handle.assert_called_once_with(
                mock_activity_info.workflow_id,
            )

            # Verify that describe was called on the workflow handle
            mock_workflow_handle.describe.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_parent_workflow_task_queue_activity_with_nested_workflows(
        self,
        activity_env: ActivityEnvironment,
        activity_instance: GetParentWorkflowTaskQueueActivity,
        mock_activity_info: MagicMock,
    ) -> None:
        """Test with nested workflows to ensure the root parent task queue is returned."""
        # Arrange
        root_task_queue = "root_task_queue"

        # Create mock workflow descriptions for nested workflows
        child_workflow_desc = MagicMock()
        child_workflow_desc.task_queue = "child_task_queue"
        child_workflow_desc.parent_id = "parent_workflow_id"

        parent_workflow_desc = MagicMock()
        parent_workflow_desc.task_queue = root_task_queue
        parent_workflow_desc.parent_id = None  # This is the root

        # Create mock workflow handles
        child_workflow_handle = AsyncMock(spec=WorkflowHandle)
        child_workflow_handle.describe.return_value = child_workflow_desc

        parent_workflow_handle = AsyncMock(spec=WorkflowHandle)
        parent_workflow_handle.describe.return_value = parent_workflow_desc

        # Configure the client to return different handles for different workflow IDs
        def get_workflow_handle_side_effect(workflow_id: str) -> AsyncMock:
            if workflow_id == "parent_workflow_id":
                return parent_workflow_handle
            return child_workflow_handle

        activity_instance._temporal_client.get_workflow_handle.side_effect = get_workflow_handle_side_effect

        with patch("awa.core.activities.get_parent_workflow_task_queue.activity.info", return_value=mock_activity_info):
            # Act
            result = await activity_env.run(activity_instance.get_parent_workflow_task_queue_activity)

            # Assert
            assert result == root_task_queue

            # Verify that both workflow handles were queried
            assert activity_instance._temporal_client.get_workflow_handle.call_count == 2
            child_workflow_handle.describe.assert_called_once()
            parent_workflow_handle.describe.assert_called_once()

    def test_activity_method_callable(self) -> None:
        """Test that the activity method is callable."""
        # Arrange
        activity_instance = GetParentWorkflowTaskQueueActivity(MagicMock())

        # Act & Assert
        # The activity method should be callable
        assert callable(activity_instance.get_parent_workflow_task_queue_activity)

    def test_activity_method_is_async(self) -> None:
        """Test that the activity method is properly defined as async."""
        # Arrange
        activity_instance = GetParentWorkflowTaskQueueActivity(MagicMock())

        # Act & Assert
        import asyncio

        assert asyncio.iscoroutinefunction(activity_instance.get_parent_workflow_task_queue_activity)

    def test_activity_method_signature(self) -> None:
        """Test that the activity method has the correct signature."""
        # Arrange
        activity_instance = GetParentWorkflowTaskQueueActivity(MagicMock())

        # Act & Assert
        import inspect

        sig = inspect.signature(activity_instance.get_parent_workflow_task_queue_activity)

        # Method should have no parameters (except self)
        assert len(sig.parameters) == 0

        # Method should return a string
        assert sig.return_annotation is str

    def test_class_has_init_docstring(self) -> None:
        """Test that the class initialization method has proper docstring."""
        # Act & Assert
        assert GetParentWorkflowTaskQueueActivity.__init__.__doc__ is not None
        assert GetParentWorkflowTaskQueueActivity.get_parent_workflow_task_queue_activity.__doc__ is not None

        # Check that docstrings contain expected content
        init_doc = GetParentWorkflowTaskQueueActivity.__init__.__doc__
        assert "Initialize" in init_doc
        assert "temporal_client" in init_doc

        activity_doc = GetParentWorkflowTaskQueueActivity.get_parent_workflow_task_queue_activity.__doc__
        assert "task queue" in activity_doc
        assert "parent workflow" in activity_doc
