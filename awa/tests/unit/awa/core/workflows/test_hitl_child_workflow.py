"""Unit tests for HITL child workflow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from awa.core.models.hitl import HITLInput, HITLOutput, HITLResponse
from awa.core.workflows.hitl_child_workflow import HITLChildWorkflow


class TestHITLChildWorkflow:
    """Test the HITL child workflow functionality."""

    def test_initial_state(self) -> None:
        wf = HITLChildWorkflow()
        assert wf.response_received is False
        assert wf.response is None
        assert wf.context is None
        assert wf.chat_history == []

    @pytest.mark.asyncio
    @patch("awa.core.workflows.hitl_child_workflow.workflow")
    async def test_blocking_with_immediate_response(self, mock_workflow: AsyncMock) -> None:
        wf = HITLChildWorkflow()
        mock_workflow.wait_condition = AsyncMock(return_value=None)

        # Mock the asyncio module - create a proper mock task and close coroutines
        def close_coroutine_and_return_task(coro: object) -> MagicMock:
            if hasattr(coro, "close"):
                coro.close()
            task = MagicMock()
            task.cancel = MagicMock()
            return task

        mock_workflow.asyncio.create_task = MagicMock(side_effect=close_coroutine_and_return_task)
        mock_workflow.sleep = AsyncMock()
        mock_workflow.info = AsyncMock(return_value=AsyncMock(workflow_id="test-workflow-id"))
        mock_workflow.logger = AsyncMock()
        wf.response_received = True
        wf.response = HITLResponse(data={"approved": True}, message="Done")
        input_data = HITLInput(
            title="Approval",
            description="Please approve",
            markdown="# Approve",
            input_schema={"type": "object"},
        )
        result = await wf.run(input_data)
        assert isinstance(result, HITLOutput)
        assert result.timed_out is False
        assert result.response is not None
        assert result.response.data["approved"] is True

    @pytest.mark.asyncio
    @patch("awa.core.workflows.hitl_child_workflow.workflow")
    async def test_non_blocking(self, mock_workflow: AsyncMock) -> None:
        wf = HITLChildWorkflow()

        # Mock the asyncio module - create a proper mock task and close coroutines
        def close_coroutine_and_return_task(coro: object) -> MagicMock:
            if hasattr(coro, "close"):
                coro.close()
            task = MagicMock()
            task.cancel = MagicMock()
            return task

        mock_workflow.asyncio.create_task = MagicMock(side_effect=close_coroutine_and_return_task)
        mock_workflow.sleep = AsyncMock()
        mock_workflow.info = AsyncMock(return_value=AsyncMock(workflow_id="test-workflow-id"))
        mock_workflow.logger = AsyncMock()
        input_data = HITLInput(
            title="NB",
            description="Non blocking",
            markdown="# NB",
            input_schema={"type": "object"},
            non_blocking=True,
        )
        result = await wf.run(input_data)
        assert result.timed_out is False
        assert result.response is None
        mock_workflow.wait_condition.assert_not_called()

    @pytest.mark.asyncio
    @patch("awa.core.workflows.hitl_child_workflow.workflow")
    async def test_timeout(self, mock_workflow: AsyncMock) -> None:
        wf = HITLChildWorkflow()

        # Mock the asyncio module - create a proper mock task and close coroutines
        def close_coroutine_and_return_task(coro: object) -> MagicMock:
            if hasattr(coro, "close"):
                coro.close()
            task = MagicMock()
            task.cancel = MagicMock()
            return task

        mock_workflow.asyncio.create_task = MagicMock(side_effect=close_coroutine_and_return_task)
        mock_workflow.sleep = AsyncMock()
        mock_workflow.info = AsyncMock(return_value=AsyncMock(workflow_id="test-workflow-id"))
        mock_workflow.logger = AsyncMock()
        input_data = HITLInput(
            title="Timeout",
            description="Will timeout",
            markdown="# Timeout",
            input_schema={"type": "object"},
            timeout_seconds=5,
        )
        mock_workflow.wait_condition = AsyncMock(side_effect=TimeoutError())
        result = await wf.run(input_data)
        assert result.timed_out is True
        assert result.response is None

    @pytest.mark.asyncio
    @patch("awa.core.workflows.hitl_child_workflow.workflow")
    async def test_indefinite_wait(self, mock_workflow: AsyncMock) -> None:
        wf = HITLChildWorkflow()

        # Mock the asyncio module - create a proper mock task and close coroutines
        def close_coroutine_and_return_task(coro: object) -> MagicMock:
            if hasattr(coro, "close"):
                coro.close()
            task = MagicMock()
            task.cancel = MagicMock()
            return task

        mock_workflow.asyncio.create_task = MagicMock(side_effect=close_coroutine_and_return_task)
        mock_workflow.sleep = AsyncMock()
        mock_workflow.info = AsyncMock(return_value=AsyncMock(workflow_id="test-workflow-id"))
        mock_workflow.logger = AsyncMock()

        input_data = HITLInput(
            title="Indef",
            description="Wait",
            markdown="# Wait",
            input_schema={"type": "object"},
        )

        # Mock wait_condition to set response_received after being called
        async def mock_wait_condition(_condition: object, **_kwargs: object) -> None:
            wf.response_received = True

        mock_workflow.wait_condition = AsyncMock(side_effect=mock_wait_condition)
        result = await wf.run(input_data)
        assert result.timed_out is False
        mock_workflow.wait_condition.assert_called_once()

    @pytest.mark.asyncio
    @patch("awa.core.workflows.hitl_child_workflow.workflow")
    async def test_queries(self, mock_workflow: AsyncMock) -> None:
        wf = HITLChildWorkflow()

        # Mock the asyncio module - create a proper mock task and close coroutines
        def close_coroutine_and_return_task(coro: object) -> MagicMock:
            if hasattr(coro, "close"):
                coro.close()
            task = MagicMock()
            task.cancel = MagicMock()
            return task

        mock_workflow.asyncio.create_task = MagicMock(side_effect=close_coroutine_and_return_task)
        mock_workflow.sleep = AsyncMock()
        mock_workflow.info = AsyncMock(return_value=AsyncMock(workflow_id="test-workflow-id"))
        mock_workflow.logger = AsyncMock()
        input_data = HITLInput(
            title="Query",
            description="Ctx",
            markdown="# Q",
            input_schema={"type": "object"},
            non_blocking=True,
            chat_mode=True,
        )
        await wf.run(input_data)
        ctx = wf.get_context()
        assert ctx is not None
        assert ctx.title == "Query"
        assert wf.get_chat_history() == []
        assert wf.is_response_received() is False
