from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from awa.core.models.hitl import HITLOutput, HITLResponse
from awa.core.workflows.hello_human import HelloHumanWorkflow


class TestHelloHumanWorkflow:
    """Test cases for HelloHumanWorkflow."""

    def test_hello_human_workflow_init(self) -> None:
        """Test HelloHumanWorkflow initialization."""
        workflow = HelloHumanWorkflow()
        assert workflow is not None

    @pytest.mark.asyncio
    @patch("awa.core.workflows.hello_human.workflow")
    async def test_run_workflow_success_with_name(self, mock_workflow: AsyncMock) -> None:
        """Test successful run of HelloHumanWorkflow with user providing name."""
        # Arrange
        hello_workflow = HelloHumanWorkflow()

        # Mock the workflow info
        mock_workflow.info.return_value.workflow_id = "test-workflow-id"

        # Mock HITL response with user name
        hitl_response = HITLResponse(
            data={"name": "Alice Smith"},
            message="",
        )
        hitl_output = HITLOutput(
            response=hitl_response,
            timed_out=False,
            chat_history=[],
        )

        # Mock async functions
        mock_workflow.execute_child_workflow = AsyncMock(return_value=hitl_output)
        mock_workflow.execute_activity = AsyncMock(return_value="Hello Alice Smith!")

        # Act
        result = await hello_workflow.run()

        # Assert
        assert result == "Hello Alice Smith!"
        mock_workflow.execute_child_workflow.assert_called_once()
        mock_workflow.execute_activity.assert_called_once()

        # Verify the activity was called with the correct name
        activity_call_args = mock_workflow.execute_activity.call_args
        assert activity_call_args[0][1] == "Alice Smith"
        assert activity_call_args[1]["start_to_close_timeout"] == timedelta(seconds=5)

    @pytest.mark.asyncio
    @patch("awa.core.workflows.hello_human.workflow")
    async def test_run_workflow_timeout(self, mock_workflow: AsyncMock) -> None:
        """Test workflow run when HITL times out."""
        # Arrange
        hello_workflow = HelloHumanWorkflow()

        # Mock the workflow info
        mock_workflow.info.return_value.workflow_id = "test-workflow-id"

        # Mock HITL timeout response
        hitl_output = HITLOutput(
            response=None,
            timed_out=True,
            chat_history=[],
        )

        # Mock async functions
        mock_workflow.execute_child_workflow = AsyncMock(return_value=hitl_output)
        mock_workflow.execute_activity = AsyncMock(return_value="Hello Anonymous!")

        # Act
        result = await hello_workflow.run()

        # Assert
        assert result == "Hello Anonymous!"
        mock_workflow.execute_child_workflow.assert_called_once()
        mock_workflow.execute_activity.assert_called_once()

        # Verify the activity was called with "Anonymous"
        activity_call_args = mock_workflow.execute_activity.call_args
        assert activity_call_args[0][1] == "Anonymous"

    @pytest.mark.asyncio
    @patch("awa.core.workflows.hello_human.workflow")
    async def test_run_workflow_no_response(self, mock_workflow: AsyncMock) -> None:
        """Test workflow run when HITL has no response."""
        # Arrange
        hello_workflow = HelloHumanWorkflow()

        # Mock the workflow info
        mock_workflow.info.return_value.workflow_id = "test-workflow-id"

        # Mock HITL no response
        hitl_output = HITLOutput(
            response=None,
            timed_out=False,
            chat_history=[],
        )

        # Mock async functions
        mock_workflow.execute_child_workflow = AsyncMock(return_value=hitl_output)
        mock_workflow.execute_activity = AsyncMock(return_value="Hello Anonymous!")

        # Act
        result = await hello_workflow.run()

        # Assert
        assert result == "Hello Anonymous!"
        mock_workflow.execute_activity.assert_called_once()

        # Verify the activity was called with "Anonymous"
        activity_call_args = mock_workflow.execute_activity.call_args
        assert activity_call_args[0][1] == "Anonymous"

    @pytest.mark.asyncio
    @patch("awa.core.workflows.hello_human.workflow")
    async def test_run_workflow_hitl_input_schema(self, mock_workflow: AsyncMock) -> None:
        """Test that HITL child workflow is called with correct input schema."""
        # Arrange
        hello_workflow = HelloHumanWorkflow()

        # Mock the workflow info
        mock_workflow.info.return_value.workflow_id = "test-workflow-id"

        # Mock HITL response
        hitl_response = HITLResponse(data={"name": "Test User"}, message="")
        hitl_output = HITLOutput(response=hitl_response, timed_out=False, chat_history=[])

        mock_workflow.execute_child_workflow = AsyncMock(return_value=hitl_output)
        mock_workflow.execute_activity = AsyncMock(return_value="Hello Test User!")

        # Act
        await hello_workflow.run()

        # Assert
        mock_workflow.execute_child_workflow.assert_called_once()
        call_args = mock_workflow.execute_child_workflow.call_args

        # Verify the HITL input structure
        hitl_input = call_args[0][1]
        assert hitl_input.title == "Hello Human Workflow"
        assert hitl_input.description == "Please provide your name so we can greet you properly."
        assert hitl_input.input_schema["type"] == "object"
        assert "name" in hitl_input.input_schema["properties"]
        assert hitl_input.input_schema["required"] == ["name"]
        assert hitl_input.timeout_seconds == 900
        assert hitl_input.non_blocking is False
        assert hitl_input.chat_mode is False

    def test_workflow_class_exists(self) -> None:
        """Test that HelloHumanWorkflow class exists and is instantiable."""
        workflow = HelloHumanWorkflow()
        assert workflow is not None
        assert hasattr(workflow, "run")
