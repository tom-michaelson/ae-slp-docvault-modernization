"""Models for content chunking strategies."""

from enum import Enum

from pydantic import BaseModel, Field


class ChunkingStrategy(str, Enum):
    """Strategy for chunking content."""

    LIST_ITEMS = "list_items"
    CONTENT_SIZE = "content_size"
    HYBRID = "hybrid"


class ContentChunk(BaseModel):
    """Represents a chunk of content."""

    items: list[str] = Field(description="List of content items in this chunk")
    chunk_index: int = Field(description="Index of this chunk (1-based)")
    total_chunks: int = Field(description="Total number of chunks")
    character_count: int = Field(description="Total character count in this chunk")
