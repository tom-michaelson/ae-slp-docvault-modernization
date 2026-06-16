"""Agent streaming utilities for publishing workflow progress to socket.io streams."""

from datetime import timedelta
from enum import Enum
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from awa.core.activities.agent_streaming_activity import (
    emit_stream_message_activity,
    emit_stream_step_activity,
)


class StreamEventType(str, Enum):
    """Event types for agent streaming."""

    MESSAGE = "message"
    STEP = "step"
    START = "start"
    COMPLETE = "complete"
    ERROR = "error"
    OUTPUT = "output"


class FileStatus(str, Enum):
    """Status values for file processing events."""

    STARTED = "started"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class AgentExecutionStatus(str, Enum):
    """Status values for agent execution events."""

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStreaming:
    """Utility class for publishing messages to agent streaming sessions."""

    @staticmethod
    async def publish_message_multi(
        session_ids: list[str],
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Publish a message to multiple agent streaming sessions.

        Args:
            session_ids: List of streaming session IDs
            message: The message content to publish
            data: Optional metadata for the message

        """
        for session_id in session_ids:
            await AgentStreaming.publish_message(session_id, message, data)

    @staticmethod
    async def publish_message(
        session_id: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Publish a message to an agent streaming session.

        Args:
            session_id: The streaming session ID
            message: The message content to publish
            data: Optional metadata for the message

        """
        if not session_id:
            return

        try:
            # Use activity to emit directly to Socket.IO (no HTTP overhead)
            await workflow.execute_activity(
                emit_stream_message_activity,
                args=[session_id, message, data],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=1),  # Don't retry socket emissions
            )
        except Exception as e:  # noqa: BLE001
            # Socket emission failures should not break workflows
            workflow.logger.warning(f"Failed to emit stream message for session {session_id}: {e}")

    @staticmethod
    async def publish_step_start_multi(
        session_ids: list[str],
        step_name: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a step start message to multiple sessions.

        Args:
            session_ids: List of streaming session IDs
            step_name: Name of the step being started
            description: Description of what the step does
            metadata: Optional metadata about the step

        """
        for session_id in session_ids:
            await AgentStreaming.publish_step_start(session_id, step_name, description, metadata)

    @staticmethod
    async def publish_step_start(
        session_id: str,
        step_name: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a step start message.

        Args:
            session_id: The streaming session ID
            step_name: Name of the step being started
            description: Description of what the step does
            metadata: Optional metadata about the step

        """
        if not session_id:
            return

        try:
            await workflow.execute_activity(
                emit_stream_step_activity,
                args=[session_id, step_name, "start", description, None, metadata],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
        except Exception as e:  # noqa: BLE001
            workflow.logger.warning(f"Failed to emit step start: {e}")

    @staticmethod
    async def publish_step_complete_multi(
        session_ids: list[str],
        step_name: str,
        result: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a step completion message to multiple sessions.

        Args:
            session_ids: List of streaming session IDs
            step_name: Name of the step that completed
            result: Result of the step execution
            metadata: Optional metadata about the step

        """
        for session_id in session_ids:
            await AgentStreaming.publish_step_complete(session_id, step_name, result, metadata)

    @staticmethod
    async def publish_step_complete(
        session_id: str,
        step_name: str,
        result: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a step completion message.

        Args:
            session_id: The streaming session ID
            step_name: Name of the step that completed
            result: Result of the step execution
            metadata: Optional metadata about the step

        """
        if not session_id:
            return

        try:
            await workflow.execute_activity(
                emit_stream_step_activity,
                args=[session_id, step_name, "complete", None, result, metadata],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
        except Exception as e:  # noqa: BLE001
            workflow.logger.warning(f"Failed to emit step complete: {e}")

    @staticmethod
    async def publish_step_error_multi(
        session_ids: list[str],
        step_name: str,
        error: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a step error message to multiple sessions.

        Args:
            session_ids: List of streaming session IDs
            step_name: Name of the step that failed
            error: Error message
            metadata: Optional metadata about the error

        """
        for session_id in session_ids:
            await AgentStreaming.publish_step_error(session_id, step_name, error, metadata)

    @staticmethod
    async def publish_step_error(
        session_id: str,
        step_name: str,
        error: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a step error message.

        Args:
            session_id: The streaming session ID
            step_name: Name of the step that failed
            error: Error message
            metadata: Optional metadata about the error

        """
        if not session_id:
            return

        try:
            await workflow.execute_activity(
                emit_stream_step_activity,
                args=[session_id, step_name, "error", None, error, metadata],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_attempts=1),
            )
        except Exception as e:  # noqa: BLE001
            workflow.logger.warning(f"Failed to emit step error: {e}")

    @staticmethod
    async def publish_progress_multi(
        session_ids: list[str],
        current: int,
        total: int,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a progress update message to multiple sessions.

        Args:
            session_ids: List of streaming session IDs
            current: Current progress value
            total: Total expected value
            description: Description of what's being tracked
            metadata: Optional metadata about the progress

        """
        for session_id in session_ids:
            await AgentStreaming.publish_progress(session_id, current, total, description, metadata)

    @staticmethod
    async def publish_progress(
        session_id: str,
        current: int,
        total: int,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a progress update message.

        Args:
            session_id: The streaming session ID
            current: Current progress value
            total: Total expected value
            description: Description of what's being tracked
            metadata: Optional metadata about the progress

        """
        percentage = (current / total * 100) if total > 0 else 0

        data = {
            "type": "progress",
            "current": current,
            "total": total,
            "percentage": percentage,
            "metadata": metadata or {},
        }

        message = f"📊 Progress: {description} ({current}/{total} - {percentage:.1f}%)"
        await AgentStreaming.publish_message(session_id, message, data=data)

    @staticmethod
    async def publish_file_processed_multi(
        session_ids: list[str],
        file_path: str,
        status: str,
        details: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a file processing update message to multiple sessions.

        Args:
            session_ids: List of streaming session IDs
            file_path: Path of the file being processed
            status: Status of the file processing (e.g., "started", "completed", "skipped", "failed")
            details: Optional additional details
            metadata: Optional metadata about the file processing

        """
        for session_id in session_ids:
            await AgentStreaming.publish_file_processed(session_id, file_path, status, details, metadata)

    @staticmethod
    async def publish_file_processed(
        session_id: str,
        file_path: str,
        status: str,
        details: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a file processing update message.

        Args:
            session_id: The streaming session ID
            file_path: Path of the file being processed
            status: Status of the file processing (e.g., "started", "completed", "skipped", "failed")
            details: Optional additional details
            metadata: Optional metadata about the file processing

        """
        data = {
            "type": "file_processed",
            "file_path": file_path,
            "status": status,
            "details": details,
            "metadata": metadata or {},
        }

        message = f"File {status}: {file_path}"
        if details:
            message += f" - {details}"

        await AgentStreaming.publish_message(session_id, message, data=data)

    @staticmethod
    async def publish_agent_execution_multi(
        session_ids: list[str],
        agent_name: str,
        operation: str,
        file_path: str | None = None,
        status: str = "started",
        result: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish an agent execution update message to multiple sessions.

        Args:
            session_ids: List of streaming session IDs
            agent_name: Name of the agent being executed
            operation: Operation being performed by the agent
            file_path: Optional file path the agent is working on
            status: Status of the agent execution
            result: Optional result of the agent execution
            metadata: Optional metadata about the agent execution

        """
        for session_id in session_ids:
            await AgentStreaming.publish_agent_execution(
                session_id,
                agent_name,
                operation,
                file_path,
                status,
                result,
                metadata,
            )

    @staticmethod
    async def publish_agent_execution(
        session_id: str,
        agent_name: str,
        operation: str,
        file_path: str | None = None,
        status: str = "started",
        result: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish an agent execution update message.

        Args:
            session_id: The streaming session ID
            agent_name: Name of the agent being executed
            operation: Operation being performed by the agent
            file_path: Optional file path the agent is working on
            status: Status of the agent execution
            result: Optional result of the agent execution
            metadata: Optional metadata about the agent execution

        """
        data = {
            "type": "agent_execution",
            "agent_name": agent_name,
            "operation": operation,
            "file_path": file_path,
            "status": status,
            "result": result,
            "metadata": metadata or {},
        }

        message = f"Agent {agent_name}: {operation}"
        if file_path:
            message += f" on {file_path}"
        if status == "completed" and result:
            message += f" - {result}"
        elif status == "failed" and result:
            message += f" - Error: {result}"

        await AgentStreaming.publish_message(session_id, message, data=data)
