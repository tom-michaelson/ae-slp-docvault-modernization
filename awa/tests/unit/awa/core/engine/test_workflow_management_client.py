import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from awa.core.engine.workflow_management_client import WorkflowManagementClient
from awa.core.models.api import WorkflowRun, WorkflowRunStatus


class TestWorkflowManagementClient:
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_temporal_client = AsyncMock()
        self.client = WorkflowManagementClient(self.mock_temporal_client)

    @pytest.mark.asyncio
    async def test_terminate_all_workflows_with_running_workflows(self) -> None:
        # Create a mock workflow handle with an async terminate method
        class MockWorkflowHandle:
            async def terminate(self) -> None:
                pass

        mock_workflow_handle = MockWorkflowHandle()
        mock_workflow_handle.terminate = AsyncMock()
        # Set get_workflow_handle as a regular function returning the mock handle
        self.mock_temporal_client.get_workflow_handle = lambda _: mock_workflow_handle

        # Simulate one running workflow
        class MockWorkflow:
            id = "id"
            status = 1

        async def list_workflows_mock(query: str) -> AsyncGenerator[MockWorkflow, None]:
            assert query == 'ExecutionStatus = "Running"'
            yield MockWorkflow()

        self.mock_temporal_client.list_workflows = list_workflows_mock
        await self.client.terminate_all_workflows()
        mock_workflow_handle.terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_terminate_all_workflows_no_running_workflows(self) -> None:
        async def list_workflows_mock(query: str) -> AsyncGenerator[Any, None]:
            assert query == 'ExecutionStatus = "Running"'
            if False:
                yield  # This is just to make it an async generator

        self.mock_temporal_client.list_workflows = list_workflows_mock
        await self.client.terminate_all_workflows()  # Should not raise

    @pytest.mark.asyncio
    async def test_list_workflow_runs_with_end_time(self) -> None:
        with patch.object(self.client, "get_workflow_ui_link", new_callable=AsyncMock) as mock_get_workflow_ui_link:
            mock_get_workflow_ui_link.return_value = "mockurl:1234/workflow"

            class MockWorkflow:
                id = "id"
                status = 1
                workflow_type = "Mock Workflow"
                run_id = str(uuid.uuid4())
                duration = timedelta(seconds=30)
                close_time = datetime.now(UTC)
                execution_time = close_time - timedelta(seconds=30)
                parent_id = None

            async def list_workflows_mock() -> AsyncGenerator[MockWorkflow, None]:
                yield MockWorkflow()

            self.mock_temporal_client.list_workflows = list_workflows_mock
            runs = await self.client.list_workflow_runs()
            assert runs[0].type == "Mock Workflow"
            assert runs[0].status == WorkflowRunStatus.RUNNING
            assert runs[0].duration == str(timedelta(seconds=30))

    @pytest.mark.asyncio
    async def test_list_workflow_runs_with_no_end_time(self) -> None:
        with patch.object(self.client, "get_workflow_ui_link", new_callable=AsyncMock) as mock_get_workflow_ui_link:
            mock_get_workflow_ui_link.return_value = "mockurl:1234/workflow"

            class MockWorkflow:
                id = "id"
                status = 1
                workflow_type = "Mock Workflow"
                run_id = str(uuid.uuid4())
                close_time = None
                execution_time = datetime.now(UTC) - timedelta(seconds=30)
                parent_id = None

            async def list_workflows_mock() -> AsyncGenerator[MockWorkflow, None]:
                yield MockWorkflow()

            self.mock_temporal_client.list_workflows = list_workflows_mock
            runs = await self.client.list_workflow_runs()
            assert runs[0].type == "Mock Workflow"
            assert runs[0].status == WorkflowRunStatus.RUNNING
            # Check duration ignoring execution time
            assert str(timedelta(seconds=30)) in runs[0].duration

    @patch("awa.core.engine.workflow_management_client.EnvConfig.get_env_config")
    @pytest.mark.asyncio
    async def test_get_workflow_ui_link(self, mock_get_env_config: Mock) -> None:
        namespace = "default"
        host = "localhost"
        port = 8002

        self.mock_temporal_client.namespace = namespace
        mock_get_env_config().temporal_ui_host = host
        mock_get_env_config().temporal_ui_port = port

        workflow_id = "20250101_123456_12345"
        run_id = str(uuid.uuid4())

        ui_link = await self.client.get_workflow_ui_link(workflow_id, run_id)

        assert ui_link == f"http://{host}:{port}/namespaces/{namespace}/workflows/{workflow_id}/{run_id}"

    @pytest.mark.asyncio
    async def test_list_workflow_exclude_child_runs(self) -> None:
        with patch.object(self.client, "get_workflow_ui_link", new_callable=AsyncMock) as mock_get_workflow_ui_link:
            mock_get_workflow_ui_link.return_value = "mockurl:1234/workflow"

            class ParentMockWorkflow:
                id = "id"
                status = 1
                workflow_type = "Mock Workflow"
                run_id = str(uuid.uuid4())
                duration = timedelta(seconds=30)
                close_time = datetime.now(UTC)
                execution_time = close_time - timedelta(seconds=30)
                parent_id = None

            class ChildMockWorkflow:
                id = "id"
                status = 1
                workflow_type = "Mock Workflow"
                run_id = str(uuid.uuid4())
                duration = timedelta(seconds=30)
                close_time = datetime.now(UTC)
                execution_time = close_time - timedelta(seconds=30)
                parent_id = "id"

            async def list_workflows_mock() -> AsyncGenerator[ParentMockWorkflow | ChildMockWorkflow, None]:
                yield ParentMockWorkflow()
                yield ChildMockWorkflow()

            self.mock_temporal_client.list_workflows = list_workflows_mock
            runs = await self.client.list_workflow_runs()
            assert len(runs) == 1

    def test_sort_workflows_by_status(self) -> None:
        mock_workflow_list = [
            WorkflowRun(
                type="Workflow Failed",
                id="3",
                workflow_id="workflow-3",
                status=WorkflowRunStatus.FAILED,
                started=datetime.now(UTC) - timedelta(seconds=30),
                duration=str(timedelta(seconds=30)),
                monitor="",
            ),
            WorkflowRun(
                type="Workflow Running",
                id="1",
                workflow_id="workflow-1",
                status=WorkflowRunStatus.RUNNING,
                started=datetime.now(UTC) - timedelta(seconds=20),
                duration=str(timedelta(seconds=20)),
                monitor="",
            ),
            WorkflowRun(
                type="Workflow Completed",
                id="2",
                workflow_id="workflow-2",
                status=WorkflowRunStatus.COMPLETED,
                started=datetime.now(UTC) - timedelta(seconds=10),
                duration=str(timedelta(seconds=10)),
                monitor="",
            ),
        ]

        sorted_workflows = self.client.sort_workflows_by_status(mock_workflow_list, WorkflowRunStatus.RUNNING)

        assert sorted_workflows[0].id == "1"
        assert sorted_workflows[1].id == "2"
        assert sorted_workflows[2].id == "3"

    def test_round_seconds(self) -> None:
        # Test rounding functionality
        result = self.client._round_seconds(timedelta(seconds=30.7))
        assert result == timedelta(seconds=31)

        result = self.client._round_seconds(timedelta(seconds=30.3))
        assert result == timedelta(seconds=30)

        result = self.client._round_seconds(timedelta(seconds=30.5))
        assert result == timedelta(seconds=30)  # Python rounds to even

    @pytest.mark.asyncio
    async def test_get_workflow_run_found(self) -> None:
        """Test successful retrieval of a workflow run."""
        run_id = str(uuid.uuid4())
        workflow_id = f"workflow_{run_id}"

        # Create mock workflow
        class MockWorkflow:
            def __init__(self) -> None:
                self.id = workflow_id
                self.run_id = run_id
                self.parent_id = None  # Not a child workflow
                self.workflow_type = "TestWorkflow"
                self.status = 1  # Running
                self.execution_time = datetime.now(UTC) - timedelta(minutes=5)
                self.close_time = None  # Still running

        async def list_workflows_mock() -> AsyncGenerator[MockWorkflow, None]:
            yield MockWorkflow()

        self.mock_temporal_client.list_workflows = list_workflows_mock

        # Mock get_workflow_ui_link
        with patch.object(self.client, "get_workflow_ui_link", new_callable=AsyncMock) as mock_ui_link:
            mock_ui_link.return_value = f"https://temporal.example.com/workflows/{run_id}"

            result = await self.client.get_workflow_run(run_id)

        assert result is not None
        assert result.id == run_id
        assert result.type == "TestWorkflow"
        assert result.status == WorkflowRunStatus.RUNNING
        assert result.monitor == f"https://temporal.example.com/workflows/{run_id}"

    @pytest.mark.asyncio
    async def test_get_workflow_run_not_found(self) -> None:
        """Test get_workflow_run when workflow is not found."""
        run_id = str(uuid.uuid4())

        async def list_workflows_mock() -> AsyncGenerator[Any, None]:
            if False:
                yield  # Empty generator

        self.mock_temporal_client.list_workflows = list_workflows_mock

        result = await self.client.get_workflow_run(run_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_workflow_run_completed_workflow(self) -> None:
        """Test retrieval of a completed workflow run."""
        run_id = str(uuid.uuid4())
        workflow_id = f"workflow_{run_id}"
        start_time = datetime.now(UTC) - timedelta(hours=2)
        end_time = datetime.now(UTC) - timedelta(hours=1)

        class MockWorkflow:
            def __init__(self) -> None:
                self.id = workflow_id
                self.run_id = run_id
                self.parent_id = None
                self.workflow_type = "CompletedWorkflow"
                self.status = 2  # Completed
                self.execution_time = start_time
                self.close_time = end_time

        async def list_workflows_mock() -> AsyncGenerator[MockWorkflow, None]:
            yield MockWorkflow()

        self.mock_temporal_client.list_workflows = list_workflows_mock

        with patch.object(self.client, "get_workflow_ui_link", new_callable=AsyncMock) as mock_ui_link:
            mock_ui_link.return_value = f"https://temporal.example.com/workflows/{run_id}"

            result = await self.client.get_workflow_run(run_id)

        assert result is not None
        assert result.id == run_id
        assert result.type == "CompletedWorkflow"
        assert result.status == WorkflowRunStatus.COMPLETED
        assert result.started == start_time
        # Duration should be approximately 1 hour
        duration_seconds = (
            int(result.duration.split(":")[0]) * 3600
            + int(result.duration.split(":")[1]) * 60
            + int(result.duration.split(":")[2])
        )
        assert 3590 <= duration_seconds <= 3610  # Allow some rounding tolerance

    @pytest.mark.asyncio
    async def test_get_workflow_run_skips_child_workflows(self) -> None:
        """Test that child workflows are skipped."""
        run_id = str(uuid.uuid4())

        class MockChildWorkflow:
            def __init__(self) -> None:
                self.id = "child-workflow"
                self.run_id = run_id
                self.parent_id = "parent-workflow"  # This is a child
                self.workflow_type = "ChildWorkflow"
                self.status = 1
                self.execution_time = datetime.now(UTC)
                self.close_time = None

        class MockParentWorkflow:
            def __init__(self) -> None:
                self.id = "parent-workflow"
                self.run_id = "different-run-id"
                self.parent_id = None
                self.workflow_type = "ParentWorkflow"
                self.status = 1
                self.execution_time = datetime.now(UTC)
                self.close_time = None

        async def list_workflows_mock() -> AsyncGenerator:
            yield MockChildWorkflow()  # Child should be skipped
            yield MockParentWorkflow()  # Different run_id

        self.mock_temporal_client.list_workflows = list_workflows_mock

        result = await self.client.get_workflow_run(run_id)

        # Should not find the child workflow even though it has the matching run_id
        assert result is None
