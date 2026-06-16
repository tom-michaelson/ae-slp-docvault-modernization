"""Unit tests for the chunk document workflow."""

from unittest.mock import patch

import pytest

from awa.core.workflows.chunk_document_workflow import ChunkDocumentWorkflow
from awa.sdk.models.chunking_models import ChunkDocumentInput, ChunkDocumentOutput, ChunkerType


@pytest.mark.asyncio
async def test_chunk_document_workflow() -> None:
    """Test the chunk document workflow execution."""
    # Arrange
    workflow = ChunkDocumentWorkflow()
    workflow_input = ChunkDocumentInput(
        content="This is test content for chunking.",
        chunker_type=ChunkerType.RECURSIVE,
    )

    expected_activity_result = {
        "chunks": [
            {
                "text": "This is test content for chunking.",
                "token_count": 7,
                "start_index": 0,
                "end_index": 34,
            },
        ],
        "total_chunks": 1,
        "chunker_used": "recursive",
    }

    # Mock the workflow.execute_activity and workflow.logger
    with (
        patch("awa.core.workflows.chunk_document_workflow.workflow.execute_activity") as mock_activity,
        patch("awa.core.workflows.chunk_document_workflow.workflow.logger") as mock_logger,
    ):
        mock_activity.return_value = expected_activity_result

        # Act
        result = await workflow.run(workflow_input)

        # Assert
        assert isinstance(result, ChunkDocumentOutput)
        assert result.total_chunks == 1
        assert result.chunker_used == "recursive"
        assert len(result.chunks) == 1
        assert result.chunks[0].text == "This is test content for chunking."

        # Verify activity was called correctly
        mock_activity.assert_called_once()
        args, _kwargs = mock_activity.call_args
        assert args[0] == "awa-chunk-document"  # Activity name
        assert args[1] == workflow_input  # Input data

        # Verify logging
        assert mock_logger.info.call_count == 2


@pytest.mark.asyncio
async def test_chunk_document_workflow_with_options() -> None:
    """Test the chunk document workflow with custom chunking options."""
    # Arrange
    workflow = ChunkDocumentWorkflow()
    workflow_input = ChunkDocumentInput(
        content="A" * 1000,  # Long content
        chunker_type=ChunkerType.TOKEN,
        max_chunk_size=100,
        chunk_overlap=20,
    )

    expected_activity_result = {
        "chunks": [
            {
                "text": "A" * 100,
                "token_count": 100,
                "start_index": 0,
                "end_index": 100,
            },
            {
                "text": "A" * 100,
                "token_count": 100,
                "start_index": 80,
                "end_index": 180,
            },
        ],
        "total_chunks": 2,
        "chunker_used": "token",
    }

    # Mock the workflow.execute_activity
    with (
        patch("awa.core.workflows.chunk_document_workflow.workflow.execute_activity") as mock_activity,
        patch("awa.core.workflows.chunk_document_workflow.workflow.logger"),
    ):
        mock_activity.return_value = expected_activity_result

        # Act
        result = await workflow.run(workflow_input)

        # Assert
        assert result.total_chunks == 2
        assert result.chunker_used == "token"
        assert len(result.chunks) == 2

        # Verify the input was passed through correctly
        mock_activity.assert_called_once()
        _, passed_input = mock_activity.call_args[0]
        assert passed_input.chunker_type == ChunkerType.TOKEN
        assert passed_input.max_chunk_size == 100
        assert passed_input.chunk_overlap == 20


@pytest.mark.asyncio
async def test_chunk_document_workflow_empty_content() -> None:
    """Test the chunk document workflow with empty content."""
    # Arrange
    workflow = ChunkDocumentWorkflow()
    workflow_input = ChunkDocumentInput(content="")

    expected_activity_result = {
        "chunks": [],
        "total_chunks": 0,
        "chunker_used": "recursive",
    }

    # Mock the workflow.execute_activity
    with (
        patch("awa.core.workflows.chunk_document_workflow.workflow.execute_activity") as mock_activity,
        patch("awa.core.workflows.chunk_document_workflow.workflow.logger"),
    ):
        mock_activity.return_value = expected_activity_result

        # Act
        result = await workflow.run(workflow_input)

        # Assert
        assert result.total_chunks == 0
        assert len(result.chunks) == 0
        assert result.chunker_used == "recursive"
