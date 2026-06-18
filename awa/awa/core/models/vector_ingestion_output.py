"""Output model for vector database ingestion workflow."""

from datetime import datetime

from pydantic import BaseModel, Field


class EmbeddingResult(BaseModel):
    """Result of embedding generation including actual model used."""

    chunks: list["ChunkInfo"] = Field(description="List of chunks with embeddings")
    actual_model: str = Field(description="Model name that was actually used")
    actual_provider: str = Field(description="Provider that was actually used (e.g., azureopenai, openai, tfidf)")


class DocumentMetadata(BaseModel):
    """Metadata for a processed document."""

    file_path: str = Field(description="Path to the original document")
    file_size: int = Field(description="Size of the file in bytes")
    file_type: str = Field(description="Type of the document (e.g., pdf, docx)")
    processed_at: datetime = Field(description="Timestamp when document was processed")
    chunk_count: int = Field(description="Number of chunks created from the document")
    embedding_count: int = Field(description="Number of embeddings generated")


class ChunkInfo(BaseModel):
    """Information about a document chunk."""

    chunk_id: str = Field(description="Unique identifier for the chunk")
    text: str = Field(description="Text content of the chunk")
    token_count: int = Field(description="Number of tokens in the chunk")
    start_index: int = Field(description="Starting position in original document")
    end_index: int = Field(description="Ending position in original document")
    embedding_vector: list[float] | None = Field(
        default=None,
        description="Embedding vector for the chunk",
    )


class VectorIngestionOutput(BaseModel):
    """Output model for vector database ingestion workflow.

    This model provides comprehensive information about the ingestion process,
    including metadata about processed documents, chunking results, and
    vector database storage information.
    """

    # Overall process information
    total_documents_processed: int = Field(
        description="Total number of documents successfully processed",
    )

    total_chunks_created: int = Field(
        description="Total number of chunks created across all documents",
    )

    total_embeddings_generated: int = Field(
        description="Total number of embeddings generated and stored",
    )

    # Processing details
    documents_metadata: list[DocumentMetadata] = Field(
        description="Metadata for each processed document",
    )

    chunks_info: list[ChunkInfo] = Field(
        description="Information about all chunks created",
    )

    # Vector database information
    vector_db_type: str = Field(description="Type of vector database used")
    vector_db_path: str = Field(description="Path or connection to vector database")
    collection_name: str = Field(description="Name of the collection created")

    # Output files
    output_directory: str = Field(description="Directory where results were stored")
    metadata_file: str = Field(description="Path to the metadata JSON file")
    summary_file: str = Field(description="Path to the summary report file")

    # Timing information
    processing_start_time: datetime = Field(description="When processing began")
    processing_end_time: datetime = Field(description="When processing completed")
    total_processing_time_seconds: float = Field(description="Total processing time in seconds")

    # Configuration used
    chunk_size: int = Field(description="Chunk size used for processing")
    chunk_overlap: int = Field(description="Chunk overlap used for processing")
    embedding_model: str = Field(description="Embedding model used")

    # Status information
    success: bool = Field(description="Whether the entire process succeeded")
    errors: list[str] = Field(
        default_factory=list,
        description="List of any errors encountered during processing",
    )

    @property
    def average_chunks_per_document(self) -> float:
        """Calculate average chunks per document."""
        if self.total_documents_processed == 0:
            return 0.0
        return self.total_chunks_created / self.total_documents_processed

    @property
    def processing_rate_chunks_per_second(self) -> float:
        """Calculate chunks processed per second."""
        if self.total_processing_time_seconds == 0:
            return 0.0
        return self.total_chunks_created / self.total_processing_time_seconds
