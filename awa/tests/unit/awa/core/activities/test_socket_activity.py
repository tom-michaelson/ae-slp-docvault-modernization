"""Unit tests for socket activity."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from awa.core.activities.socket_activity import emit_hitl_chat_message


class TestEmitHitlChatMessage:
    """Test cases for emit_hitl_chat_message activity."""

    @pytest.mark.asyncio
    @patch("awa.core.activities.socket_activity.emit_hitl_system_message")
    async def test_emit_hitl_chat_message_success(
        self,
        mock_emit_hitl_system_message: AsyncMock,
    ) -> None:
        """Test successful emission of HITL chat message."""
        # Arrange
        task_id = "test-task-123"
        message = "Test message"
        data = {"key": "value"}
        timestamp = datetime.now(UTC)

        # Act
        await emit_hitl_chat_message(task_id, message, data, timestamp)

        # Assert
        mock_emit_hitl_system_message.assert_called_once_with(
            task_id=task_id,
            message=message,
            data=data,
            timestamp=timestamp,
        )

    @pytest.mark.asyncio
    @patch("awa.core.activities.socket_activity.emit_hitl_system_message")
    async def test_emit_hitl_chat_message_with_defaults(
        self,
        mock_emit_hitl_system_message: AsyncMock,
    ) -> None:
        """Test emission with default parameters."""
        # Arrange
        task_id = "test-task-123"
        message = "Test message"

        # Act
        await emit_hitl_chat_message(task_id, message)

        # Assert
        mock_emit_hitl_system_message.assert_called_once_with(
            task_id=task_id,
            message=message,
            data=None,
            timestamp=None,
        )

    @pytest.mark.asyncio
    @patch("awa.core.activities.socket_activity.emit_hitl_system_message")
    async def test_emit_hitl_chat_message_handles_exception(
        self,
        mock_emit_hitl_system_message: AsyncMock,
    ) -> None:
        """Test that exceptions in socket emission don't propagate."""
        # Arrange
        task_id = "test-task-123"
        message = "Test message"
        mock_emit_hitl_system_message.side_effect = Exception("Socket error")

        # Act - should not raise exception
        await emit_hitl_chat_message(task_id, message)

        # Assert
        mock_emit_hitl_system_message.assert_called_once_with(
            task_id=task_id,
            message=message,
            data=None,
            timestamp=None,
        )
