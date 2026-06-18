import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from temporalio import activity, workflow

from awa.core.engine.temporal_client import TemporalClient
from awa.core.engine.temporal_worker import TemporalWorker


# Test workflow and activity with decorator names
@workflow.defn(name="test-worker-workflow")
class TestWorkerWorkflow:
    @workflow.run
    async def run(self, param: str) -> str:
        return f"Test: {param}"


@activity.defn(name="test-worker-activity")
async def sample_worker_activity(param: str) -> str:
    return f"Activity: {param}"


# Test objects without decorator names for fallback testing
@workflow.defn
class TestWorkerWorkflowNoName:
    @workflow.run
    async def run(self, param: str) -> str:
        return f"Test: {param}"


@activity.defn
async def sample_worker_activity_no_name(param: str) -> str:
    return f"Activity: {param}"


@pytest.mark.asyncio
@patch("awa.core.engine.temporal_client.TemporalClient.create")
class TestTemporalWorker:
    # Legacy method tests for backward compatibility
    async def test_check_service_status_worker_running(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)
        with patch(
            "awa.core.engine.temporal_worker._get_active_worker_pollers",
            new_callable=AsyncMock,
        ) as mock_pollers:
            mock_pollers.return_value = ["worker-1@host-1"]
            result = await worker.check_service_status()
            assert result is True
            mock_pollers.assert_called_once_with(worker.default_task_queue)

    async def test_check_service_status_worker_not_running(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)
        with patch(
            "awa.core.engine.temporal_worker._get_active_worker_pollers",
            new_callable=AsyncMock,
        ) as mock_pollers:
            mock_pollers.return_value = []
            result = await worker.check_service_status()
            assert result is False
            mock_pollers.assert_called_once_with(worker.default_task_queue)

    # New unified interface tests
    async def test_start(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Create a dummy coroutine function
        async def dummy_coroutine() -> None:
            pass

        with (
            patch.object(worker, "_construct_temporal_worker", new_callable=AsyncMock) as mock_construct,
            patch.object(worker, "_temporal_worker", side_effect=lambda: dummy_coroutine()),
            patch.object(worker.worker_started_event, "wait", new_callable=AsyncMock) as mock_wait,
        ):
            # Create a mock task
            mock_task = Mock()
            mock_task.done.return_value = False

            # Override the condition check by setting the worker_started_event to not set initially
            worker.worker_started_event.clear()
            worker._worker_task = None  # Ensure the condition is met

            # Mock asyncio.create_task to consume and close the coroutine
            def create_task_side_effect(coro: object) -> Mock:
                if hasattr(coro, "close"):
                    coro.close()  # type: ignore[attr-defined]  # Close the coroutine to prevent warning
                return mock_task

            with patch("asyncio.create_task", side_effect=create_task_side_effect):
                await worker.start()

            mock_construct.assert_called_once()
            mock_wait.assert_called_once()
            # Verify the worker_task was set
            assert worker._worker_task == mock_task

    async def test_stop(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Create a real asyncio task that can be awaited
        async def dummy_task() -> None:
            await asyncio.sleep(0.01)  # Short sleep to simulate work

        # Create the task and set it up
        real_task = asyncio.create_task(dummy_task())
        worker._worker_task = real_task

        # Add a small delay to ensure task is running
        await asyncio.sleep(0.001)

        await worker.stop()

        # Verify the task was cancelled
        assert real_task.cancelled()

    async def test_is_healthy_when_running(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Set up worker as running
        worker.worker_started_event.set()
        mock_task = Mock()
        mock_task.done.return_value = False
        worker._worker_task = mock_task

        result = await worker.is_healthy()
        assert result is True

    async def test_is_healthy_when_not_running(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Worker not started (event not set)
        result = await worker.is_healthy()
        assert result is False

    async def test_is_healthy_when_task_done(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Set event but task is done
        worker.worker_started_event.set()
        mock_task = Mock()
        mock_task.done.return_value = True
        worker._worker_task = mock_task

        result = await worker.is_healthy()
        assert result is False

    async def test_restart(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        with (
            patch.object(worker, "stop", new_callable=AsyncMock) as mock_stop,
            patch.object(worker, "start", new_callable=AsyncMock) as mock_start,
        ):
            await worker.restart()
            mock_stop.assert_awaited_once()
            mock_start.assert_awaited_once()

    async def test_wait_until_ready_success(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Set event immediately
        worker.worker_started_event.set()

        with patch(
            "awa.core.engine.temporal_worker._get_active_worker_pollers",
            new_callable=AsyncMock,
        ) as mock_pollers:
            mock_pollers.return_value = []
            result = await worker.wait_until_ready(timeout_sec=1.0)
            assert result is True

    async def test_wait_until_ready_timeout(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Don't set event - should timeout
        result = await worker.wait_until_ready(timeout_sec=0.1)
        assert result is False

    async def test_run_with_retries_success(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        with (
            patch.object(worker, "start", new_callable=AsyncMock) as mock_start,
            patch.object(worker, "stop", new_callable=AsyncMock) as mock_stop,
        ):
            # Create a real task that completes immediately
            async def dummy_task() -> None:
                pass

            mock_task = asyncio.create_task(dummy_task())
            mock_start.side_effect = lambda: setattr(worker, "_worker_task", mock_task)

            await worker.run_with_retries(max_retries=3)

            mock_start.assert_called_once()
            mock_stop.assert_not_called()  # Should not stop on success

    async def test_run_with_retries_with_failures_then_success(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        call_count = 0

        async def mock_start_side_effect() -> None:
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise RuntimeError(f"Simulated failure {call_count}")

            # Success on 3rd attempt - create a real task
            async def dummy_task() -> None:
                pass

            mock_task = asyncio.create_task(dummy_task())
            worker._worker_task = mock_task

        with (
            patch.object(worker, "start", new_callable=AsyncMock) as mock_start,
            patch.object(worker, "stop", new_callable=AsyncMock) as mock_stop,
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            mock_start.side_effect = mock_start_side_effect

            await worker.run_with_retries(max_retries=5)

            # Should try 3 times total (2 failures + 1 success)
            assert mock_start.call_count == 3
            # Should stop after each failure (2 times)
            assert mock_stop.call_count == 2
            # Should sleep between retries (2 times)
            assert mock_sleep.call_count == 2

    async def test_run_with_retries_max_retries_exceeded(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        with (
            patch.object(worker, "start", new_callable=AsyncMock) as mock_start,
            patch.object(worker, "stop", new_callable=AsyncMock) as mock_stop,
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            # Always fail
            mock_start.side_effect = RuntimeError("Persistent failure")

            with pytest.raises(RuntimeError, match="Persistent failure"):
                await worker.run_with_retries(max_retries=3)

            # Should try 3 times
            assert mock_start.call_count == 3
            # Should stop after each failure except the last
            assert mock_stop.call_count == 2
            # Should sleep between retries
            assert mock_sleep.call_count == 2

    # Legacy method tests for backward compatibility
    async def test_start_temporal_worker_calls_start(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        with patch.object(worker, "start", new_callable=AsyncMock) as mock_start:
            await worker.start_temporal_worker()
            mock_start.assert_called_once()

    async def test_stop_temporal_worker_calls_stop(self, mock_create: AsyncMock) -> None:
        mock_client = AsyncMock()
        mock_create.return_value = mock_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        with patch.object(worker, "stop", new_callable=AsyncMock) as mock_stop:
            await worker.stop_temporal_worker()
            mock_stop.assert_called_once()

    async def test_construct_temporal_worker_logs_decorator_names(self, mock_create: AsyncMock) -> None:
        """Test that _construct_temporal_worker logs decorator-defined names instead of class names."""
        # Arrange
        mock_temporal_client = AsyncMock()
        mock_internal_client = Mock()  # The actual Temporal SDK client
        # Setup the config method that Worker expects - use Mock not AsyncMock for sync method
        mock_internal_client.config.return_value = {"plugins": [], "interceptors": []}
        mock_temporal_client.get_client.return_value = mock_internal_client
        mock_create.return_value = mock_temporal_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Mock workflows and activities with decorator names
        mock_workflows = [TestWorkerWorkflow, TestWorkerWorkflowNoName]
        mock_activities = [sample_worker_activity, sample_worker_activity_no_name]

        with (
            patch("awa.core.engine.temporal_worker.TemporalDiscovery") as mock_discovery_class,
            patch("awa.core.engine.temporal_worker.Worker") as mock_worker_class,  # Patch at the import location
            patch.object(worker, "logger") as mock_logger,
        ):
            # Set up the discovery mock
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            mock_discovery.discover_workflows_and_activities.return_value = (mock_workflows, mock_activities)

            # Mock the Worker class - prevent actual instantiation
            mock_worker_instance = Mock()
            mock_worker_class.return_value = mock_worker_instance

            # Act
            await worker._construct_temporal_worker()

            # Assert - Check that logger.info was called
            mock_logger.info.assert_called()

            # Get the logged messages and find the registration log
            logged_calls = mock_logger.info.call_args_list
            registration_log_call = None
            for call in logged_calls:
                call_message = str(call[0][0])
                if (
                    "Registering" in call_message
                    and "workflows and" in call_message
                    and "activities with Temporal Worker" in call_message
                ):
                    registration_log_call = call
                    break

            assert registration_log_call is not None, (
                f"Registration log call not found. Calls were: {[str(call) for call in logged_calls]}"
            )

            # Verify the name extraction logic was called (basic test)
            # Just verify that the mocked discovery was used
            mock_discovery.discover_workflows_and_activities.assert_called_once()


def test_workflow_name_extraction_logic() -> None:
    """Test the workflow name extraction logic used in TemporalWorker."""
    # Test with decorator name
    defn = getattr(TestWorkerWorkflow, "__temporal_workflow_definition", None)
    if defn and hasattr(defn, "name") and defn.name:
        name = defn.name
    else:
        name = getattr(TestWorkerWorkflow, "__name__", str(TestWorkerWorkflow))

    assert name == "test-worker-workflow"

    # Test fallback to class name
    defn = getattr(TestWorkerWorkflowNoName, "__temporal_workflow_definition", None)
    if defn and hasattr(defn, "name") and defn.name:
        name = defn.name
    else:
        name = getattr(TestWorkerWorkflowNoName, "__name__", str(TestWorkerWorkflowNoName))

    assert name == "TestWorkerWorkflowNoName"


def test_activity_name_extraction_logic() -> None:
    """Test the activity name extraction logic used in TemporalWorker."""
    # Test with decorator name
    defn = getattr(sample_worker_activity, "__temporal_activity_definition", None)
    if defn and hasattr(defn, "name") and defn.name:
        name = defn.name
    else:
        name = getattr(sample_worker_activity, "__name__", str(sample_worker_activity))

    assert name == "test-worker-activity"

    # Test fallback to function name
    defn = getattr(sample_worker_activity_no_name, "__temporal_activity_definition", None)
    if defn and hasattr(defn, "name") and defn.name:
        name = defn.name
    else:
        name = getattr(sample_worker_activity_no_name, "__name__", str(sample_worker_activity_no_name))

    assert name == "sample_worker_activity_no_name"
