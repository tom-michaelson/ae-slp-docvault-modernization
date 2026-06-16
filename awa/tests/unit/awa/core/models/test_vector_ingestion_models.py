"""Unit tests for vector ingestion models."""

from datetime import UTC, datetime

import pytest

from awa.core.models.vector_ingestion_input import VectorIngestionInput
from awa.core.models.vector_ingestion_output import (
    ChunkInfo,
    DocumentMetadata,
    VectorIngestionOutput,
)


class TestVectorIngestionInput:
    """Test cases for VectorIngestionInput model."""

    def test_valid_input(self) -> None:
        """Test creating a valid input model."""
        input_data = VectorIngestionInput(
            input_directory="input/",
            output_directory="output/",
            embedding_model="tfidf-svd",  # Now required
        )

        assert input_data.input_directory == "input/"
        assert input_data.output_directory == "output/"
        assert input_data.chunk_size == 512
        assert input_data.chunk_overlap == 50
        assert input_data.embedding_model == "tfidf-svd"
        assert input_data.vector_db_type == "chroma"
        assert input_data.include_metadata is True

    def test_custom_parameters(self) -> None:
        """Test creating input with custom parameters."""
        input_data = VectorIngestionInput(
            input_directory="docs/",
            output_directory="results/",
            chunk_size=1024,
            chunk_overlap=100,
            embedding_model="text-embedding-3-small",
            vector_db_type="lancedb",
            max_files=10,
        )

        assert input_data.chunk_size == 1024
        assert input_data.chunk_overlap == 100
        assert input_data.embedding_model == "text-embedding-3-small"
        assert input_data.vector_db_type == "lancedb"
        assert input_data.max_files == 10

    def test_validation_constraints(self) -> None:
        """Test input validation constraints."""
        # Test chunk_size minimum
        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                chunk_size=50,  # Below minimum of 100
            )

        # Test chunk_size maximum
        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                chunk_size=3000,  # Above maximum of 2000
            )

        # Test chunk_overlap minimum
        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                chunk_overlap=-10,  # Below minimum of 0
            )

        # Test chunk_overlap maximum
        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                chunk_overlap=300,  # Above maximum of 200
            )

        # Test max_files minimum
        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                max_files=0,  # Below minimum of 1
            )

    def test_embedding_model_required(self) -> None:
        """Test that embedding_model is required."""
        # Test missing embedding_model
        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                # embedding_model is missing - should raise error
            )

    def test_s3_vector_store_configuration(self) -> None:
        """Test S3 Vector Store specific configurations."""
        # Test S3 Vector Store with TF-IDF
        input_data = VectorIngestionInput(
            input_directory="input/",
            output_directory="output/",
            embedding_model="tfidf-svd",
            vector_db_type="s3_vector",
            vector_dimension=128,
        )

        assert input_data.vector_db_type == "s3_vector"
        assert input_data.embedding_model == "tfidf-svd"
        assert input_data.vector_dimension == 128

        # Test S3 Vector Store with Azure OpenAI
        azure_input = VectorIngestionInput(
            input_directory="docs/",
            output_directory="results/",
            embedding_model="azure-text-embedding-ada-002",
            vector_db_type="s3_vector",
            vector_dimension=1536,
            chunk_size=1024,
            chunk_overlap=100,
            include_metadata=True,
        )

        assert azure_input.vector_db_type == "s3_vector"
        assert azure_input.embedding_model == "azure-text-embedding-ada-002"
        assert azure_input.vector_dimension == 1536
        assert azure_input.include_metadata is True

        # Test S3 Vector Store with OpenAI
        openai_input = VectorIngestionInput(
            input_directory="docs/",
            output_directory="results/",
            embedding_model="text-embedding-ada-002",
            vector_db_type="s3_vector",
            vector_dimension=1536,
        )

        assert openai_input.vector_db_type == "s3_vector"
        assert openai_input.embedding_model == "text-embedding-ada-002"
        assert openai_input.vector_dimension == 1536

    def test_supported_vector_db_types(self) -> None:
        """Test all supported vector database types."""
        supported_types = ["chroma", "lancedb", "pinecone", "s3_vector"]

        for db_type in supported_types:
            input_data = VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                vector_db_type=db_type,
            )
            assert input_data.vector_db_type == db_type

    def test_case_insensitive_vector_db_type(self) -> None:
        """Test that vector_db_type handling works correctly for routing."""
        # Test that the model accepts different cases
        test_cases = ["s3_vector", "S3_VECTOR", "S3_Vector", "chroma", "CHROMA"]

        for db_type in test_cases:
            input_data = VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                vector_db_type=db_type,
            )
            # Model stores the exact value provided
            assert input_data.vector_db_type == db_type
            # Routing logic should use lowercase comparison
            routes_to_s3 = input_data.vector_db_type.lower() == "s3_vector"
            expected_s3_routing = db_type.lower() == "s3_vector"
            assert routes_to_s3 == expected_s3_routing


class TestDocumentMetadata:
    """Test cases for DocumentMetadata model."""

    def test_valid_metadata(self) -> None:
        """Test creating valid document metadata."""
        now = datetime.now(tz=UTC)
        metadata = DocumentMetadata(
            file_path="test.txt",
            file_size=100,
            file_type=".txt",
            processed_at=now,
            chunk_count=1,
            embedding_count=1,
        )

        assert metadata.file_path == "test.txt"
        assert metadata.file_size == 100
        assert metadata.file_type == ".txt"
        assert metadata.processed_at == now
        assert metadata.chunk_count == 1
        assert metadata.embedding_count == 1

    def test_metadata_calculations(self) -> None:
        """Test metadata calculated properties."""
        now = datetime.now(tz=UTC)
        metadata = DocumentMetadata(
            file_path="test.txt",
            file_size=100,
            file_type=".txt",
            processed_at=now,
            chunk_count=5,
            embedding_count=3,
        )

        # Test that the model can be created and has the expected properties
        assert metadata.file_path == "test.txt"
        assert metadata.file_size == 100
        assert metadata.file_type == ".txt"
        assert metadata.chunk_count == 5
        assert metadata.embedding_count == 3
        assert metadata.processed_at == now


class TestChunkInfo:
    """Test cases for ChunkInfo model."""

    def test_valid_chunk(self) -> None:
        """Test creating a valid chunk."""
        chunk = ChunkInfo(
            chunk_id="chunk_1",
            text="This is a test chunk",
            token_count=5,
            start_index=0,
            end_index=20,
        )

        assert chunk.chunk_id == "chunk_1"
        assert chunk.text == "This is a test chunk"
        assert chunk.token_count == 5
        assert chunk.start_index == 0
        assert chunk.end_index == 20
        assert chunk.embedding_vector is None

    def test_chunk_with_embedding(self) -> None:
        """Test creating a chunk with embedding vector."""
        chunk = ChunkInfo(
            chunk_id="chunk_1",
            text="This is a test chunk",
            token_count=5,
            start_index=0,
            end_index=20,
            embedding_vector=[0.1, 0.2, 0.3],
        )

        assert chunk.embedding_vector == [0.1, 0.2, 0.3]


class TestVectorIngestionOutput:
    """Test cases for VectorIngestionOutput model."""

    def test_valid_output(self) -> None:
        """Test creating a valid output."""
        now = datetime.now(tz=UTC)
        doc_meta = DocumentMetadata(
            file_path="test.txt",
            file_size=100,
            file_type=".txt",
            processed_at=now,
            chunk_count=1,
            embedding_count=1,
        )

        chunk_info = ChunkInfo(
            chunk_id="chunk_1",
            text="Test content",
            token_count=3,
            start_index=0,
            end_index=12,
        )

        output = VectorIngestionOutput(
            total_documents_processed=1,
            total_chunks_created=1,
            total_embeddings_generated=1,
            documents_metadata=[doc_meta],
            chunks_info=[chunk_info],
            vector_db_type="chroma",
            vector_db_path="./test_chroma_db",
            collection_name="test_collection",
            output_directory="test-data/output/",
            metadata_file="test-data/output/metadata.json",
            summary_file="test-data/output/summary.txt",
            processing_start_time=now,
            processing_end_time=now,
            total_processing_time_seconds=1.0,
            chunk_size=512,
            chunk_overlap=50,
            embedding_model="text-embedding-ada-002",
            success=True,
            errors=[],
        )

        assert output.total_documents_processed == 1
        assert output.total_chunks_created == 1
        assert output.total_embeddings_generated == 1
        assert output.success is True
        assert output.errors == []

    def test_calculated_properties(self) -> None:
        """Test calculated properties."""
        now = datetime.now(tz=UTC)
        doc_meta = DocumentMetadata(
            file_path="test.txt",
            file_size=100,
            file_type=".txt",
            processed_at=now,
            chunk_count=5,
            embedding_count=3,
        )

        chunk_info = ChunkInfo(
            chunk_id="chunk_1",
            text="Test content",
            token_count=3,
            start_index=0,
            end_index=12,
        )

        output = VectorIngestionOutput(
            total_documents_processed=1,
            total_chunks_created=5,
            total_embeddings_generated=3,
            documents_metadata=[doc_meta],
            chunks_info=[chunk_info],
            vector_db_type="chroma",
            vector_db_path="./test_chroma_db",
            collection_name="test_collection",
            output_directory="test-data/output/",
            metadata_file="test-data/output/metadata.json",
            summary_file="test-data/output/summary.txt",
            processing_start_time=now,
            processing_end_time=now,
            total_processing_time_seconds=1.0,
            chunk_size=512,
            chunk_overlap=50,
            embedding_model="text-embedding-ada-002",
            success=True,
            errors=[],
        )

        # Test the actual calculated properties that exist
        assert output.average_chunks_per_document == 5.0  # 5/1
        assert output.processing_rate_chunks_per_second == 5.0  # 5/1

    def test_calculated_properties_edge_cases(self) -> None:
        """Test calculated properties with edge cases."""
        now = datetime.now(tz=UTC)
        doc_meta = DocumentMetadata(
            file_path="test.txt",
            file_size=100,
            file_type=".txt",
            processed_at=now,
            chunk_count=0,
            embedding_count=0,
        )

        output = VectorIngestionOutput(
            total_documents_processed=0,
            total_chunks_created=0,
            total_embeddings_generated=0,
            documents_metadata=[doc_meta],
            chunks_info=[],
            vector_db_type="chroma",
            vector_db_path="./test_chroma_db",
            collection_name="test_collection",
            output_directory="test-data/output/",
            metadata_file="test-data/output/metadata.json",
            summary_file="test-data/output/summary.txt",
            processing_start_time=now,
            processing_end_time=now,
            total_processing_time_seconds=0.0,
            chunk_size=512,
            chunk_overlap=50,
            embedding_model="text-embedding-ada-002",
            success=True,
            errors=[],
        )

        # Test division by zero handling for the actual properties
        assert output.average_chunks_per_document == 0.0
        assert output.processing_rate_chunks_per_second == 0.0
