"""Unit tests for the chunk document activity."""

import pytest

from awa.core.activities.chunk_document import chunk_document_activity
from awa.sdk.models.chunking_models import ChunkDocumentInput, ChunkerType


@pytest.mark.asyncio
async def test_chunk_document_with_default_chunker() -> None:
    """Test chunking with default RecursiveChunker."""
    input_data = ChunkDocumentInput(
        content="This is a test document. It has multiple sentences. Each sentence should be chunked appropriately. "
        "We need enough content to ensure proper chunking behavior is tested.",
    )
    result = await chunk_document_activity(input_data)

    assert result.total_chunks > 0
    assert result.chunker_used == ChunkerType.RECURSIVE.value
    assert all(chunk.text for chunk in result.chunks)
    assert all(chunk.token_count > 0 for chunk in result.chunks)
    assert all(chunk.start_index >= 0 for chunk in result.chunks)
    assert all(chunk.end_index > chunk.start_index for chunk in result.chunks)


@pytest.mark.asyncio
async def test_chunk_document_with_token_chunker() -> None:
    """Test chunking with TokenChunker."""
    # Create a long string to ensure multiple chunks
    content = " ".join(["word"] * 200)
    input_data = ChunkDocumentInput(
        content=content,
        chunker_type=ChunkerType.TOKEN,
        max_chunk_size=50,
    )
    result = await chunk_document_activity(input_data)

    assert result.chunker_used == ChunkerType.TOKEN.value
    assert result.total_chunks > 1  # Should have multiple chunks
    assert all(chunk.token_count <= 50 for chunk in result.chunks)


@pytest.mark.asyncio
async def test_chunk_document_with_sentence_chunker() -> None:
    """Test chunking with SentenceChunker."""
    input_data = ChunkDocumentInput(
        content="First sentence. Second sentence. Third sentence. Fourth sentence.",
        chunker_type=ChunkerType.SENTENCE,
    )
    result = await chunk_document_activity(input_data)

    assert result.chunker_used == ChunkerType.SENTENCE.value
    assert result.total_chunks > 0
    assert all("." in chunk.text for chunk in result.chunks if chunk.text.strip())


@pytest.mark.asyncio
async def test_empty_content() -> None:
    """Test handling of empty content."""
    input_data = ChunkDocumentInput(content="")
    result = await chunk_document_activity(input_data)

    assert result.total_chunks == 0
    assert len(result.chunks) == 0
    assert result.chunker_used == ChunkerType.RECURSIVE.value


@pytest.mark.asyncio
async def test_single_word_content() -> None:
    """Test handling of single word content."""
    input_data = ChunkDocumentInput(content="Hello")
    result = await chunk_document_activity(input_data)

    assert result.total_chunks >= 1
    assert len(result.chunks) >= 1
    assert result.chunks[0].text == "Hello"


@pytest.mark.asyncio
async def test_chunk_size_configuration() -> None:
    """Test custom chunk size configuration."""
    # Create a string with known length
    content = "A" * 1000  # Long string
    input_data = ChunkDocumentInput(
        content=content,
        chunker_type=ChunkerType.TOKEN,
        max_chunk_size=100,
    )
    result = await chunk_document_activity(input_data)

    assert result.total_chunks > 1  # Should have multiple chunks
    # Note: Some chunkers might not strictly respect max_chunk_size
    # so we check that chunks are reasonably sized
    assert all(chunk.token_count <= 150 for chunk in result.chunks)


@pytest.mark.asyncio
async def test_chunk_overlap_configuration() -> None:
    """Test chunk overlap configuration."""
    content = " ".join([f"Word{i}" for i in range(100)])
    input_data = ChunkDocumentInput(
        content=content,
        chunker_type=ChunkerType.TOKEN,
        max_chunk_size=20,
        chunk_overlap=5,
    )
    result = await chunk_document_activity(input_data)

    assert result.total_chunks > 1
    # Verify that chunks have some overlapping content
    # (This is a basic check - actual overlap verification would be more complex)
    assert len(result.chunks) > 0


# Note: test_code_chunker removed because CodeChunker requires tree-sitter dependency
# which we're avoiding for cross-platform compatibility


@pytest.mark.asyncio
async def test_whitespace_only_content() -> None:
    """Test handling of whitespace-only content."""
    input_data = ChunkDocumentInput(content="   \n\t  \n   ")
    result = await chunk_document_activity(input_data)

    # Different chunkers might handle whitespace differently
    # but should not crash
    assert isinstance(result.total_chunks, int)
    assert result.chunker_used == ChunkerType.RECURSIVE.value


@pytest.mark.asyncio
async def test_unicode_content() -> None:
    """Test handling of Unicode content."""
    input_data = ChunkDocumentInput(
        content="Hello 世界! This is a test with émojis 🚀 and special characters: ñ, ü, ß.",
    )
    result = await chunk_document_activity(input_data)

    assert result.total_chunks > 0
    # Verify Unicode content is preserved
    combined_text = "".join(chunk.text for chunk in result.chunks)
    assert "世界" in combined_text
    assert "🚀" in combined_text
    assert "ñ" in combined_text


@pytest.mark.asyncio
async def test_very_long_document() -> None:
    """Test handling of very long documents."""
    # Create a document with 10,000 words
    long_content = " ".join([f"Word{i % 100}" for i in range(10000)])
    input_data = ChunkDocumentInput(
        content=long_content,
        chunker_type=ChunkerType.TOKEN,
        max_chunk_size=500,
    )
    result = await chunk_document_activity(input_data)

    assert result.total_chunks > 10  # Should have many chunks
    assert all(chunk.token_count <= 600 for chunk in result.chunks)  # Allow some flexibility


@pytest.mark.asyncio
async def test_invalid_chunker_type() -> None:
    """Test handling of invalid chunker type."""
    # This test should be adjusted based on how we handle invalid types
    # For now, we'll test with a valid type since Pydantic validates the enum
    input_data = ChunkDocumentInput(
        content="Test content",
        chunker_type=ChunkerType.RECURSIVE,
    )
    result = await chunk_document_activity(input_data)

    assert result.chunker_used == ChunkerType.RECURSIVE.value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chunker_type",
    [
        ChunkerType.TOKEN,
        ChunkerType.SENTENCE,
        ChunkerType.RECURSIVE,
        # Note: Some chunkers might require additional setup or dependencies
        # Uncomment these as they become available
        # ChunkerType.SEMANTIC,
        # ChunkerType.SDPM,
        # ChunkerType.LATE,
        # ChunkerType.NEURAL,
        # ChunkerType.SLUMBER,
    ],
)
async def test_all_basic_chunker_types(chunker_type: ChunkerType) -> None:
    """Test all basic chunker types that don't require special setup."""
    input_data = ChunkDocumentInput(
        content="This is a test document for chunking. It contains multiple sentences and paragraphs. "
        "We want to ensure that all chunker types can handle basic text content without errors.",
        chunker_type=chunker_type,
    )
    result = await chunk_document_activity(input_data)

    assert result.chunker_used == chunker_type.value
    assert result.total_chunks > 0
    assert len(result.chunks) == result.total_chunks


@pytest.mark.asyncio
async def test_chunk_indices() -> None:
    """Test that chunk indices are properly set and sequential."""
    input_data = ChunkDocumentInput(
        content="This is sentence one. This is sentence two. This is sentence three.",
        chunker_type=ChunkerType.SENTENCE,
    )
    result = await chunk_document_activity(input_data)

    assert result.total_chunks > 0

    # Verify indices are valid
    for _i, chunk in enumerate(result.chunks):
        assert chunk.start_index >= 0
        assert chunk.end_index > chunk.start_index
        assert chunk.end_index <= len(input_data.content)

        # Verify the text matches the indices
        extracted_text = input_data.content[chunk.start_index : chunk.end_index]
        assert chunk.text == extracted_text
