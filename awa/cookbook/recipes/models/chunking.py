"""Data models for chunking and summarization functionality."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChunkingStrategy(str, Enum):
    """Strategy for how to chunk content."""

    LIST_ITEMS = "list_items"  # Chunk by list items (e.g., file descriptions)
    CONTENT_SIZE = "content_size"  # Chunk by raw content size
    HYBRID = "hybrid"  # Use list items but respect size limits


class ChunkAndSummarizeInput(BaseModel):
    """Input configuration for the chunk and summarize workflow."""

    content_items: list[str] = Field(
        default_factory=list,
        description="List of content items to potentially chunk and summarize",
    )
    max_content_length: int = Field(
        default=50000,  # ~12k tokens for GPT-4
        description="Maximum total character length before chunking is triggered",
    )
    max_chunk_length: int = Field(
        default=20000,  # ~5k tokens per chunk
        description="Maximum character length per chunk",
    )
    chunking_strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.LIST_ITEMS,
        description="Strategy for how to chunk the content",
    )
    context_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context data to pass to BAML transforms",
    )
    baml_path: str = Field(
        default="",
        description="Path to BAML file containing summarization functions (empty string if not provided)",
    )
    chunk_summary_function: str = Field(
        default="SummarizeChunk",
        description="Name of BAML function to summarize individual chunks",
    )
    final_summary_function: str = Field(
        default="SummarizeFinal",
        description="Name of BAML function to create final summary from chunk summaries",
    )
    preserve_structure: bool = Field(
        default=True,
        description="Whether to preserve the original structure in summaries",
    )
    iterative_summarization: bool = Field(
        default=True,
        description="Whether to iteratively summarize if summaries exceed max length",
    )


class ChunkAndSummarizeResult(BaseModel):
    """Result from the chunk and summarize workflow."""

    final_summary: str = Field(description="The final summarized content")
    chunk_summaries: list[str] = Field(
        default_factory=list,
        description="Individual chunk summaries (if chunking was needed)",
    )
    was_chunked: bool = Field(
        default=False,
        description="Whether the content was chunked",
    )
    num_chunks: int = Field(default=1, description="Number of chunks created")
    total_original_length: int = Field(
        default=0,
        description="Total character length of original content",
    )
    iterations_performed: int = Field(
        default=0,
        description="Number of summarization iterations performed",
    )


class ContentChunk(BaseModel):
    """Represents a single chunk of content."""

    items: list[str] = Field(description="Content items in this chunk")
    chunk_index: int = Field(description="Index of this chunk")
    total_chunks: int = Field(description="Total number of chunks")
    character_count: int = Field(description="Total character count in this chunk")
