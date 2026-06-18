"""Utilities for chunking content intelligently."""

from awa.core.models.chunking import ChunkingStrategy, ContentChunk


def create_chunks(
    content_items: list[str],
    max_chunk_length: int,
    strategy: ChunkingStrategy = ChunkingStrategy.LIST_ITEMS,
) -> list[ContentChunk]:
    """Create chunks from content items based on the specified strategy.

    Args:
        content_items: List of content items to chunk
        max_chunk_length: Maximum character length per chunk
        strategy: Chunking strategy to use

    Returns:
        List of ContentChunk objects

    """
    if not content_items:
        return []

    if strategy == ChunkingStrategy.LIST_ITEMS:
        return _chunk_by_items(content_items, max_chunk_length)
    if strategy == ChunkingStrategy.CONTENT_SIZE:
        return _chunk_by_size(content_items, max_chunk_length)
    # HYBRID
    return _chunk_hybrid(content_items, max_chunk_length)


def _chunk_by_items(content_items: list[str], max_chunk_length: int) -> list[ContentChunk]:
    """Chunk content by keeping items together up to max length.

    This is the preferred strategy for file/directory descriptions.
    """
    chunks = []
    current_chunk_items = []
    current_chunk_size = 0

    for item in content_items:
        item_size = len(item)

        # If adding this item would exceed the limit, start a new chunk
        if current_chunk_size + item_size > max_chunk_length and current_chunk_items:
            chunks.append(current_chunk_items)
            current_chunk_items = []
            current_chunk_size = 0

        # Handle case where single item exceeds max length
        if item_size > max_chunk_length:
            # If we have items in current chunk, save them first
            if current_chunk_items:
                chunks.append(current_chunk_items)
                current_chunk_items = []
                current_chunk_size = 0

            # Split the large item
            split_items = _split_large_item(item, max_chunk_length)
            chunks.extend([[split_item] for split_item in split_items[:-1]])

            # Continue with the last piece
            current_chunk_items = [split_items[-1]]
            current_chunk_size = len(split_items[-1])
        else:
            current_chunk_items.append(item)
            current_chunk_size += item_size

    # Add the last chunk if it has content
    if current_chunk_items:
        chunks.append(current_chunk_items)

    # Convert to ContentChunk objects
    total_chunks = len(chunks)
    return [
        ContentChunk(
            items=chunk_items,
            chunk_index=idx + 1,
            total_chunks=total_chunks,
            character_count=sum(len(item) for item in chunk_items),
        )
        for idx, chunk_items in enumerate(chunks)
    ]


def _chunk_by_size(content_items: list[str], max_chunk_length: int) -> list[ContentChunk]:
    """Chunk content purely by size, potentially splitting items.

    This strategy may split items across chunks.
    """
    # Join all items and split by size
    full_content = "\n".join(content_items)

    chunks = []
    for i in range(0, len(full_content), max_chunk_length):
        chunk_text = full_content[i : i + max_chunk_length]
        chunks.append([chunk_text])

    total_chunks = len(chunks)
    return [
        ContentChunk(
            items=chunk_items,
            chunk_index=idx + 1,
            total_chunks=total_chunks,
            character_count=sum(len(item) for item in chunk_items),
        )
        for idx, chunk_items in enumerate(chunks)
    ]


def _chunk_hybrid(content_items: list[str], max_chunk_length: int) -> list[ContentChunk]:
    """Hybrid approach: prefer keeping items together but split if necessary.

    Similar to _chunk_by_items but more aggressive about fitting content.
    """
    # For now, use the same logic as chunk_by_items
    # This could be enhanced with more sophisticated strategies
    return _chunk_by_items(content_items, max_chunk_length)


def _split_large_item(item: str, max_length: int) -> list[str]:
    """Split a large item into smaller pieces.

    Tries to split at natural boundaries (newlines, sentences) if possible.
    """
    if len(item) <= max_length:
        return [item]

    pieces = []
    remaining = item

    while remaining:
        if len(remaining) <= max_length:
            pieces.append(remaining)
            break

        # Try to find a good split point
        chunk = remaining[:max_length]

        # Look for newline near the end
        last_newline = chunk.rfind("\n", int(max_length * 0.8))
        if last_newline > 0:
            pieces.append(remaining[:last_newline])
            remaining = remaining[last_newline + 1 :]
            continue

        # Look for sentence end
        for delimiter in [". ", "! ", "? ", "; "]:
            last_delimiter = chunk.rfind(delimiter, int(max_length * 0.8))
            if last_delimiter > 0:
                pieces.append(remaining[: last_delimiter + 1])
                remaining = remaining[last_delimiter + 1 :].lstrip()
                break
        else:
            # No good split point, just split at max length
            pieces.append(remaining[:max_length])
            remaining = remaining[max_length:]

    return pieces


def calculate_total_length(content_items: list[str]) -> int:
    """Calculate the total character length of all content items."""
    return sum(len(item) for item in content_items)


def needs_chunking(content_items: list[str], max_content_length: int) -> bool:
    """Determine if content needs to be chunked."""
    return calculate_total_length(content_items) > max_content_length
