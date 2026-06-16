"""Input model for vector database ingestion workflow."""

from pydantic import BaseModel, Field


class VectorIngestionInput(BaseModel):
    """Input model for vector database ingestion workflow.

    This model defines the configuration for ingesting documents into a vector database,
    including file paths, chunking parameters, embedding model, and vector database settings.
    """

    input_directory: str = Field(
        description="Directory containing files to ingest",
        examples=["input/", "/path/to/documents/"],
    )

    output_directory: str = Field(
        description="Directory to store ingestion results and metadata",
        examples=["output/", "/path/to/results/"],
    )

    chunk_size: int = Field(
        default=512,
        description="Maximum number of tokens per chunk",
        ge=100,
        le=2000,
    )

    chunk_overlap: int = Field(
        default=50,
        description="Number of tokens to overlap between chunks",
        ge=0,
        le=200,
    )

    embedding_model: str = Field(
        description=(
            "Type of embedding model to use (required). Must specify one of: 'tfidf-svd', "
            "OpenAI models, or Azure OpenAI models."
        ),
        examples=[
            "tfidf-svd",
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large",
            "azure-text-embedding-ada-002",
        ],
    )

    vector_dimension: int = Field(
        default=128,
        description="Dimension of the embedding vectors to generate",
        ge=64,
        le=4096,
    )

    vector_db_type: str = Field(
        default="chroma",
        description="Type of vector database to use",
        examples=["chroma", "lancedb", "pinecone"],
    )

    vector_db_path: str | None = Field(
        default=None,
        description="Path or connection string for vector database",
        examples=["./chroma_db", "postgresql://user:pass@localhost/vectordb"],
    )

    include_metadata: bool = Field(
        default=True,
        description="Whether to include document metadata with embeddings",
    )

    max_files: int | None = Field(
        default=None,
        description="Maximum number of files to process (for testing)",
        ge=1,
    )
