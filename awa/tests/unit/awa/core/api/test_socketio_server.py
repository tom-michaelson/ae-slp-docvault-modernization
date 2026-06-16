"""Unit tests for Socket.IO server functionality."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from awa.core.api.socketio_server import emit_hitl_system_message


class TestEmitHITLSystemMessage:
    """Test cases for emit_hitl_system_message function."""

    @pytest.mark.asyncio
    @patch("awa.core.api.socketio_server.sio")
    async def test_emit_hitl_system_message_success(self, mock_sio: AsyncMock) -> None:
        """Test successful emission of HITL system message."""
        # Arrange
        mock_sio.emit = AsyncMock()
        task_id = "task-123"
        message = "System message"
        data = {"type": "status", "value": "processing"}
        timestamp = datetime.now(UTC)

        # Act
        await emit_hitl_system_message(
            task_id=task_id,
            message=message,
            data=data,
            timestamp=timestamp,
            is_human=False,
        )

        # Assert
        expected_message = {
            "task_id": task_id,
            "message": message,
            "data": data,
            "timestamp": timestamp.isoformat(),
            "is_human": False,
        }
        mock_sio.emit.assert_called_once_with(
            "hitl_chat_message",
            expected_message,
            room=f"hitl_chat_{task_id}",
        )

    @pytest.mark.asyncio
    @patch("awa.core.api.socketio_server.sio")
    async def test_emit_hitl_system_message_with_defaults(self, mock_sio: AsyncMock) -> None:
        """Test emission with default parameters."""
        # Arrange
        mock_sio.emit = AsyncMock()
        task_id = "task-456"
        message = "Default message"

        # Act
        await emit_hitl_system_message(task_id=task_id, message=message)

        # Assert
        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args

        # Verify event name and room
        assert call_args[0][0] == "hitl_chat_message"
        assert call_args[1]["room"] == f"hitl_chat_{task_id}"

        # Verify message structure
        emitted_message = call_args[0][1]
        assert emitted_message["task_id"] == task_id
        assert emitted_message["message"] == message
        assert emitted_message["data"] is None
        assert emitted_message["is_human"] is False
        assert "timestamp" in emitted_message

    @pytest.mark.asyncio
    @patch("awa.core.api.socketio_server.sio")
    async def test_emit_hitl_system_message_human_message(self, mock_sio: AsyncMock) -> None:
        """Test emission of human message."""
        # Arrange
        mock_sio.emit = AsyncMock()
        task_id = "task-789"
        message = "User question"
        user_data = {"user_id": "user-123", "name": "John"}

        # Act
        await emit_hitl_system_message(
            task_id=task_id,
            message=message,
            data=user_data,
            is_human=True,
        )

        # Assert
        mock_sio.emit.assert_called_once()
        emitted_message = mock_sio.emit.call_args[0][1]
        assert emitted_message["is_human"] is True
        assert emitted_message["data"] == user_data


class TestSocketIOEvents:
    """Test cases for Socket.IO event handlers."""

    @pytest.fixture
    def mock_connected_clients(self) -> dict:
        """Mock connected clients dictionary."""
        return {"client-1": set(), "client-2": {"hitl_chat_task-123"}}

    @pytest.mark.asyncio
    @patch("awa.core.api.socketio_server.connected_clients")
    @patch("awa.core.api.socketio_server.sio")
    async def test_join_hitl_chat_success(
        self,
        mock_sio: AsyncMock,
        mock_connected_clients: MagicMock,
    ) -> None:
        """Test successful joining of HITL chat room."""
        # Import the event handler
        from awa.core.api.socketio_server import join_hitl_chat

        # Arrange
        mock_sio.enter_room = AsyncMock()
        mock_client_rooms = MagicMock()
        mock_client_rooms.add = MagicMock()
        mock_connected_clients.__getitem__.return_value = mock_client_rooms

        sid = "client-123"
        data = {"task_id": "task-456"}

        # Act
        result = await join_hitl_chat(sid, data)

        # Assert
        assert result == {"status": "joined", "task_id": "task-456", "room": "hitl_chat_task-456"}
        mock_sio.enter_room.assert_called_once_with(sid, "hitl_chat_task-456")
        mock_client_rooms.add.assert_called_once_with("hitl_chat_task-456")

    @pytest.mark.asyncio
    async def test_join_hitl_chat_missing_task_id(self) -> None:
        """Test joining chat room with missing task_id."""
        # Import the event handler
        from awa.core.api.socketio_server import join_hitl_chat

        # Arrange
        sid = "client-123"
        data = {}  # Missing task_id

        # Act
        result = await join_hitl_chat(sid, data)

        # Assert
        assert result == {"status": "error", "message": "task_id required"}

    @pytest.mark.asyncio
    @patch("awa.core.api.socketio_server.connected_clients")
    @patch("awa.core.api.socketio_server.sio")
    async def test_leave_hitl_chat_success(
        self,
        mock_sio: AsyncMock,
        mock_connected_clients: MagicMock,
    ) -> None:
        """Test successful leaving of HITL chat room."""
        # Import the event handler
        from awa.core.api.socketio_server import leave_hitl_chat

        # Arrange
        mock_sio.leave_room = AsyncMock()
        mock_client_rooms = MagicMock()
        mock_client_rooms.discard = MagicMock()
        mock_connected_clients.__getitem__.return_value = mock_client_rooms

        sid = "client-123"
        data = {"task_id": "task-456"}

        # Act
        result = await leave_hitl_chat(sid, data)

        # Assert
        assert result == {"status": "left", "task_id": "task-456", "room": "hitl_chat_task-456"}
        mock_sio.leave_room.assert_called_once_with(sid, "hitl_chat_task-456")
        mock_client_rooms.discard.assert_called_once_with("hitl_chat_task-456")

    @pytest.mark.asyncio
    async def test_leave_hitl_chat_missing_task_id(self) -> None:
        """Test leaving chat room with missing task_id."""
        # Import the event handler
        from awa.core.api.socketio_server import leave_hitl_chat

        # Arrange
        sid = "client-123"
        data = {}  # Missing task_id

        # Act
        result = await leave_hitl_chat(sid, data)

        # Assert
        assert result == {"status": "error", "message": "task_id required"}

    @pytest.mark.asyncio
    @patch("awa.core.api.socketio_server.sio")
    async def test_send_hitl_chat_message_success(self, mock_sio: AsyncMock) -> None:
        """Test successful sending of chat message."""
        # Import the event handler
        from awa.core.api.socketio_server import send_hitl_chat_message

        # Arrange
        mock_sio.emit = AsyncMock()
        sid = "client-123"
        data = {
            "task_id": "task-789",
            "message": "Hello from user",
            "user_info": {"name": "Jane", "id": "user-456"},
        }

        # Act
        result = await send_hitl_chat_message(sid, data)

        # Assert
        assert result == {"status": "sent", "task_id": "task-789"}
        mock_sio.emit.assert_called_once()

        # Verify the emitted message structure
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == "hitl_chat_message"
        assert call_args[1]["room"] == "hitl_chat_task-789"

        emitted_message = call_args[0][1]
        assert emitted_message["task_id"] == "task-789"
        assert emitted_message["message"] == "Hello from user"
        assert emitted_message["user_info"] == {"name": "Jane", "id": "user-456"}
        assert emitted_message["is_human"] is True
        assert "timestamp" in emitted_message

    @pytest.mark.asyncio
    async def test_send_hitl_chat_message_missing_data(self) -> None:
        """Test sending chat message with missing required data."""
        # Import the event handler
        from awa.core.api.socketio_server import send_hitl_chat_message

        # Arrange
        sid = "client-123"

        # Test missing task_id
        data_no_task = {"message": "Hello"}
        result = await send_hitl_chat_message(sid, data_no_task)
        assert result == {"status": "error", "message": "task_id and message are required"}

        # Test missing message
        data_no_message = {"task_id": "task-123"}
        result = await send_hitl_chat_message(sid, data_no_message)
        assert result == {"status": "error", "message": "task_id and message are required"}

    @pytest.mark.asyncio
    async def test_send_hitl_chat_message_empty_user_info(self) -> None:
        """Test sending chat message with empty user_info."""
        # Import the event handler
        from awa.core.api.socketio_server import send_hitl_chat_message

        # Arrange
        with patch("awa.core.api.socketio_server.sio") as mock_sio:
            mock_sio.emit = AsyncMock()

            sid = "client-123"
            data = {
                "task_id": "task-789",
                "message": "Message without user info",
            }

            # Act
            result = await send_hitl_chat_message(sid, data)

            # Assert
            assert result == {"status": "sent", "task_id": "task-789"}
            emitted_message = mock_sio.emit.call_args[0][1]
            assert emitted_message["user_info"] == {}
