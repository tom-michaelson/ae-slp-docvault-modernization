# Document Chunking with Chonkie

The AWA Document Chunking feature enables intelligent segmentation of large documents into smaller, manageable chunks optimized for Large Language Model (LLM) processing. This feature is powered by the [Chonkie library](https://github.com/chonkie-ai/chonkie) and integrates seamlessly with AWA's workflow system.

## Overview

The `chunk_document` activity provides flexible document chunking strategies to split text into appropriately sized segments while maintaining semantic coherence. This is essential for processing large documents that exceed LLM context windows or for implementing retrieval-augmented generation (RAG) pipelines.

## Chunking Strategies

AWA supports three chunking strategies from the Chonkie library:

### Token Chunker

- **Type**: `token`
- **Description**: Splits text into fixed-size chunks based on token count
- **Best for**: Simple, consistent chunking when semantic boundaries are less important
- **Parameters**: `max_chunk_size`, `chunk_overlap`

### Sentence Chunker

- **Type**: `sentence`
- **Description**: Splits text at sentence boundaries, respecting linguistic structure
- **Best for**: Maintaining complete thoughts and grammatical coherence
- **Parameters**: `max_chunk_size`, `chunk_overlap`

### Recursive Chunker (Default)

- **Type**: `recursive`
- **Description**: Hierarchically splits text using multiple separators (paragraphs, sentences, words)
- **Best for**: Preserving semantic meaning and document structure
- **Parameters**: `max_chunk_size`, `chunk_overlap`

## Usage

See the Activity reference documentation for [chunk-document](/reference/activity/chunk-document.md).

## How It Works

1. **Content Input**: Accepts text content from any source (files, API responses, etc.)
2. **Strategy Selection**: Choose appropriate chunking strategy based on use case
3. **Chunking Process**: Applies the selected chunker with specified parameters
4. **Metadata Enrichment**: Each chunk includes token count and position information
5. **Output Structure**: Returns structured chunks ready for downstream processing

## Workflow Integration

The document chunking functionality is available as both an activity and a workflow:

- **Activity**: `chunk_document` - Direct execution for simple use cases
- **Workflow**: `ChunkDocumentWorkflow` - Provides workflow-level orchestration

### Using the Workflow

The `ChunkDocumentWorkflow` wraps the chunking activity to enable:

- Workflow-level retries and error handling
- Integration with other workflows as a child workflow
- Future extensibility for caching and batch processing

```python
from awa.core.workflows.chunk_document_workflow import ChunkDocumentWorkflow
from awa.sdk.models.chunking_models import ChunkDocumentInput, ChunkerType

# Execute the workflow
result = await workflow_client.execute_workflow(
    ChunkDocumentWorkflow.run,
    ChunkDocumentInput(
        content="Your long document text here...",
        chunker_type=ChunkerType.RECURSIVE,
        max_chunk_size=512,
        chunk_overlap=50
    ),
    id="chunk-document-123",
    task_queue=TASK_QUEUE_AGENT_OPERATIONS,
)

# Access results
for chunk in result.chunks:
    print(f"Chunk: {chunk.text[:50]}...")
    print(f"Tokens: {chunk.token_count}")
    print(f"Position: {chunk.start_index}-{chunk.end_index}")
```

### Using WorkflowUtils

For convenience within workflows, use the `WorkflowUtils.chunk_document` method:

```python
from awa.sdk.utils.workflow_utils import WorkflowUtils
from awa.sdk.models.chunking_models import ChunkerType

# Within a workflow
result = await WorkflowUtils.chunk_document(
    content=document_text,
    chunker_type=ChunkerType.RECURSIVE,
    max_chunk_size=512,
    chunk_overlap=50
)

# Process chunks
for chunk in result.chunks:
    # Send each chunk to LLM for processing
    await process_chunk(chunk.text)
```

## Common Use Cases

### 1. RAG Pipeline Integration

```python
# Read and parse document
content = await WorkflowUtils.read_file_and_parse("docs/technical-manual.pdf")

# Chunk for vector database ingestion
chunks = await WorkflowUtils.chunk_document(
    content=content,
    chunker_type=ChunkerType.RECURSIVE,
    max_chunk_size=512,  # Optimal for most embedding models
    chunk_overlap=50     # Ensure context continuity
)

# Store chunks in vector database
for chunk in chunks.chunks:
    await store_in_vector_db(chunk.text, metadata={
        "source": "technical-manual.pdf",
        "position": f"{chunk.start_index}-{chunk.end_index}",
        "tokens": chunk.token_count
    })
```

### 2. Long Document Summarization

```python
# Chunk large document for parallel processing
chunks = await WorkflowUtils.chunk_document(
    content=long_document,
    chunker_type=ChunkerType.SENTENCE,
    max_chunk_size=2048  # Larger chunks for summarization
)

# Summarize each chunk in parallel
summaries = await workflow.gather(
    [summarize_chunk(chunk.text) for chunk in chunks.chunks]
)

# Combine summaries
final_summary = await combine_summaries(summaries)
```

### 3. Context Window Management

```python
# Ensure content fits within LLM context window
chunks = await WorkflowUtils.chunk_document(
    content=user_content,
    chunker_type=ChunkerType.TOKEN,
    max_chunk_size=3500,  # Leave room for system prompt
    chunk_overlap=200     # Maintain context between chunks
)

# Process chunks sequentially with context
previous_response = ""
for chunk in chunks.chunks:
    response = await process_with_llm(
        chunk.text,
        previous_context=previous_response[-500:]  # Carry forward context
    )
    previous_response = response
```

## Best Practices

1. **Choose the Right Chunker**

   - Use `RECURSIVE` (default) for most general-purpose chunking
   - Use `SENTENCE` when maintaining complete thoughts is critical
   - Use `TOKEN` when you need precise control over chunk sizes

2. **Optimize Chunk Size**

   - For embeddings: 256-512 tokens typically work well
   - For LLM processing: Consider model context window minus prompt overhead
   - For summarization: Larger chunks (1000-2000 tokens) preserve more context

3. **Configure Overlap Wisely**

   - 10-20% overlap helps maintain context continuity
   - Higher overlap for dense technical content
   - Lower overlap for narrative or conversational text

4. **Handle Edge Cases**
   - Empty content returns empty chunks array
   - Very small documents may return a single chunk
   - Chunks always include position metadata for reconstruction

## Integration with Document Parsing

Combine document parsing and chunking for complete document processing:

```python
# Parse document to markdown
parsed_content = await WorkflowUtils.read_file_and_parse("report.docx")

# Chunk the parsed content
chunks = await WorkflowUtils.chunk_document(
    content=parsed_content,
    chunker_type=ChunkerType.RECURSIVE,
    max_chunk_size=512
)

# Process chunks with LLM
results = []
for chunk in chunks.chunks:
    result = await analyze_chunk(chunk.text)
    results.append(result)
```

## Performance Considerations

- Chunking is CPU-bound and scales linearly with document size
- The RECURSIVE chunker has slightly higher overhead but produces better semantic chunks
- Consider batching multiple documents when processing large volumes
- Chunk metadata (positions, token counts) adds minimal memory overhead

## Future Enhancements

The current implementation uses Chonkie's base chunkers which don't require additional dependencies. Future versions may include:

- Semantic chunkers using embeddings (requires PyTorch)
- Code-aware chunkers for source code (requires tree-sitter)
- Neural chunkers using transformer models
- Caching mechanisms for frequently chunked content
- Batch processing capabilities for multiple documents
