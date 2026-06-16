"""Models for document chunking with Chonkie."""

from enum import Enum

from pydantic import BaseModel, Field


class ChunkerType(str, Enum):
    """Available chunker types in Chonkie (base package only, no torch dependency)."""

    TOKEN = "token"  # noqa: S105
    SENTENCE = "sentence"
    RECURSIVE = "recursive"
    # The following chunkers require additional dependencies:
    # SEMANTIC = "semantic"  # Requires torch via sentence-transformers
    # SDPM = "sdpm"  # Requires torch via sentence-transformers
    # LATE = "late"  # Requires torch via sentence-transformers
    # CODE = "code"  # Requires tree-sitter, magika
    # NEURAL = "neural"  # Requires torch via transformers
    # SLUMBER = "slumber"  # Requires torch via transformers


class ChunkDocumentInput(BaseModel):
    """Input model for document chunking activity."""

    content: str = Field(description="The text content to be chunked")
    chunker_type: ChunkerType = Field(
        default=ChunkerType.RECURSIVE,
        description="The type of chunker to use",
    )
    max_chunk_size: int | None = Field(
        default=None,
        description="Maximum size of each chunk (in tokens)",
    )
    chunk_overlap: int | None = Field(
        default=None,
        description="Number of tokens to overlap between chunks",
    )


class ChunkResult(BaseModel):
    """Model representing a single chunk result."""

    text: str = Field(description="The text content of the chunk")
    token_count: int = Field(description="Number of tokens in the chunk")
    start_index: int = Field(description="Starting character index in original text")
    end_index: int = Field(description="Ending character index in original text")


class ChunkDocumentOutput(BaseModel):
    """Output model for document chunking activity."""

    chunks: list[ChunkResult] = Field(
        description="List of chunks with their metadata",
    )
    total_chunks: int = Field(description="Total number of chunks created")
    chunker_used: str = Field(description="The chunker type that was used")
