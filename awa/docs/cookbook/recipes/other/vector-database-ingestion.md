# Vector Database Ingestion Workflow

A comprehensive workflow for ingesting documents into a vector database for RAG (Retrieval-Augmented Generation) applications. This workflow demonstrates an end-to-end process for preparing RAG corpora by processing documents, chunking them, generating embeddings, and storing them in vector databases.

## Overview

The Vector Database Ingestion Workflow is designed to transform raw documents into searchable vector embeddings. It reuses existing AWA building blocks for file parsing and document chunking, then adds embedding generation and vector database storage capabilities. This workflow provides a simple, pluggable example that can be extended for production use.

## Key Features

- **Multi-format Support**: Handles PDF, DOCX, TXT, MD, HTML, and CSV files
- **Flexible Chunking**: Configurable chunk size and overlap for optimal RAG performance
- **Multiple Embedding Models**: Supports TF-IDF, OpenAI, and Azure OpenAI models
- **Vector Database Integration**: Compatible with Chroma, LanceDB, and Pinecone
- **Comprehensive Metadata**: Tracks processing details and generates detailed reports
- **Error Handling**: Graceful failure handling with detailed error reporting
- **Scalable Processing**: Configurable file limits and batch processing

## How It Works

1. **File Discovery**: Lists and filters files in the input directory by supported extensions
2. **Document Processing**: Reads and parses each file using the ReadFileAndParseWorkflow
3. **Content Chunking**: Splits documents into manageable chunks using the ChunkDocumentWorkflow
4. **Embedding Generation**: Creates vector embeddings for each chunk using the specified model
5. **Vector Storage**: Stores embeddings in the configured vector database
6. **Output Generation**: Creates metadata files and summary reports for tracking

## Usage

### Input

The workflow accepts a `VectorIngestionInput` object with the following parameters:

| Name               | Type          | Default       | Description                               | Examples                                                                    |
| ------------------ | ------------- | ------------- | ----------------------------------------- | --------------------------------------------------------------------------- |
| `input_directory`  | `str`         | Required      | Directory containing files to ingest      | `"input/", "/path/to/documents/"`                                           |
| `output_directory` | `str`         | Required      | Directory to store results and metadata   | `"output/", "/path/to/results/"`                                            |
| `chunk_size`       | `int`         | `512`         | Maximum tokens per chunk (100-2000)       | `512`, `1024`, `768`                                                        |
| `chunk_overlap`    | `int`         | `50`          | Token overlap between chunks (0-200)      | `50`, `100`, `0`                                                            |
| `embedding_model`  | `str`         | `"tfidf-svd"` | Embedding model to use                    | `"tfidf-svd"`, `"text-embedding-ada-002"`, `"azure-text-embedding-ada-002"` |
| `vector_dimension` | `int`         | `128`         | Dimension of embedding vectors (64-4096)  | `128`, `256`, `1536`                                                        |
| `vector_db_type`   | `str`         | `"chroma"`    | Type of vector database                   | `"chroma"`, `"lancedb"`, `"pinecone"`                                       |
| `vector_db_path`   | `str \| None` | `None`        | Path/connection string for vector DB      | `"./chroma_db"`, `"postgresql://user:pass@localhost/vectordb"`              |
| `include_metadata` | `bool`        | `True`        | Include document metadata with embeddings | `True`, `False`                                                             |
| `max_files`        | `int \| None` | `None`        | Maximum files to process (for testing)    | `10`, `100`, `None`                                                         |

### Output

**Direct Output**: Returns a `VectorIngestionOutput` object containing:

- **Processing Summary**: Total documents, chunks, and embeddings processed
- **Document Metadata**: Detailed information about each processed file
- **Chunk Information**: Text content and metadata for each chunk
- **Vector Database Details**: Database type, path, and collection information
- **Timing Information**: Start/end times and total processing duration
- **Configuration Used**: All parameters that were applied during processing

**File Outputs**:

- `ingestion_metadata.json`: Comprehensive JSON metadata including configuration and results
- `ingestion_summary.txt`: Human-readable summary report with processing statistics

### Enhanced Model Tracking and Metadata

The workflow now provides comprehensive tracking of embedding generation, including actual model usage and fallback behavior through the `EmbeddingResult` object:

- **`requested_model`**: The embedding model that was requested
- **`actual_model`**: The embedding model that was actually used
- **`actual_provider`**: The provider that was actually used (e.g., "openai", "azureopenai", "tfidf")
- **`fallback_occurred`**: Boolean indicating whether fallback to TF-IDF occurred
- **`fallback_reason`**: Detailed reason for fallback if it occurred

### Automatic Fallback Detection

The system automatically detects and reports when fallback occurs:

1. **Azure OpenAI → TF-IDF**: When Azure API key is missing or configuration is invalid
2. **OpenAI → TF-IDF**: When OpenAI API key is missing or rate limits exceeded
3. **Model Configuration Issues**: When embedding model configuration is not found

### Enhanced Metadata Files

The generated metadata files now include actual vs requested model information:

**ingestion_metadata.json**:
```json
{
  "input_directory": "/path/to/input",
  "output_directory": "/path/to/output",
  "requested_embedding_model": "azure-text-embedding-ada-002",
  "actual_embedding_model": "text-embedding-ada-002",
  "actual_embedding_provider": "azureopenai",
  "embedding_fallback_occurred": false,
  "fallback_reason": null,
  "vector_dimension": 128,
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

## Configuration

### API Keys and Environment Setup

#### OpenAI Configuration

Set your OpenAI API key in your `.env` file:

```bash
# For OpenAI
OPENAI_API_KEY=your_openai_api_key_here
```

#### Azure OpenAI Configuration

Set your Azure OpenAI API key and configure the embedding models in your `config.yaml`:

```bash
# For Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
```

Configure Azure OpenAI models in your `config.yaml`:

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

### Supported File Types

- **PDF**: `.pdf` files
- **Word Documents**: `.docx` files
- **Text Files**: `.txt` files
- **Markdown**: `.md` files
- **HTML**: `.html` files
- **CSV**: `.csv` files

### Embedding Models

AWA supports multiple embedding models for different use cases, from local development to production deployments.

#### Local Models

##### TF-IDF + SVD (Default)

- **Model**: `"tfidf-svd"`
- **Dimensions**: Configurable (default: 128, max: 4096)
- **Use Case**: Lightweight, fast processing for development and testing
- **Requirements**: No external API keys needed
- **Performance**: Good for small to medium datasets, basic semantic understanding
- **Features**:
  - Local processing (no internet required)
  - No API costs
  - Fast processing
  - Domain-specific training on your corpus

#### OpenAI Models

##### text-embedding-ada-002

- **Model**: `"text-embedding-ada-002"`
- **Dimensions**: 1536 (fixed)
- **Use Case**: Production-quality embeddings with high accuracy
- **Requirements**: OpenAI API key (`OPENAI_API_KEY`)
- **Performance**: Excellent semantic understanding across domains

##### text-embedding-3-small

- **Model**: `"text-embedding-3-small"`
- **Dimensions**: 1536 (fixed)
- **Use Case**: Latest OpenAI model with improved performance
- **Requirements**: OpenAI API key (`OPENAI_API_KEY`)
- **Performance**: Enhanced accuracy with faster processing

##### text-embedding-3-large

- **Model**: `"text-embedding-3-large"`
- **Dimensions**: 3072 (fixed)
- **Use Case**: Highest quality embeddings for critical applications
- **Requirements**: OpenAI API key (`OPENAI_API_KEY`)
- **Performance**: Best-in-class semantic understanding

#### Azure OpenAI Models

##### azure-text-embedding-ada-002

- **Model**: `"azure-text-embedding-ada-002"`
- **Dimensions**: 1536 (fixed)
- **Use Case**: Enterprise deployments using Azure infrastructure
- **Requirements**: Azure OpenAI API key and resource configuration
- **Performance**: Same quality as OpenAI with Azure compliance and security
- **Features**:
  - Enterprise security and compliance
  - Azure integration
  - Dedicated resources
  - Custom rate limits

### Vector Database Options

#### Chroma (Default)

- **Type**: `"chroma"`
- **Path**: `"./chroma_db"` (local file-based storage)
- **Use Case**: Development, testing, and small to medium deployments
- **Advantages**: Simple setup, no external dependencies

#### LanceDB

- **Type**: `"lancedb"`
- **Path**: `"./lancedb"` (local file-based storage)
- **Use Case**: High-performance local vector storage
- **Advantages**: Fast queries, efficient storage

#### Pinecone

- **Type**: `"pinecone"`
- **Path**: Connection string from Pinecone console
- **Use Case**: Production deployments requiring scalability
- **Advantages**: Managed service, high availability

## Command Line Execution

### Basic Usage with TF-IDF

```bash
# Simple ingestion with default TF-IDF settings (no API key required)
uv run -m awa.main run -w awa-vector-database-ingestion \
  --input '{
    "input_directory": "tests/workflow/test-data/input/",
    "output_directory": "/Users/mahima.chaudhary/Downloads/",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "embedding_model": "tfidf-svd",
    "vector_dimension": 128,
    "vector_db_type": "chroma",
    "vector_db_path": "./chroma_db"
  }'
```

### OpenAI Embeddings Usage

```bash
# OpenAI Ada-002 embeddings (requires OPENAI_API_KEY)
uv run -m awa.main run -w awa-vector-database-ingestion \
  --input '{
    "input_directory": "/path/to/documents/",
    "output_directory": "/path/to/results/",
    "chunk_size": 1000,
    "chunk_overlap": 100,
    "embedding_model": "text-embedding-ada-002",
    "vector_dimension": 1536,
    "vector_db_type": "chroma",
    "vector_db_path": "./openai_chroma_db",
    "include_metadata": true
  }'

# OpenAI 3-Small embeddings (faster processing)
uv run -m awa.main run -w awa-vector-database-ingestion \
  --input '{
    "input_directory": "/path/to/documents/",
    "output_directory": "/path/to/results/",
    "chunk_size": 1000,
    "chunk_overlap": 100,
    "embedding_model": "text-embedding-3-small",
    "vector_dimension": 1536,
    "vector_db_type": "chroma",
    "vector_db_path": "./openai_3_small_db"
  }'

# OpenAI 3-Large embeddings (highest quality)
uv run -m awa.main run -w awa-vector-database-ingestion \
  --input '{
    "input_directory": "/path/to/documents/",
    "output_directory": "/path/to/results/",
    "chunk_size": 1000,
    "chunk_overlap": 100,
    "embedding_model": "text-embedding-3-large",
    "vector_dimension": 3072,
    "vector_db_type": "chroma",
    "vector_db_path": "./openai_3_large_db"
  }'
```

### Azure OpenAI Usage

```bash
# Azure OpenAI embeddings (requires AZURE_OPENAI_API_KEY and config.yaml)
uv run -m awa.main run -w awa-vector-database-ingestion \
  --input '{
    "input_directory": "/path/to/production/documents/",
    "output_directory": "/path/to/ingestion/results/",
    "chunk_size": 1024,
    "chunk_overlap": 100,
    "embedding_model": "azure-text-embedding-ada-002",
    "vector_dimension": 1536,
    "vector_db_type": "chroma",
    "vector_db_path": "./production_chroma_db",
    "include_metadata": true,
    "max_files": 1000
  }'
```

## MCP Server Execution

This workflow can be executed via MCP using the `start_workflow` tool:

```json
{
  "tool": "start_workflow",
  "arguments": {
    "workflow_name": "awa-vector-database-ingestion",
    "input": {
      "input_directory": "input/",
      "output_directory": "output/",
      "embedding_model": "tfidf-svd",
      "vector_db_type": "chroma"
    }
  }
}
```

## Prerequisites

1. **AWA Services Running**: Ensure Temporal server, worker, and API are running
2. **Input Documents**: Place documents to be processed in the input directory
3. **Output Directory**: Ensure the output directory exists or is writable
4. **API Keys** (if using external embedding models):
   - OpenAI API key for OpenAI models
   - Azure OpenAI API key for Azure models
5. **Dependencies**: Vector database libraries (Chroma, LanceDB, etc.)

## Example Workflow

### Input Directory Structure

```
input/
├── sample_document.txt
├── technical_overview.md
├── user_manual.pdf
└── data_report.csv
```

### Expected Output

```
output/
├── ingestion_metadata.json
├── ingestion_summary.txt
└── chroma_db/          # Vector database files
    ├── chroma.sqlite3
    └── embeddings/
```

### Sample Output Summary

```
Vector Database Ingestion Summary
=====================================

Workflow ID: 20250814_094127_491_65a57
Processing Time: 1.21 seconds

Configuration:
- Input Directory: /path/to/input/
- Output Directory: /path/to/output/
- Chunk Size: 512
- Chunk Overlap: 50
- Embedding Model (Requested): tfidf-svd
- Embedding Model (Actual): tfidf-svd
- Embedding Provider: tfidf
- Fallback Occurred: No
- Vector Dimension: 128
- Vector DB Type: chroma

Results:
- Documents Processed: 4
- Total Chunks Created: 12
- Total Embeddings Generated: 12
- Vector Database: chroma
- Collection: documents_20250814_094128

Files Processed:
- sample_document.txt: 1 chunks, 1 embeddings
- technical_overview.md: 2 chunks, 2 embeddings
- user_manual.pdf: 5 chunks, 5 embeddings
- data_report.csv: 4 chunks, 4 embeddings
```

## Error Handling

The workflow includes comprehensive error handling:

- **File Processing Errors**: Individual file failures don't stop the entire process
- **Graceful Degradation**: Continues processing other files if one fails
- **Detailed Error Reporting**: Errors are captured and included in the output
- **Partial Success**: Returns partial results even if some processing fails

## When to Use Each Embedding Approach

### TF-IDF-SVD (Default)

**Best for:**
- ✅ **Development and Testing**: No API keys required for quick prototyping
- ✅ **Offline Processing**: No internet connection needed
- ✅ **Cost-Sensitive Projects**: Completely free to use
- ✅ **Domain-Specific Corpora**: Gets trained on your specific text
- ✅ **Fast Processing**: Immediate processing without API delays

**Limitations:**
- ❌ **Basic Semantic Understanding**: Word frequency based, misses deeper meaning
- ❌ **Poor Cross-Domain**: Works best within similar document types

### OpenAI Embeddings

**Best for:**
- ✅ **Production RAG Applications**: High-quality semantic understanding
- ✅ **Cross-Domain Content**: Works well across different text types and domains
- ✅ **Consistent Results**: Same text always produces identical embeddings
- ✅ **State-of-the-Art Performance**: Leading embedding quality

**Considerations:**
- ❌ **API Costs**: Charges per token processed (~$0.0001 per 1K tokens for ada-002)
- ❌ **Internet Dependency**: Requires stable OpenAI API access
- ❌ **Rate Limits**: API request limitations may affect processing speed
- ❌ **External Dependency**: Reliant on OpenAI service availability

### Azure OpenAI Embeddings

**Best for:**
- ✅ **Enterprise Deployments**: Azure security and compliance features
- ✅ **Regulated Industries**: Meets enterprise security requirements
- ✅ **Azure Ecosystem**: Integrates with other Azure services
- ✅ **Custom Rate Limits**: Dedicated resources with configurable limits
- ✅ **Data Residency**: Control over data location and processing

**Considerations:**
- ❌ **Setup Complexity**: Requires Azure OpenAI resource configuration
- ❌ **API Costs**: Similar pricing to OpenAI with additional Azure overhead
- ❌ **Configuration Required**: More complex setup with config.yaml

### Recommendation Matrix

| Use Case | Recommended Model | Reason |
|----------|-------------------|---------|
| **Prototyping/Development** | `tfidf-svd` | Fast, free, no setup required |
| **Small Production Apps** | `text-embedding-ada-002` | Good balance of quality and cost |
| **High-Quality RAG** | `text-embedding-3-large` | Best semantic understanding |
| **Fast Production Processing** | `text-embedding-3-small` | Good quality with faster API calls |
| **Enterprise/Regulated** | `azure-text-embedding-ada-002` | Compliance and security features |
| **Offline/Air-Gapped** | `tfidf-svd` | Only option without internet access |

## Performance Considerations

- **Chunk Size**: Larger chunks (1024+ tokens) reduce embedding overhead but may lose context
- **Chunk Overlap**: Higher overlap (100+ tokens) improves context preservation but increases storage
- **Batch Processing**: Process files in batches using `max_files` for large document collections
- **Embedding Model Choice**:
  - TF-IDF is fastest for development
  - text-embedding-3-small offers good quality/speed balance
  - text-embedding-3-large provides highest quality
  - Azure models offer enterprise features with similar performance to OpenAI

### Automatic Features

- **Dimension Handling**: OpenAI/Azure embeddings are automatically truncated or padded to match requested dimensions
- **Batch Processing**: External API calls are batched (100 chunks) to avoid rate limits
- **Normalization**: All embeddings are normalized to unit vectors for consistent similarity calculations
- **Graceful Fallback**: Automatic fallback to TF-IDF when external APIs are unavailable

## Troubleshooting

### Common Issues

1. **Empty Output Directory**: Ensure the output directory exists and is writable
2. **Unsupported File Types**: Check that files have supported extensions
3. **API Key Errors**: Verify embedding model API keys are configured correctly
4. **Vector Database Errors**: Ensure vector database paths are accessible and writable

### Debug Mode

Enable debug logging to see detailed processing information:

```bash
export AWA_LOG_LEVEL=DEBUG
uv run -m awa.main run -w awa-vector-database-ingestion --input '...'
```

### Testing

Use the `max_files` parameter to limit processing for testing:

```bash
uv run -m awa.main run -w awa-vector-database-ingestion \
  --input '{
    "input_directory": "test_docs/",
    "output_directory": "test_output/",
    "max_files": 2
  }'
```
