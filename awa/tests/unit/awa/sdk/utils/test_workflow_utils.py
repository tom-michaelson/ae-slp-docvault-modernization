"""Test cases for SDK utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest

from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel
from awa.sdk.models.chunking_models import ChunkDocumentOutput, ChunkerType
from awa.sdk.models.jira_issue_request import JiraIssueRequest
from awa.sdk.models.read_directory_result import ReadDirectoryResult
from awa.sdk.models.workflow_paths import WorkflowPaths
from awa.sdk.utils.activity import (
    copy_directory_activity,
    delete_directory_activity,
    read_directory_activity,
    read_file_activity,
    read_file_bytes_activity,
    upsert_jira_issue_activity,
    write_file_activity,
)
from awa.sdk.utils.general import get_workflow_paths
from awa.sdk.utils.workflow import chunk_document_workflow, execute_agent_workflow


class TestSDKUtils:
    """Test cases for SDK utility functions."""

    @pytest.mark.asyncio
    async def test_read_file(self) -> None:
        """Test reading a file through read_file function."""
        # Arrange
        file_path = "/test/file.txt"
        expected_content = "file content"

        with patch("awa.sdk.utils.activity.read_file_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = expected_content

            # Act
            result = await read_file_activity(file_path)

            # Assert
            assert result == expected_content
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [file_path, None]

    @pytest.mark.asyncio
    async def test_read_file_with_default(self) -> None:
        """Test reading a file with default value."""
        # Arrange
        file_path = Path("/test/file.txt")
        default_content = "default content"

        with patch("awa.sdk.utils.activity.read_file_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = default_content

            # Act
            result = await read_file_activity(file_path, default_content)

            # Assert
            assert result == default_content
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [str(file_path), default_content]

    @pytest.mark.asyncio
    async def test_read_file_bytes(self) -> None:
        """Test reading file as bytes."""
        # Arrange
        file_path = "/test/binary.bin"
        expected_bytes = b"binary content"

        with patch("awa.sdk.utils.activity.read_file_bytes_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = expected_bytes

            # Act
            result = await read_file_bytes_activity(file_path)

            # Assert
            assert result == expected_bytes
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_file_bytes_with_default(self) -> None:
        """Test reading file bytes with default value."""
        # Arrange
        file_path = Path("/test/binary.bin")
        default_bytes = b"default binary"

        with patch("awa.sdk.utils.activity.read_file_bytes_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = default_bytes

            # Act
            result = await read_file_bytes_activity(file_path, default_bytes)

            # Assert
            assert result == default_bytes
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [str(file_path), default_bytes]

    @pytest.mark.asyncio
    async def test_write_file(self) -> None:
        """Test writing a file through write_file function."""
        # Arrange
        file_path = "/test/output.txt"
        content = "content to write"

        with patch("awa.sdk.utils.activity.write_file_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = None

            # Act
            await write_file_activity(file_path, content)

            # Assert
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [file_path, content]

    @pytest.mark.asyncio
    async def test_write_file_with_path_object(self) -> None:
        """Test writing a file using Path object."""
        # Arrange
        file_path = Path("/test/output.txt")
        content = "content to write"

        with patch("awa.sdk.utils.activity.write_file_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = None

            # Act
            await write_file_activity(file_path, content)

            # Assert
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [str(file_path), content]

    @pytest.mark.asyncio
    async def test_read_directory(self) -> None:
        """Test reading directory through read_directory function."""
        # Arrange
        directory_path = "/test/directory"

        with patch("awa.sdk.utils.activity.read_directory_activity.workflow.execute_activity") as mock_execute:
            # Mock the activity to return dictionary format as expected by activity
            mock_execute.return_value = [
                {"file": "/test/directory/file1.txt", "content": "content1"},
                {"file": "/test/directory/file2.txt", "content": "content2"},
            ]

            # Act
            result = await read_directory_activity(directory_path)

            # Assert
            assert len(result) == 2
            assert all(isinstance(item, ReadDirectoryResult) for item in result)
            assert result[0].file == "/test/directory/file1.txt"
            assert result[0].content == "content1"
            assert result[1].file == "/test/directory/file2.txt"
            assert result[1].content == "content2"

    @pytest.mark.asyncio
    async def test_read_directory_empty(self) -> None:
        """Test reading empty directory."""
        # Arrange
        directory_path = Path("/test/empty")

        with patch("awa.sdk.utils.activity.read_directory_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = []

            # Act
            result = await read_directory_activity(directory_path)

            # Assert
            assert result == []
            mock_execute.assert_called_once()

    def test_get_workflow_paths(self) -> None:
        """Test getting workflow paths."""
        # Arrange
        current_file_path = Path("/project/awa/workflows/test/test_workflow.py")

        # Mock workflow info
        mock_info = type("MockInfo", (), {})()
        mock_info.workflow_id = "test-workflow-123"
        mock_info.workflow_type = "TestWorkflow"

        # Act
        result = get_workflow_paths(current_file_path, mock_info)

        # Assert
        assert isinstance(result, WorkflowPaths)
        # The exact paths depend on the implementation, but should be strings
        assert isinstance(result.input, str)
        assert isinstance(result.output, str)
        assert isinstance(result.workflow_root, str)

    @pytest.mark.asyncio
    async def test_execute_agent(self) -> None:
        """Test executing agent through execute_agent function."""
        # Arrange
        agent_config = AgentConfiguration(
            provider="test_provider",
            model="test_model",
            instructions="test instructions",
        )
        expected_response = TaskResponseModel(
            status="completed",
            output="agent response",
        )

        with (
            patch("awa.sdk.utils.workflow.execute_agent_workflow.workflow.execute_child_workflow") as mock_execute,
            patch("awa.sdk.utils.workflow.execute_agent_workflow.workflow.info") as mock_info,
        ):
            mock_execute.return_value = expected_response
            mock_info.return_value.workflow_id = "test-workflow"

            # Act
            result = await execute_agent_workflow(agent_config)

            # Assert
            assert result == expected_response
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_jira_issue(self) -> None:
        """Test upserting JIRA issue through upsert_jira_issue function."""
        # Arrange
        jira_request = JiraIssueRequest(
            project_id="TEST",
            summary="Test Issue",
            description="Test Description",
            issue_type="Bug",
        )
        expected_response = "TEST-123"

        with patch("awa.sdk.utils.activity.upsert_jira_issue_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = expected_response

            # Act
            result = await upsert_jira_issue_activity(jira_request)

            # Assert
            assert result == expected_response
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_copy_directory(self) -> None:
        """Test copying directory through copy_directory function."""
        # Arrange
        source_path = "/source/directory"
        destination_path = "/dest/directory"
        ignore_file_path = "/ignore.txt"
        expected_files = ["/dest/directory/file1.txt", "/dest/directory/file2.txt"]

        with patch("awa.sdk.utils.activity.copy_directory_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = expected_files

            # Act
            result = await copy_directory_activity(source_path, destination_path, ignore_file_path)

            # Assert
            assert result == expected_files
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [source_path, destination_path, ignore_file_path]

    @pytest.mark.asyncio
    async def test_copy_directory_without_ignore(self) -> None:
        """Test copying directory without ignore file."""
        # Arrange
        source_path = Path("/source")
        destination_path = Path("/dest")

        with patch("awa.sdk.utils.activity.copy_directory_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = []

            # Act
            await copy_directory_activity(source_path, destination_path)

            # Assert
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [str(source_path), str(destination_path), None]

    @pytest.mark.asyncio
    async def test_delete_directory(self) -> None:
        """Test deleting directory through delete_directory function."""
        # Arrange
        directory_path = "/test/to/delete"

        with patch("awa.sdk.utils.activity.delete_directory_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = None

            # Act
            await delete_directory_activity(directory_path)

            # Assert
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["args"] == [directory_path]

    @pytest.mark.asyncio
    async def test_workflow_utils_activity_timeouts(self) -> None:
        """Test that utility functions use appropriate timeouts."""
        # This test verifies that timeout constants are used correctly

        with patch("awa.sdk.utils.activity.read_file_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = "test"

            # Act - call a method that should use file I/O timeout
            await read_file_activity("/test/file.txt")

            # Assert - verify timeout was set
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert "start_to_close_timeout" in kwargs
            # The exact timeout value depends on constants, but should be present

    @pytest.mark.asyncio
    async def test_workflow_utils_task_queue_usage(self) -> None:
        """Test that utility functions use correct task queue."""
        # Arrange
        with patch("awa.sdk.utils.activity.write_file_activity.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = None

            # Act
            await write_file_activity("test.txt", "content")

            # Assert - verify task queue was set
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert "task_queue" in kwargs
            # Should use the AWA default task queue constant

    @pytest.mark.asyncio
    async def test_chunk_document(self) -> None:
        """Test chunking a document through chunk_document function."""
        # Arrange
        content = "This is a test document with multiple sentences. It should be chunked appropriately."
        expected_chunks = [
            {
                "text": "This is a test document with multiple sentences.",
                "token_count": 10,
                "start_index": 0,
                "end_index": 48,
            },
            {
                "text": "It should be chunked appropriately.",
                "token_count": 6,
                "start_index": 49,
                "end_index": 84,
            },
        ]
        expected_output = {
            "chunks": expected_chunks,
            "total_chunks": 2,
            "chunker_used": "recursive",
        }

        with (
            patch("awa.sdk.utils.workflow.chunk_document_workflow.workflow.execute_child_workflow") as mock_execute,
            patch("awa.sdk.utils.workflow.chunk_document_workflow.workflow.info") as mock_info,
        ):
            # Mock execute_child_workflow to return a ChunkDocumentOutput directly
            mock_execute.return_value = ChunkDocumentOutput.model_validate(expected_output)
            # Mock workflow.info()
            mock_info.return_value.workflow_id = "test-workflow-id"

            # Act
            result = await chunk_document_workflow(content)

            # Assert
            assert isinstance(result, ChunkDocumentOutput)
            assert result.total_chunks == 2
            assert result.chunker_used == "recursive"
            assert len(result.chunks) == 2
            assert result.chunks[0].text == "This is a test document with multiple sentences."

            # Verify the workflow was called correctly
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["workflow"] == "awa-chunk-document"
            assert kwargs["arg"].content == content
            assert kwargs["arg"].chunker_type == ChunkerType.RECURSIVE

    @pytest.mark.asyncio
    async def test_chunk_document_with_custom_options(self) -> None:
        """Test chunking a document with custom chunker type and options."""
        # Arrange
        content = "Test content"
        chunker_type = ChunkerType.TOKEN
        max_chunk_size = 50
        chunk_overlap = 10
        expected_output = {
            "chunks": [
                {
                    "text": "Test content",
                    "token_count": 2,
                    "start_index": 0,
                    "end_index": 12,
                },
            ],
            "total_chunks": 1,
            "chunker_used": "token",
        }

        with (
            patch("awa.sdk.utils.workflow.chunk_document_workflow.workflow.execute_child_workflow") as mock_execute,
            patch("awa.sdk.utils.workflow.chunk_document_workflow.workflow.info") as mock_info,
        ):
            # Mock execute_child_workflow to return a ChunkDocumentOutput directly
            mock_execute.return_value = ChunkDocumentOutput.model_validate(expected_output)
            # Mock workflow.info()
            mock_info.return_value.workflow_id = "test-workflow-id"

            # Act
            result = await chunk_document_workflow(
                content=content,
                chunker_type=chunker_type,
                max_chunk_size=max_chunk_size,
                chunk_overlap=chunk_overlap,
            )

            # Assert
            assert result.chunker_used == "token"

            # Verify the workflow was called with correct parameters
            mock_execute.assert_called_once()
            _args, kwargs = mock_execute.call_args
            assert kwargs["workflow"] == "awa-chunk-document"
            assert kwargs["arg"].content == content
            assert kwargs["arg"].chunker_type == ChunkerType.TOKEN
            assert kwargs["arg"].max_chunk_size == max_chunk_size
            assert kwargs["arg"].chunk_overlap == chunk_overlap
