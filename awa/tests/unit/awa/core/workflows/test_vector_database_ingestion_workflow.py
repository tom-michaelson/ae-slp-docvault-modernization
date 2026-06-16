"""Unit tests for vector database ingestion workflow."""

import pytest

from awa.core.models.vector_ingestion_input import VectorIngestionInput
from awa.core.workflows.vector_database_ingestion_workflow import VectorDatabaseIngestionWorkflow


class TestVectorDatabaseIngestionWorkflow:
    """Test cases for VectorDatabaseIngestionWorkflow."""

    def test_workflow_creation(self) -> None:
        """Test that the workflow class can be created."""
        workflow = VectorDatabaseIngestionWorkflow()
        assert workflow is not None

    def test_workflow_input_validation(self) -> None:
        """Test that workflow input model validation works."""
        # Test valid input
        input_data = VectorIngestionInput(
            input_directory="input/",
            output_directory="output/",
            embedding_model="tfidf-svd",  # Now required
        )

        assert input_data.input_directory == "input/"
        assert input_data.output_directory == "output/"
        assert input_data.embedding_model == "tfidf-svd"
        assert input_data.vector_db_type == "chroma"

    def test_workflow_input_with_custom_settings(self) -> None:
        """Test workflow input with custom settings."""
        input_data = VectorIngestionInput(
            input_directory="docs/",
            output_directory="results/",
            chunk_size=1024,
            chunk_overlap=100,
            embedding_model="text-embedding-3-small",
            vector_db_type="lancedb",
            vector_dimension=256,
            max_files=5,
        )

        assert input_data.chunk_size == 1024
        assert input_data.chunk_overlap == 100
        assert input_data.embedding_model == "text-embedding-3-small"
        assert input_data.vector_db_type == "lancedb"
        assert input_data.vector_dimension == 256
        assert input_data.max_files == 5

    def test_workflow_input_s3_vector_store(self) -> None:
        """Test workflow input with S3 Vector Store configuration."""
        input_data = VectorIngestionInput(
            input_directory="docs/",
            output_directory="results/",
            chunk_size=1024,
            chunk_overlap=100,
            embedding_model="azure-text-embedding-ada-002",
            vector_db_type="s3_vector",
            vector_dimension=1536,
            include_metadata=True,
        )

        assert input_data.vector_db_type == "s3_vector"
        assert input_data.embedding_model == "azure-text-embedding-ada-002"
        assert input_data.vector_dimension == 1536
        assert input_data.include_metadata is True

    def test_workflow_input_s3_vector_with_tfidf(self) -> None:
        """Test workflow input with S3 Vector Store and TF-IDF embeddings."""
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

    def test_workflow_input_validation_constraints(self) -> None:
        """Test that input validation constraints work properly."""
        # Test chunk_size constraints
        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                chunk_size=50,  # Below minimum
            )

        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                chunk_size=3000,  # Above maximum
            )

        # Test chunk_overlap constraints
        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                chunk_overlap=-10,  # Below minimum
            )

        # Test max_files constraints
        with pytest.raises(ValueError):
            VectorIngestionInput(
                input_directory="input/",
                output_directory="output/",
                embedding_model="tfidf-svd",
                max_files=0,  # Below minimum
            )
