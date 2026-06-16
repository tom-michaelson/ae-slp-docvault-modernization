"""Unit tests for write_to_s3_vector_store activity."""

from unittest.mock import Mock, patch

import pytest

from awa.core.activities.write_to_s3_vector_store import write_to_s3_vector_store_activity
from awa.core.models.vector_ingestion_output import ChunkInfo


class TestWriteToS3VectorStoreActivity:
    """Test cases for write_to_s3_vector_store activity."""

    @patch("awa.core.activities.write_to_s3_vector_store.ConfigLoader")
    @patch("awa.core.activities.write_to_s3_vector_store.S3VectorStore")
    async def test_write_to_s3_vector_store_activity_success(
        self,
        mock_s3_store_class: Mock,
        mock_config_loader: Mock,
    ) -> None:
        """Test successful S3 Vector Store write."""
        # Mock configuration with proper string values
        mock_config = Mock()
        mock_s3_vector_config = Mock()
        mock_s3_vector_config.enabled = True
        mock_s3_vector_config.region_name = "us-east-2"
        mock_s3_vector_config.vector_bucket_name = "test-bucket"
        mock_s3_vector_config.index_name = "test-index"
        mock_s3_vector_config.embedding_source = "azure_openai"
        mock_config.s3_vector = mock_s3_vector_config
        mock_config_loader.get_config.return_value = mock_config

        # Mock S3VectorStore
        mock_s3_store = Mock()
        mock_s3_store_class.return_value = mock_s3_store
        mock_s3_store.create_index_if_not_exists.return_value = {"status": "created"}
        mock_s3_store.batch_put_vectors.return_value = [{"status": "success"}]

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
        result = await write_to_s3_vector_store_activity(
            chunks,
            "test-index",
            create_index=True,
            batch_size=100,
        )

        # Verify results
        assert result["vectors_written"] == 1
        assert result["index_name"] == "test-index"
        assert result["created_index"] is True
        assert result["skipped"] is False

        # Verify method calls
        mock_s3_store.create_index_if_not_exists.assert_called_once_with(
            index_name="test-index",
            dimension=3,  # Length of embedding vector
        )
        mock_s3_store.batch_put_vectors.assert_called_once()

    @patch("awa.core.activities.write_to_s3_vector_store.ConfigLoader")
    async def test_write_to_s3_vector_store_activity_disabled(
        self,
        mock_config_loader: Mock,
    ) -> None:
        """Test S3 Vector Store write when service is disabled."""
        # Mock configuration with S3 Vector Store disabled
        mock_config = Mock()
        mock_config.s3_vector = None
        mock_config_loader.get_config.return_value = mock_config

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
        result = await write_to_s3_vector_store_activity(chunks)

        # Verify results
        assert result["vectors_written"] == 0
        assert result["index_name"] is None
        assert result["created_index"] is False
        assert result["skipped"] is True
        assert result["reason"] == "S3 Vector Store not enabled"

    @patch("awa.core.activities.write_to_s3_vector_store.ConfigLoader")
    @patch("awa.core.activities.write_to_s3_vector_store.S3VectorStore")
    async def test_write_to_s3_vector_store_activity_no_embeddings(
        self,
        mock_s3_store_class: Mock,
        mock_config_loader: Mock,
    ) -> None:
        """Test S3 Vector Store write with no embeddings."""
        # Mock configuration with proper string values
        mock_config = Mock()
        mock_s3_vector_config = Mock()
        mock_s3_vector_config.enabled = True
        mock_s3_vector_config.region_name = "us-east-2"
        mock_s3_vector_config.vector_bucket_name = "test-bucket"
        mock_s3_vector_config.index_name = "test-index"
        mock_s3_vector_config.embedding_source = "tfidf"
        mock_config.s3_vector = mock_s3_vector_config
        mock_config_loader.get_config.return_value = mock_config

        # Mock S3VectorStore - this will never be instantiated in this test due to empty chunks
        # but we need to mock it in case the test logic changes
        mock_s3_store = Mock()
        mock_s3_store_class.return_value = mock_s3_store

        # Test data - empty chunks
        chunks = []

        # Test the activity - should raise RuntimeError wrapping ValueError for no chunks with embeddings
        with pytest.raises(
            RuntimeError,
            match="Failed to write to S3 Vector Store: No chunks with embeddings provided",
        ):
            await write_to_s3_vector_store_activity(chunks, "test-index", create_index=True, batch_size=100)

    @patch("awa.core.activities.write_to_s3_vector_store.ConfigLoader")
    @patch("awa.core.activities.write_to_s3_vector_store.S3VectorStore")
    async def test_write_to_s3_vector_store_activity_with_metadata(
        self,
        mock_s3_store_class: Mock,
        mock_config_loader: Mock,
    ) -> None:
        """Test S3 Vector Store write with custom metadata."""
        # Mock configuration with proper string values
        mock_config = Mock()
        mock_s3_vector_config = Mock()
        mock_s3_vector_config.enabled = True
        mock_s3_vector_config.region_name = "us-east-2"
        mock_s3_vector_config.vector_bucket_name = "test-bucket"
        mock_s3_vector_config.index_name = "test-index"
        mock_s3_vector_config.embedding_source = "tfidf"
        mock_config.s3_vector = mock_s3_vector_config
        mock_config_loader.get_config.return_value = mock_config

        # Mock S3VectorStore
        mock_s3_store = Mock()
        mock_s3_store_class.return_value = mock_s3_store
        mock_s3_store.create_index_if_not_exists.return_value = {"status": "created"}
        mock_s3_store.batch_put_vectors.return_value = [{"status": "success"}]

        # Test data - create a mock chunk object with all the attributes the activity looks for
        chunk_with_metadata = Mock()
        chunk_with_metadata.chunk_id = "chunk_with_meta"
        chunk_with_metadata.text = "Test content with metadata"
        chunk_with_metadata.token_count = 5
        chunk_with_metadata.start_index = 0
        chunk_with_metadata.end_index = 25
        chunk_with_metadata.embedding_vector = [0.1, 0.2, 0.3, 0.4]
        chunk_with_metadata.file_path = "/test/path.pdf"
        chunk_with_metadata.metadata = {"custom_field": "custom_value"}

        chunks = [chunk_with_metadata]

        # Test the activity
        result = await write_to_s3_vector_store_activity(chunks, "test-index", create_index=False, batch_size=50)

        # Verify results
        assert result["vectors_written"] == 1
        assert result["index_name"] == "test-index"
        assert result["created_index"] is False
        assert result["skipped"] is False

        # Verify batch_put_vectors was called with correct parameters
        mock_s3_store.batch_put_vectors.assert_called_once()
        call_args = mock_s3_store.batch_put_vectors.call_args
        vectors = call_args.args[0]

        assert len(vectors) == 1
        vector = vectors[0]
        assert vector["key"] == "/test/path.pdf_chunk_with_meta"
        assert vector["embedding"] == [0.1, 0.2, 0.3, 0.4]
        assert "custom_field" in vector["metadata"]
        assert vector["metadata"]["custom_field"] == "custom_value"
        assert vector["metadata"]["source_text"] == "Test content with metadata"
        assert vector["metadata"]["file_path"] == "/test/path.pdf"

    @patch("awa.core.activities.write_to_s3_vector_store.ConfigLoader")
    @patch("awa.core.activities.write_to_s3_vector_store.S3VectorStore")
    async def test_write_to_s3_vector_store_activity_error_handling(
        self,
        mock_s3_store_class: Mock,
        mock_config_loader: Mock,
    ) -> None:
        """Test S3 Vector Store write error handling."""
        # Mock configuration with proper string values
        mock_config = Mock()
        mock_s3_vector_config = Mock()
        mock_s3_vector_config.enabled = True
        mock_s3_vector_config.region_name = "us-east-2"
        mock_s3_vector_config.vector_bucket_name = "test-bucket"
        mock_s3_vector_config.index_name = "test-index"
        mock_config.s3_vector = mock_s3_vector_config
        mock_config_loader.get_config.return_value = mock_config

        # Mock S3VectorStore to raise an error
        mock_s3_store = Mock()
        mock_s3_store_class.return_value = mock_s3_store
        mock_s3_store.create_index_if_not_exists.side_effect = Exception("AWS Error")

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
        with pytest.raises(RuntimeError, match="Failed to write to S3 Vector Store: AWS Error"):
            await write_to_s3_vector_store_activity(chunks, "test-index", create_index=True, batch_size=100)

    @patch("awa.core.activities.write_to_s3_vector_store.ConfigLoader")
    @patch("awa.core.activities.write_to_s3_vector_store.S3VectorStore")
    async def test_write_to_s3_vector_store_activity_skip_chunks_without_embeddings(
        self,
        mock_s3_store_class: Mock,
        mock_config_loader: Mock,
    ) -> None:
        """Test S3 Vector Store write skips chunks without embeddings."""
        # Mock configuration with proper string values
        mock_config = Mock()
        mock_s3_vector_config = Mock()
        mock_s3_vector_config.enabled = True
        mock_s3_vector_config.region_name = "us-east-2"
        mock_s3_vector_config.vector_bucket_name = "test-bucket"
        mock_s3_vector_config.index_name = "test-index"
        mock_s3_vector_config.embedding_source = "openai"
        mock_config.s3_vector = mock_s3_vector_config
        mock_config_loader.get_config.return_value = mock_config

        # Mock S3VectorStore
        mock_s3_store = Mock()
        mock_s3_store_class.return_value = mock_s3_store
        mock_s3_store.create_index_if_not_exists.return_value = {"status": "exists"}
        mock_s3_store.batch_put_vectors.return_value = [{"status": "success"}]

        # Test data with mixed chunks (some with/without embeddings)
        chunks = [
            ChunkInfo(
                chunk_id="chunk_1",
                text="Test content with embedding",
                token_count=3,
                start_index=0,
                end_index=12,
                embedding_vector=[0.1, 0.2, 0.3],
            ),
            ChunkInfo(
                chunk_id="chunk_2",
                text="Test content without embedding",
                token_count=3,
                start_index=0,
                end_index=12,
                # No embedding_vector
            ),
        ]

        # Test the activity
        result = await write_to_s3_vector_store_activity(chunks, "test-index", create_index=True, batch_size=100)

        # Verify results - only 1 chunk with embedding should be written
        assert result["vectors_written"] == 1
        assert result["index_name"] == "test-index"
        assert result["created_index"] is True
        assert result["skipped"] is False

        # Verify only 1 vector was passed to batch_put_vectors
        mock_s3_store.batch_put_vectors.assert_called_once()
        call_args = mock_s3_store.batch_put_vectors.call_args
        vectors = call_args.args[0]
        assert len(vectors) == 1
