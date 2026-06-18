"""Integration tests for MCP workflow lifecycle.

This module tests the complete MCP workflow functionality including:
- Blocking workflow execution (execute_workflow renamed tool)
- Non-blocking workflow lifecycle (start -> status -> result)
- Concurrent workflow management
- Error handling scenarios
- Memory management and cleanup
- Backward compatibility
"""

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio.api.enums.v1 import WorkflowExecutionStatus
from temporalio.client import WorkflowHandle

from awa.core.cli.service_manager import ServiceManager
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.mcp.mcp_server import (
    StartWorkflowResponse,
    WorkflowExecutionResult,
    WorkflowNotCompletedError,
    WorkflowNotFoundError,
    WorkflowResultResponse,
    WorkflowStatusResponse,
    _active_workflow_handles,
    _cleanup_completed_workflow,
    _get_workflow_result,
    _get_workflow_status,
    _start_workflow,
    _store_workflow_handle,
    _workflow_metadata,
    execute_workflow,
)
from awa.core.models.api import WorkflowDefinition
from awa.core.workflows.hello_world import HelloWorldInput
from tests.workflow.utils.temporal_utils import (
    connect_to_temporal,
    wait_for_temporal_services,
)

logger = get_logger(LoggerComponent.TEST)


@pytest.fixture
async def real_service_manager() -> AsyncGenerator[ServiceManager, None]:
    """Create a real ServiceManager for integration tests."""
    service_manager = ServiceManager()

    # Start services if not already running
    try:
        await wait_for_temporal_services()
        yield service_manager
    finally:
        # Cleanup if needed (but don't stop services in CI)
        pass


@pytest.fixture
async def real_temporal_client() -> AsyncGenerator[Any, None]:
    """Create a real Temporal client connected to services."""
    await wait_for_temporal_services()
    client = await connect_to_temporal()
    return client


@pytest.fixture
def sample_workflow_definitions() -> list[WorkflowDefinition]:
    """Provide sample workflow definitions for testing."""
    return [
        WorkflowDefinition(
            name="awa-hello-world",
            display_name="Hello World Workflow",
            description="A simple test workflow",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to greet"},
                },
                "required": ["name"],
            },
        ),
        WorkflowDefinition(
            name="test-concurrent-workflow",
            display_name="Concurrent Test Workflow",
            description="A workflow for testing concurrent execution",
            input_schema={
                "type": "object",
                "properties": {
                    "delay_seconds": {"type": "integer", "description": "Delay time"},
                },
            },
        ),
    ]


@pytest.fixture
async def integration_test_context() -> AsyncGenerator[None, None]:
    """Create a test context for integration tests."""
    # Clear any existing workflow storage
    _active_workflow_handles.clear()
    _workflow_metadata.clear()

    yield

    # Cleanup after test
    _active_workflow_handles.clear()
    _workflow_metadata.clear()


class TestBlockingWorkflowIntegration:
    """Test blocking workflow execution integration."""

    @pytest.mark.asyncio
    async def test_execute_workflow_blocking_mode(
        self,
        real_service_manager: ServiceManager,
        real_temporal_client: Any,  # noqa: ARG002, ANN401
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test execute_workflow with real Temporal workflow."""
        # Create workflow input
        workflow_input = HelloWorldInput(name="Integration Test")

        # Execute workflow in blocking mode
        result = await execute_workflow(
            workflow_name="awa-hello-world",
            workflow_input=workflow_input,
            service_manager=real_service_manager,
        )

        # Verify result structure
        assert isinstance(result, WorkflowExecutionResult)
        assert result["status"] == "success"
        assert "Integration Test" in str(result["result"])

    @pytest.mark.asyncio
    async def test_backward_compatibility_execute_workflow(
        self,
        real_service_manager: ServiceManager,
        real_temporal_client: Any,  # noqa: ARG002, ANN401
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test that execute_workflow maintains backward compatibility."""
        # Test with simple input
        workflow_input = {"name": "Backward Compat Test"}

        # Execute workflow using dict input (backward compatible)
        result = await execute_workflow(
            workflow_name="awa-hello-world",
            workflow_input=workflow_input,
            service_manager=real_service_manager,
        )

        # Verify backward compatible behavior
        assert result["status"] == "success"
        assert "Backward Compat Test" in str(result["result"])

    @pytest.mark.asyncio
    async def test_execute_workflow_with_failure(
        self,
        real_service_manager: ServiceManager,
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test execute_workflow handles workflow failures properly."""
        # Create input that will cause workflow to fail
        with patch("awa.core.mcp.mcp_server.WorkflowManagementClient") as MockClient:  # noqa: N806
            mock_client = MockClient.return_value
            mock_client.execute_workflow = AsyncMock(side_effect=Exception("Workflow failed"))

            result = await execute_workflow(
                workflow_name="failing-workflow",
                workflow_input={"fail": True},
                service_manager=real_service_manager,
            )

            assert result["status"] == "failed"
            assert "Workflow failed" in str(result["result"])


class TestNonBlockingWorkflowIntegration:
    """Test non-blocking workflow execution integration."""

    @pytest.mark.asyncio
    async def test_complete_lifecycle_start_status_result(
        self,
        real_service_manager: ServiceManager,
        real_temporal_client: Any,  # noqa: ARG002, ANN401
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test complete lifecycle: start -> status -> result."""
        # Start workflow
        workflow_input = HelloWorldInput(name="Lifecycle Test")
        start_response = await _start_workflow(
            workflow_name="awa-hello-world",
            workflow_input=workflow_input,
            service_manager=real_service_manager,
        )

        # Verify start response
        assert isinstance(start_response, StartWorkflowResponse)
        assert start_response["status"] == "RUNNING"
        assert "workflow_id" in start_response
        assert "run_id" in start_response
        assert "temporal_ui_link" in start_response

        workflow_id = start_response["workflow_id"]

        # Check status while running or after completion
        status_response = await _get_workflow_status(workflow_id)
        assert isinstance(status_response, WorkflowStatusResponse)
        assert status_response["workflow_id"] == workflow_id
        assert status_response["status"] in ["RUNNING", "COMPLETED"]

        # Wait for completion if still running
        max_wait = 10  # seconds
        start_time = time.time()
        while status_response["status"] == "RUNNING" and (time.time() - start_time) < max_wait:
            await asyncio.sleep(0.5)
            status_response = await _get_workflow_status(workflow_id)

        # Get result after completion
        if status_response["status"] == "COMPLETED":
            result_response = await _get_workflow_result(workflow_id)
            assert isinstance(result_response, WorkflowResultResponse)
            assert result_response["workflow_id"] == workflow_id
            assert result_response["status"] == "COMPLETED"
            assert "result" in result_response
            assert "Lifecycle Test" in str(result_response["result"])

    @pytest.mark.asyncio
    async def test_workflow_handle_storage_and_cleanup(
        self,
        real_service_manager: ServiceManager,
        real_temporal_client: Any,  # noqa: ARG002, ANN401
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test that workflow handles are properly stored and cleaned up."""
        # Start a workflow
        workflow_input = HelloWorldInput(name="Storage Test")
        start_response = await _start_workflow(
            workflow_name="awa-hello-world",
            workflow_input=workflow_input,
            service_manager=real_service_manager,
        )

        workflow_id = start_response["workflow_id"]

        # Verify handle is stored
        assert workflow_id in _active_workflow_handles
        assert workflow_id in _workflow_metadata

        # Wait for completion and get result
        max_wait = 10
        start_time = time.time()
        while (time.time() - start_time) < max_wait:
            try:
                status = await _get_workflow_status(workflow_id)
                if status["status"] == "COMPLETED":
                    break
            except Exception:  # noqa: S110, BLE001
                pass
            await asyncio.sleep(0.5)

        # Get result (should trigger cleanup)
        result = await _get_workflow_result(workflow_id)
        assert result["status"] == "COMPLETED"

        # Verify cleanup happened
        assert workflow_id not in _active_workflow_handles
        assert workflow_id not in _workflow_metadata

    @pytest.mark.asyncio
    async def test_get_result_before_completion_error(
        self,
        real_service_manager: ServiceManager,  # noqa: ARG002
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test that getting result before completion raises appropriate error."""
        # Create a mock handle that's still running
        mock_handle = MagicMock(spec=WorkflowHandle)
        mock_handle.describe = AsyncMock(
            return_value=MagicMock(
                status=WorkflowExecutionStatus.RUNNING,
                close_time=None,
            ),
        )

        workflow_id = f"test-{uuid.uuid4().hex[:8]}"
        await _store_workflow_handle(
            workflow_id,
            mock_handle,
            {"started_at": datetime.now(UTC).isoformat()},
        )

        # Try to get result while running
        with pytest.raises(WorkflowNotCompletedError) as exc_info:
            await _get_workflow_result(workflow_id)

        assert "still running" in str(exc_info.value).lower()


class TestConcurrentWorkflowIntegration:
    """Test concurrent workflow handling in real environment."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_workflows(
        self,
        real_service_manager: ServiceManager,
        real_temporal_client: Any,  # noqa: ARG002, ANN401
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test running multiple workflows concurrently."""
        num_workflows = 3
        workflow_ids = []

        # Start multiple workflows concurrently
        tasks = []
        for i in range(num_workflows):
            workflow_input = HelloWorldInput(name=f"Concurrent Test {i}")
            task = _start_workflow(
                workflow_name="awa-hello-world",
                workflow_input=workflow_input,
                service_manager=real_service_manager,
            )
            tasks.append(task)

        # Wait for all to start
        start_responses = await asyncio.gather(*tasks)

        # Collect workflow IDs
        for response in start_responses:
            assert response["status"] == "RUNNING"
            workflow_ids.append(response["workflow_id"])

        # Verify all are tracked
        for wf_id in workflow_ids:
            assert wf_id in _active_workflow_handles

        # Check status of all workflows
        status_tasks = [_get_workflow_status(wf_id) for wf_id in workflow_ids]
        status_responses = await asyncio.gather(*status_tasks)

        for status in status_responses:
            assert status["status"] in ["RUNNING", "COMPLETED"]

        # Wait for all to complete and get results
        max_wait = 15
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            all_completed = True
            for wf_id in workflow_ids:
                try:
                    status = await _get_workflow_status(wf_id)
                    if status["status"] != "COMPLETED":
                        all_completed = False
                        break
                except Exception:  # noqa: BLE001
                    all_completed = False
                    break

            if all_completed:
                break
            await asyncio.sleep(0.5)

        # Get all results
        result_tasks = [_get_workflow_result(wf_id) for wf_id in workflow_ids]
        results = await asyncio.gather(*result_tasks)

        # Verify all completed successfully
        for i, result in enumerate(results):
            assert result["status"] == "COMPLETED"
            assert f"Concurrent Test {i}" in str(result["result"])

    @pytest.mark.asyncio
    async def test_mixed_blocking_nonblocking_usage(
        self,
        real_service_manager: ServiceManager,
        real_temporal_client: Any,  # noqa: ARG002, ANN401
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test using both blocking and non-blocking modes together."""
        # Start a non-blocking workflow
        nb_input = HelloWorldInput(name="Non-blocking Test")
        nb_response = await _start_workflow(
            workflow_name="awa-hello-world",
            workflow_input=nb_input,
            service_manager=real_service_manager,
        )
        nb_workflow_id = nb_response["workflow_id"]

        # Execute a blocking workflow while the other is running
        blocking_input = HelloWorldInput(name="Blocking Test")
        blocking_result = await execute_workflow(
            workflow_name="awa-hello-world",
            workflow_input=blocking_input,
            service_manager=real_service_manager,
        )

        # Verify blocking result
        assert blocking_result["status"] == "success"
        assert "Blocking Test" in str(blocking_result["result"])

        # Check status and get result of non-blocking workflow
        max_wait = 10
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            status = await _get_workflow_status(nb_workflow_id)
            if status["status"] == "COMPLETED":
                break
            await asyncio.sleep(0.5)

        nb_result = await _get_workflow_result(nb_workflow_id)
        assert nb_result["status"] == "COMPLETED"
        assert "Non-blocking Test" in str(nb_result["result"])


class TestRealWorldErrorScenarios:
    """Test error handling with real services."""

    @pytest.mark.asyncio
    async def test_workflow_not_found_error(
        self,
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test handling of non-existent workflow ID."""
        fake_workflow_id = f"non-existent-{uuid.uuid4().hex}"

        # Try to get status of non-existent workflow
        with pytest.raises(WorkflowNotFoundError) as exc_info:
            await _get_workflow_status(fake_workflow_id)

        assert "not found" in str(exc_info.value).lower()

        # Try to get result of non-existent workflow
        with pytest.raises(WorkflowNotFoundError) as exc_info:
            await _get_workflow_result(fake_workflow_id)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_workflow_failure_handling(
        self,
        real_service_manager: ServiceManager,
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test handling of workflow that fails during execution."""
        # Create a mock workflow that will fail
        with patch("awa.core.engine.workflow_management_client.WorkflowManagementClient") as MockClient:  # noqa: N806
            mock_mgmt_client = MockClient.return_value

            # Mock a workflow that starts successfully but fails during execution
            mock_handle = MagicMock(spec=WorkflowHandle)
            mock_handle.id = f"test-fail-{uuid.uuid4().hex[:8]}"
            mock_handle.run_id = f"run-{uuid.uuid4().hex[:8]}"
            mock_handle.result = AsyncMock(side_effect=Exception("Workflow execution failed"))
            mock_handle.describe = AsyncMock(
                return_value=MagicMock(
                    status=WorkflowExecutionStatus.FAILED,
                    close_time=datetime.now(UTC),
                    execution_time=datetime.now(UTC),
                    parent_id=None,
                ),
            )

            mock_mgmt_client.start_workflow = AsyncMock(return_value=mock_handle)

            # Start the workflow
            start_response = await _start_workflow(
                workflow_name="test-fail-workflow",
                workflow_input={"should_fail": True},
                service_manager=real_service_manager,
            )

            workflow_id = start_response["workflow_id"]

            # Store the mock handle
            await _store_workflow_handle(
                workflow_id,
                mock_handle,
                {"started_at": datetime.now(UTC).isoformat()},
            )

            # Get result of failed workflow
            result = await _get_workflow_result(workflow_id)
            assert result["status"] == "FAILED"
            assert "error" in result
            assert "Workflow execution failed" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_invalidation_scenario(
        self,
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test scenarios where workflow handle becomes invalid."""
        # Create a mock handle that becomes invalid
        mock_handle = MagicMock(spec=WorkflowHandle)
        mock_handle.describe = AsyncMock(side_effect=Exception("Handle no longer valid"))

        workflow_id = f"invalid-{uuid.uuid4().hex[:8]}"
        await _store_workflow_handle(
            workflow_id,
            mock_handle,
            {"started_at": datetime.now(UTC).isoformat()},
        )

        # Try to get status with invalid handle
        with pytest.raises(Exception) as exc_info:
            await _get_workflow_status(workflow_id)

        assert "Handle no longer valid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_service_interruption_recovery(
        self,
        real_service_manager: ServiceManager,
        real_temporal_client: Any,  # noqa: ARG002, ANN401
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test recovery from temporary service interruptions."""
        # Start a real workflow
        workflow_input = HelloWorldInput(name="Interruption Test")
        start_response = await _start_workflow(
            workflow_name="awa-hello-world",
            workflow_input=workflow_input,
            service_manager=real_service_manager,
        )

        workflow_id = start_response["workflow_id"]

        # Simulate temporary loss of handle (but workflow still exists in Temporal)
        original_handle = _active_workflow_handles[workflow_id]
        del _active_workflow_handles[workflow_id]

        # Status check should fail when handle is missing
        with pytest.raises(WorkflowNotFoundError):
            await _get_workflow_status(workflow_id)

        # Restore handle and verify recovery
        _active_workflow_handles[workflow_id] = original_handle

        # Should work again
        status = await _get_workflow_status(workflow_id)
        assert status["workflow_id"] == workflow_id
        assert status["status"] in ["RUNNING", "COMPLETED"]


class TestMemoryAndCleanupIntegration:
    """Test memory management in real environment."""

    @pytest.mark.asyncio
    async def test_handle_storage_memory_usage(
        self,
        real_service_manager: ServiceManager,
        real_temporal_client: Any,  # noqa: ARG002, ANN401
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test that handle storage doesn't leak memory."""
        initial_count = len(_active_workflow_handles)

        # Start multiple workflows
        num_workflows = 5
        workflow_ids = []

        for i in range(num_workflows):
            workflow_input = HelloWorldInput(name=f"Memory Test {i}")
            response = await _start_workflow(
                workflow_name="awa-hello-world",
                workflow_input=workflow_input,
                service_manager=real_service_manager,
            )
            workflow_ids.append(response["workflow_id"])

        # Verify all are stored
        assert len(_active_workflow_handles) == initial_count + num_workflows

        # Wait for completion and get results (triggering cleanup)
        for wf_id in workflow_ids:
            # Wait for completion
            max_wait = 10
            start_time = time.time()
            while (time.time() - start_time) < max_wait:
                try:
                    status = await _get_workflow_status(wf_id)
                    if status["status"] == "COMPLETED":
                        break
                except Exception:  # noqa: S110, BLE001
                    pass
                await asyncio.sleep(0.5)

            # Get result (triggers cleanup)
            try:
                await _get_workflow_result(wf_id)
            except Exception:  # noqa: BLE001
                # May fail if workflow didn't complete, but cleanup should still happen
                await _cleanup_completed_workflow(wf_id)

        # Verify all cleaned up
        assert len(_active_workflow_handles) == initial_count

    @pytest.mark.asyncio
    async def test_long_running_workflow_cleanup(
        self,
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test cleanup of long-running workflows."""
        # Create mock long-running workflow
        mock_handle = MagicMock(spec=WorkflowHandle)
        mock_handle.describe = AsyncMock(
            return_value=MagicMock(
                status=WorkflowExecutionStatus.RUNNING,
                close_time=None,
                execution_time=datetime.now(UTC),
                parent_id=None,
            ),
        )

        workflow_id = f"long-running-{uuid.uuid4().hex[:8]}"
        metadata = {
            "started_at": datetime.now(UTC).isoformat(),
            "workflow_name": "long-running-test",
        }

        await _store_workflow_handle(workflow_id, mock_handle, metadata)

        # Verify stored
        assert workflow_id in _active_workflow_handles
        assert workflow_id in _workflow_metadata

        # Manually trigger cleanup
        await _cleanup_completed_workflow(workflow_id)

        # Verify cleaned up
        assert workflow_id not in _active_workflow_handles
        assert workflow_id not in _workflow_metadata

    @pytest.mark.asyncio
    async def test_metadata_consistency(
        self,
        real_service_manager: ServiceManager,
        real_temporal_client: Any,  # noqa: ARG002, ANN401
        integration_test_context: None,  # noqa: ARG002
    ) -> None:
        """Test that metadata remains consistent throughout workflow lifecycle."""
        # Start a workflow
        workflow_input = HelloWorldInput(name="Metadata Test")
        start_response = await _start_workflow(
            workflow_name="awa-hello-world",
            workflow_input=workflow_input,
            service_manager=real_service_manager,
        )

        workflow_id = start_response["workflow_id"]

        # Verify initial metadata
        assert workflow_id in _workflow_metadata
        initial_metadata = _workflow_metadata[workflow_id]
        assert "started_at" in initial_metadata
        assert "workflow_name" in initial_metadata

        # Check metadata remains consistent during execution
        status = await _get_workflow_status(workflow_id)
        assert workflow_id in _workflow_metadata
        assert _workflow_metadata[workflow_id] == initial_metadata

        # Wait for completion
        max_wait = 10
        start_time = time.time()
        while (time.time() - start_time) < max_wait:
            status = await _get_workflow_status(workflow_id)
            if status["status"] == "COMPLETED":
                break
            await asyncio.sleep(0.5)

        # Get result (triggers cleanup)
        result = await _get_workflow_result(workflow_id)
        assert result["status"] == "COMPLETED"

        # Verify metadata cleaned up
        assert workflow_id not in _workflow_metadata


# Test helper functions
async def create_test_workflow_input(test_name: str) -> HelloWorldInput:
    """Create a test workflow input with unique identifier."""
    return HelloWorldInput(name=f"{test_name}-{uuid.uuid4().hex[:8]}")


async def wait_for_workflow_completion(
    workflow_id: str,
    max_wait_seconds: int = 10,
) -> WorkflowStatusResponse:
    """Wait for a workflow to complete and return final status."""
    start_time = time.time()

    while (time.time() - start_time) < max_wait_seconds:
        try:
            status = await _get_workflow_status(workflow_id)
            if status["status"] in ["COMPLETED", "FAILED", "CANCELLED", "TERMINATED"]:
                return status
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Error checking workflow status: {e}")

        await asyncio.sleep(0.5)

    # Return last known status
    return await _get_workflow_status(workflow_id)


# Integration with pytest markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.workflow,
    pytest.mark.mcp,
]
