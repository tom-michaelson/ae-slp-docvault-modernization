# OpenAI and Azure OpenAI Embeddings in AWA

AWA now supports OpenAI and Azure OpenAI embeddings as alternatives to the default TF-IDF-SVD approach. This provides higher quality semantic understanding for production use cases.

## Overview

The `generate_embeddings_activity` supports multiple embedding models with **required explicit specification**:

- **`tfidf-svd`**: Local TF-IDF + SVD approach, no API key required
- **`text-embedding-ada-002`**: OpenAI's Ada embedding model (1536 dimensions)
- **`text-embedding-3-small`**: OpenAI's 3-Small embedding model (1536 dimensions)
- **`text-embedding-3-large`**: OpenAI's 3-Large embedding model (3072 dimensions)
- **`azure-text-embedding-ada-002`**: Azure OpenAI's Ada embedding model (1536 dimensions)

**Important:** Starting from recent versions, you must explicitly specify which embedding model to use. The system will fail with clear error messages if the specified model cannot be configured, preventing silent fallbacks or unexpected behavior.

## Supported Models

AWA supports the following embedding models:

### OpenAI Models

- `text-embedding-ada-002` - OpenAI's Ada embedding model (1536 dimensions)
- `text-embedding-3-small` - OpenAI's 3-Small embedding model (1536 dimensions)
- `text-embedding-3-large` - OpenAI's 3-Large embedding model (3072 dimensions)

### Azure OpenAI Models

- `azure-text-embedding-ada-002` - Azure OpenAI's Ada embedding model (1536 dimensions)

### Local Models

- `tfidf-svd` - Local TF-IDF + SVD approach (configurable dimensions)

## Configuration

### 1. Set Environment Variables

Set your API keys in your `.env` file:

```bash
# For OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# For Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
```

### 2. Configure in config.yaml

Configure embedding models in your `config.yaml` using the `embedding_models` section:

```yaml
# Embedding model configuration
embedding_models:
  - name: azure-text-embedding-ada-002
    provider: azureopenai
    resource_name: openai-ampf-finra-poc  # Azure OpenAI resource name
    api_version: "2023-05-15"             # Azure OpenAI API version
    model: text-embedding-ada-002         # The actual model name
  - name: text-embedding-ada-002
    provider: openai
    model: text-embedding-ada-002
  - name: tfidf-svd
    provider: tfidf
    model: tfidf-svd

# Optional: LLM provider configuration for other models
llm:
  providers:
    openai: {} # OpenAI provider configuration
    azure_openai:
      resource_name: my-azure-openai
      api_version: "2024-02-15-preview"
```

## Usage

### Basic Usage

```python
from awa.core.activities.generate_embeddings import generate_embeddings_activity

# Use default TF-IDF-SVD (local, no API key)
result = await generate_embeddings_activity(
    chunks,
    embedding_model="tfidf-svd",
    vector_dimension=128,
)
# Access chunks with embeddings
chunks_with_embeddings = result.chunks
print(f"Model: {result.actual_model}, Provider: {result.actual_provider}")

# Use OpenAI embeddings (requires API key)
try:
    result = await generate_embeddings_activity(
        chunks,
        embedding_model="text-embedding-ada-002",
        vector_dimension=128,
    )
    chunks_with_embeddings = result.chunks
    print(f"Provider: {result.actual_provider}")
except RuntimeError as e:
    print(f"Embedding model configuration error: {e}")

# Use Azure OpenAI embeddings (requires API key and config)
try:
    result = await generate_embeddings_activity(
        chunks,
        embedding_model="azure-text-embedding-ada-002",
        vector_dimension=128,
    )
    chunks_with_embeddings = result.chunks
    print(f"Successfully configured Azure OpenAI embeddings")
except RuntimeError as e:
    print(f"Azure OpenAI configuration error: {e}")
```

### Workflow Configuration

When using the `VectorDatabaseIngestionWorkflow`, you can now specify your preferred embedding model and vector dimension:

```python
from awa.core.models.vector_ingestion_input import VectorIngestionInput

# Configure for OpenAI embeddings
workflow_input = VectorIngestionInput(
    input_directory="path/to/documents",
    output_directory="path/to/output",
    embedding_model="text-embedding-ada-002",  # Use OpenAI
    vector_dimension=256,  # Custom dimension
    chunk_size=512,
    chunk_overlap=50,
)

# Configure for Azure OpenAI embeddings
workflow_input = VectorIngestionInput(
    input_directory="path/to/documents",
    output_directory="path/to/output",
    embedding_model="azure-text-embedding-ada-002",  # Use Azure OpenAI
    vector_dimension=256,  # Custom dimension
    chunk_size=512,
    chunk_overlap=50,
)

# Configure for local TF-IDF-SVD embeddings
workflow_input = VectorIngestionInput(
    input_directory="path/to/documents",
    output_directory="path/to/output",
    embedding_model="tfidf-svd",  # Use local processing
    vector_dimension=128,  # Custom dimension
    chunk_size=512,
    chunk_overlap=50,
)
```

### In Workflows

```python
# In your workflow
embedding_result = await workflow.execute_activity(
    generate_embeddings_activity,
    args=[
        all_chunks,
        workflow_input.embedding_model,  # Use embedding model from input
        workflow_input.vector_dimension,  # Use vector dimension from input
    ],
    start_to_close_timeout=timedelta(minutes=10),
)

# Access the chunks with embeddings
chunks_with_embeddings = embedding_result.chunks

# Log actual model used for tracking
workflow.logger.info(f"Embedding generation completed with {embedding_result.actual_provider}: {embedding_result.actual_model}")
```

**Important**: The `VectorDatabaseIngestionWorkflow` now properly respects the `embedding_model` and `vector_dimension` parameters from the input instead of hardcoding values. This means you can specify your preferred embedding model when calling the workflow.

## Enhanced Model Tracking and Metadata

AWA provides comprehensive tracking of embedding generation with clear error handling.

### EmbeddingResult Object

The `generate_embeddings_activity` returns an `EmbeddingResult` object that includes:

```python
class EmbeddingResult(BaseModel):
    chunks: list[ChunkInfo]           # List of chunks with embeddings
    actual_model: str                 # Model name that was actually used
    actual_provider: str              # Provider that was actually used
```

### Error Handling

Instead of silent fallbacks, the system now provides explicit error handling:

```python
try:
    result = await generate_embeddings_activity(chunks, "azure-text-embedding-ada-002", 128)
    print(f"Success: {result.actual_model} via {result.actual_provider}")
except RuntimeError as e:
    print(f"Configuration error: {e}")
    # Handle the error appropriately (e.g., use a different model, notify user, etc.)
```

### Metadata Files Enhanced

The vector ingestion workflow generates metadata files that show actual model information:

**ingestion_metadata.json**:
```json
{
  "input_directory": "/path/to/input",
  "output_directory": "/path/to/output",
  "embedding_model": "azure-text-embedding-ada-002",
  "actual_embedding_model": "text-embedding-ada-002",
  "actual_embedding_provider": "azureopenai",
  "vector_dimension": 128,
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

**ingestion_summary.txt**:
```
Vector Database Ingestion Summary
=================================

Input Directory: /path/to/input
Output Directory: /path/to/output
Embedding Model: text-embedding-ada-002 (azureopenai)
Vector Dimension: 128
```

### Configuration Error Detection

The system provides clear error messages for common configuration issues:

1. **Azure OpenAI Configuration Issues**: When Azure API key is missing or configuration is invalid
2. **OpenAI Configuration Issues**: When OpenAI API key is missing or model is unavailable
3. **Model Configuration Missing**: When embedding model configuration is not found in config.yaml
4. **Invalid Model Names**: When unsupported embedding models are specified

## Features

### Automatic Dimension Handling

- **Truncation**: If OpenAI/Azure OpenAI returns more dimensions than requested, embeddings are automatically truncated
- **Padding**: If OpenAI/Azure OpenAI returns fewer dimensions than requested, embeddings are padded with zeros
- **Normalization**: All embeddings are normalized to unit vectors for consistent similarity calculations

### Batch Processing

- Text chunks are processed in batches of 100 to avoid API rate limits
- Progress logging shows batch completion status
- Error handling for individual batch failures

### Error Handling

- **Fail-Fast Approach**: Clear error messages when embedding models cannot be configured
- **No Silent Fallbacks**: Explicit model specification prevents unexpected behavior
- **Configuration Validation**: Validates supported embedding models and required configuration
- **Detailed Error Messages**: Specific guidance for resolving configuration issues

## Examples

### OpenAI Embeddings

See `examples/openai_embeddings_example.py` for a complete working example.

```bash
# Set your API key
export OPENAI_API_KEY="your-key-here"

# Run the example
python examples/openai_embeddings_example.py
```

### Azure OpenAI Embeddings

See `examples/azure_openai_embeddings_example.py` for a complete working example.

```bash
# Set your API key
export AZURE_OPENAI_API_KEY="your-key-here"

# Run the example
python examples/azure_openai_embeddings_example.py
```

## When to Use Each Approach

### TF-IDF-SVD (Default)

- ✅ **Local processing** - no internet connection required
- ✅ **No API costs** - completely free
- ✅ **Fast** - processes text immediately
- ❌ **Basic semantic understanding** - word frequency based
- ❌ **Domain specific** - trained on your specific text corpus

### OpenAI Embeddings

- ✅ **High quality** - state-of-the-art semantic understanding
- ✅ **Domain agnostic** - works well across different text types
- ✅ **Consistent** - same text always produces same embedding
- ❌ **API costs** - charges per token processed
- ❌ **Internet required** - needs OpenAI API access
- ❌ **Rate limits** - API has request limits

### Azure OpenAI Embeddings

- ✅ **High quality** - same models as OpenAI with enterprise features
- ✅ **Enterprise ready** - Azure security and compliance
- ✅ **Consistent** - same text always produces same embedding
- ✅ **Azure integration** - works with Azure services
- ❌ **API costs** - charges per token processed
- ❌ **Internet required** - needs Azure OpenAI API access
- ❌ **Rate limits** - API has request limits
- ❌ **Configuration required** - needs Azure OpenAI setup
