"""Unit tests for write_to_vector_db activity."""

from unittest.mock import Mock, patch

import pytest

from awa.core.activities.write_to_vector_db import write_to_vector_db_activity
from awa.core.models.vector_ingestion_output import ChunkInfo


class TestWriteToVectorDbActivity:
    """Test cases for write_to_vector_db activity."""

    @patch("awa.core.activities.write_to_vector_db.chromadb")
    async def test_write_to_vector_db_activity_success(self, mock_chromadb: Mock) -> None:
        """Test successful vector database write."""
        # Mock ChromaDB
        mock_client = Mock()
        mock_collection = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection

        # Mock collection methods
        mock_collection.count.return_value = 1
        mock_collection.metadata = {"test": "metadata"}

        # Test data
        chunks = [
            ChunkInfo(
                chunk_id="chunk_1",
                text="Test content",
                token_count=3,
                start_index=0,
                end_index=12,
                embedding_vector=[0.1, 0.2, 0.3],
            ),
        ]

        # Test the activity
        result = await write_to_vector_db_activity(
            chunks,
            "chroma",
            "./test_db",
            "test_collection",
        )

        # Check the actual return structure from the activity
        assert result["vector_db_type"] == "chroma"
        assert result["vector_db_path"] == "./test_db"
        assert result["collection_name"] == "test_collection"
        assert result["total_embeddings_stored"] == 1

        # Check that PersistentClient was called with the correct path
        mock_chromadb.PersistentClient.assert_called_once()
        call_args = mock_chromadb.PersistentClient.call_args
        assert call_args.kwargs["path"] == "./test_db"

    async def test_write_to_vector_db_activity_unsupported_type(self) -> None:
        """Test that unsupported vector DB types raise proper error."""
        # Test data
        chunks = [
            ChunkInfo(
                chunk_id="chunk_1",
                text="Test content",
                token_count=3,
                start_index=0,
                end_index=12,
                embedding_vector=[0.1, 0.2, 0.3],
            ),
        ]

        # Test that unsupported DB types raise Exception (not ValueError)
        with pytest.raises(Exception, match="Failed to write to vector database"):
            await write_to_vector_db_activity(
                chunks,
                "unsupported_db",
                "./test_db",
                "test_collection",
            )
