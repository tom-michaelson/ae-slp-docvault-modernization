"""Unit tests for agent streaming utilities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from awa.core.utils.agent_streaming_utils import (
    AgentExecutionStatus,
    AgentStreaming,
    FileStatus,
    StreamEventType,
)


class TestStreamEventType:
    """Test cases for StreamEventType enum."""

    def test_event_types(self) -> None:
        """Test that all expected event types are defined."""
        assert StreamEventType.MESSAGE == "message"
        assert StreamEventType.STEP == "step"
        assert StreamEventType.START == "start"
        assert StreamEventType.COMPLETE == "complete"
        assert StreamEventType.ERROR == "error"
        assert StreamEventType.OUTPUT == "output"


class TestFileStatus:
    """Test cases for FileStatus enum."""

    def test_file_statuses(self) -> None:
        """Test that all expected file statuses are defined."""
        assert FileStatus.STARTED == "started"
        assert FileStatus.COMPLETED == "completed"
        assert FileStatus.SKIPPED == "skipped"
        assert FileStatus.FAILED == "failed"


class TestAgentExecutionStatus:
    """Test cases for AgentExecutionStatus enum."""

    def test_execution_statuses(self) -> None:
        """Test that all expected execution statuses are defined."""
        assert AgentExecutionStatus.STARTED == "started"
        assert AgentExecutionStatus.COMPLETED == "completed"
        assert AgentExecutionStatus.FAILED == "failed"


class TestAgentStreamingPublishMessage:
    """Test cases for AgentStreaming.publish_message methods."""

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_message(self, mock_workflow: MagicMock) -> None:
        """Test publishing a message to a single session."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_message(
            session_id="test-session-123",
            message="Test message",
            data={"key": "value"},
        )

        mock_workflow.execute_activity.assert_called_once()
        call_args = mock_workflow.execute_activity.call_args
        # Verify the activity and arguments
        assert call_args.kwargs["args"] == ["test-session-123", "Test message", {"key": "value"}]

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_message_without_data(self, mock_workflow: MagicMock) -> None:
        """Test publishing a message without data."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_message(
            session_id="test-session-456",
            message="Simple message",
        )

        mock_workflow.execute_activity.assert_called_once()
        call_args = mock_workflow.execute_activity.call_args
        assert call_args.kwargs["args"][2] is None

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_message_empty_session_id(self, mock_workflow: MagicMock) -> None:
        """Test that publishing with empty session_id is skipped."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_message(
            session_id="",
            message="Should not be sent",
        )

        mock_workflow.execute_activity.assert_not_called()

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_message_handles_error(self, mock_workflow: MagicMock) -> None:
        """Test that errors in publish_message are handled gracefully."""
        mock_workflow.execute_activity = AsyncMock(side_effect=Exception("Activity failed"))
        mock_workflow.logger = MagicMock()

        # Should not raise
        await AgentStreaming.publish_message(
            session_id="test-session-error",
            message="Error test",
        )

        mock_workflow.logger.warning.assert_called_once()

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_message_multi(self, mock_workflow: MagicMock) -> None:
        """Test publishing a message to multiple sessions."""
        mock_workflow.execute_activity = AsyncMock()

        session_ids = ["session-1", "session-2", "session-3"]
        await AgentStreaming.publish_message_multi(
            session_ids=session_ids,
            message="Multi-session message",
            data={"type": "broadcast"},
        )

        assert mock_workflow.execute_activity.call_count == 3


class TestAgentStreamingPublishStep:
    """Test cases for AgentStreaming.publish_step methods."""

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_step_start(self, mock_workflow: MagicMock) -> None:
        """Test publishing a step start event."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_step_start(
            session_id="test-session-123",
            step_name="initialization",
            description="Starting initialization",
            metadata={"priority": "high"},
        )

        mock_workflow.execute_activity.assert_called_once()
        call_args = mock_workflow.execute_activity.call_args
        args = call_args.kwargs["args"]
        assert args[0] == "test-session-123"
        assert args[1] == "initialization"
        assert args[2] == "start"
        assert args[3] == "Starting initialization"

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_step_complete(self, mock_workflow: MagicMock) -> None:
        """Test publishing a step complete event."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_step_complete(
            session_id="test-session-456",
            step_name="processing",
            result="Successfully processed",
        )

        mock_workflow.execute_activity.assert_called_once()
        call_args = mock_workflow.execute_activity.call_args
        args = call_args.kwargs["args"]
        assert args[2] == "complete"
        assert args[4] == "Successfully processed"

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_step_error(self, mock_workflow: MagicMock) -> None:
        """Test publishing a step error event."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_step_error(
            session_id="test-session-error",
            step_name="validation",
            error="Validation failed",
            metadata={"error_code": "ERR001"},
        )

        mock_workflow.execute_activity.assert_called_once()
        call_args = mock_workflow.execute_activity.call_args
        args = call_args.kwargs["args"]
        assert args[2] == "error"
        assert args[4] == "Validation failed"

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_step_start_multi(self, mock_workflow: MagicMock) -> None:
        """Test publishing step start to multiple sessions."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_step_start_multi(
            session_ids=["s1", "s2"],
            step_name="deployment",
            description="Deploying",
        )

        assert mock_workflow.execute_activity.call_count == 2


class TestAgentStreamingPublishProgress:
    """Test cases for AgentStreaming.publish_progress methods."""

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_progress(self, mock_workflow: MagicMock) -> None:
        """Test publishing progress update."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_progress(
            session_id="test-session-123",
            current=5,
            total=10,
            description="Processing files",
        )

        mock_workflow.execute_activity.assert_called_once()
        call_args = mock_workflow.execute_activity.call_args
        args = call_args.kwargs["args"]
        message = args[1]
        assert "50.0%" in message
        assert "5/10" in message
        assert "Processing files" in message

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_progress_calculates_percentage(self, mock_workflow: MagicMock) -> None:
        """Test that progress percentage is calculated correctly."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_progress(
            session_id="test-session-456",
            current=25,
            total=100,
            description="Test",
        )

        call_args = mock_workflow.execute_activity.call_args
        message = call_args.kwargs["args"][1]
        data = call_args.kwargs["args"][2]

        assert "25.0%" in message
        assert data["percentage"] == 25.0

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_progress_handles_zero_total(self, mock_workflow: MagicMock) -> None:
        """Test that zero total doesn't cause division by zero."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_progress(
            session_id="test-session-zero",
            current=0,
            total=0,
            description="No items",
        )

        call_args = mock_workflow.execute_activity.call_args
        data = call_args.kwargs["args"][2]
        assert data["percentage"] == 0

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_progress_multi(self, mock_workflow: MagicMock) -> None:
        """Test publishing progress to multiple sessions."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_progress_multi(
            session_ids=["s1", "s2", "s3"],
            current=10,
            total=20,
            description="Multi-progress",
        )

        assert mock_workflow.execute_activity.call_count == 3


class TestAgentStreamingPublishFileProcessed:
    """Test cases for AgentStreaming.publish_file_processed methods."""

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_file_processed_started(self, mock_workflow: MagicMock) -> None:
        """Test publishing file processing started event."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_file_processed(
            session_id="test-session-123",
            file_path="/path/to/file.txt",
            status="started",
            details="Reading file",
        )

        call_args = mock_workflow.execute_activity.call_args
        message = call_args.kwargs["args"][1]
        data = call_args.kwargs["args"][2]

        assert "File started" in message
        assert "/path/to/file.txt" in message
        assert "Reading file" in message
        assert data["file_path"] == "/path/to/file.txt"
        assert data["status"] == "started"

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_file_processed_completed(self, mock_workflow: MagicMock) -> None:
        """Test publishing file processing completed event."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_file_processed(
            session_id="test-session-456",
            file_path="/path/to/output.json",
            status="completed",
        )

        call_args = mock_workflow.execute_activity.call_args
        message = call_args.kwargs["args"][1]
        assert "File completed" in message
        assert "output.json" in message

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_file_processed_with_metadata(self, mock_workflow: MagicMock) -> None:
        """Test publishing file processed with metadata."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_file_processed(
            session_id="test-session-meta",
            file_path="/file.txt",
            status="completed",
            metadata={"size": 1024, "encoding": "utf-8"},
        )

        call_args = mock_workflow.execute_activity.call_args
        data = call_args.kwargs["args"][2]
        assert data["metadata"]["size"] == 1024

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_file_processed_multi(self, mock_workflow: MagicMock) -> None:
        """Test publishing file processed to multiple sessions."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_file_processed_multi(
            session_ids=["s1", "s2"],
            file_path="/test.txt",
            status="completed",
        )

        assert mock_workflow.execute_activity.call_count == 2


class TestAgentStreamingPublishAgentExecution:
    """Test cases for AgentStreaming.publish_agent_execution methods."""

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_agent_execution_started(self, mock_workflow: MagicMock) -> None:
        """Test publishing agent execution started event."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_agent_execution(
            session_id="test-session-123",
            agent_name="ClaudeAgent",
            operation="code_review",
            file_path="/src/main.py",
            status="started",
        )

        call_args = mock_workflow.execute_activity.call_args
        message = call_args.kwargs["args"][1]
        data = call_args.kwargs["args"][2]

        assert "Agent ClaudeAgent" in message
        assert "code_review" in message
        assert "/src/main.py" in message
        assert data["agent_name"] == "ClaudeAgent"
        assert data["status"] == "started"

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_agent_execution_completed_with_result(self, mock_workflow: MagicMock) -> None:
        """Test publishing agent execution completed with result."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_agent_execution(
            session_id="test-session-456",
            agent_name="GooseAgent",
            operation="refactor",
            status="completed",
            result="Successfully refactored 5 functions",
        )

        call_args = mock_workflow.execute_activity.call_args
        message = call_args.kwargs["args"][1]
        assert "Successfully refactored 5 functions" in message

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_agent_execution_failed_with_error(self, mock_workflow: MagicMock) -> None:
        """Test publishing agent execution failed with error."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_agent_execution(
            session_id="test-session-error",
            agent_name="CodexAgent",
            operation="generate",
            status="failed",
            result="API rate limit exceeded",
        )

        call_args = mock_workflow.execute_activity.call_args
        message = call_args.kwargs["args"][1]
        assert "Error: API rate limit exceeded" in message

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_agent_execution_without_file_path(self, mock_workflow: MagicMock) -> None:
        """Test publishing agent execution without file path."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_agent_execution(
            session_id="test-session-no-file",
            agent_name="TestAgent",
            operation="analyze",
            file_path=None,
            status="started",
        )

        call_args = mock_workflow.execute_activity.call_args
        message = call_args.kwargs["args"][1]
        assert "on" not in message  # Should not include file path clause

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_agent_execution_with_metadata(self, mock_workflow: MagicMock) -> None:
        """Test publishing agent execution with metadata."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_agent_execution(
            session_id="test-session-meta",
            agent_name="QAgent",
            operation="test",
            status="completed",
            metadata={"duration": 5.2, "tests_run": 42},
        )

        call_args = mock_workflow.execute_activity.call_args
        data = call_args.kwargs["args"][2]
        assert data["metadata"]["duration"] == 5.2
        assert data["metadata"]["tests_run"] == 42

    @pytest.mark.asyncio
    @patch("awa.core.utils.agent_streaming_utils.workflow")
    async def test_publish_agent_execution_multi(self, mock_workflow: MagicMock) -> None:
        """Test publishing agent execution to multiple sessions."""
        mock_workflow.execute_activity = AsyncMock()

        await AgentStreaming.publish_agent_execution_multi(
            session_ids=["s1", "s2", "s3"],
            agent_name="MultiAgent",
            operation="process",
            status="started",
        )

        assert mock_workflow.execute_activity.call_count == 3
