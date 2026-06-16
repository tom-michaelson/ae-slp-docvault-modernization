# `awa-chunk-document`

A workflow that chunks documents into smaller pieces using various chunking strategies.

This workflow takes document content and chunking parameters as input and returns the chunked output by calling the chunk_document activity. It serves as a wrapper that allows for future enhancement such as caching, batch processing, or multi-step chunking strategies.

## Parameters

| Name             | Type                 | Description                                                        |
| :--------------- | :------------------- | :----------------------------------------------------------------- |
| `workflow_input` | `ChunkDocumentInput` | An object containing the document content and chunking parameters. |

### ChunkDocumentInput

| Name             | Type             | Description                                      |
| :--------------- | :--------------- | :----------------------------------------------- |
| `content`        | `str`            | The text content to be chunked.                  |
| `chunker_type`   | `ChunkerType`    | The type of chunker to use (default: RECURSIVE). |
| `max_chunk_size` | `int` (optional) | Maximum size of each chunk in tokens.            |
| `chunk_overlap`  | `int` (optional) | Number of tokens to overlap between chunks.      |

### ChunkerType

The available chunker types (enum values):

- `TOKEN`: Fixed-size token chunks
- `SENTENCE`: Splits by sentences
- `RECURSIVE`: Hierarchical, semantically meaningful chunks (default)

## Returns

| Type                  | Description                                   |
| :-------------------- | :-------------------------------------------- |
| `ChunkDocumentOutput` | An object containing the chunks and metadata. |

### ChunkDocumentOutput

| Name           | Type                | Description                         |
| :------------- | :------------------ | :---------------------------------- |
| `chunks`       | `List[ChunkResult]` | List of chunks with their metadata. |
| `total_chunks` | `int`               | Total number of chunks created.     |
| `chunker_used` | `str`               | The chunker type that was used.     |

### ChunkResult

| Name          | Type  | Description                                |
| :------------ | :---- | :----------------------------------------- |
| `text`        | `str` | The text content of the chunk.             |
| `token_count` | `int` | Number of tokens in the chunk.             |
| `start_index` | `int` | Starting character index in original text. |
| `end_index`   | `int` | Ending character index in original text.   |

## Usage

The following examples show how to start the `awa-chunk-document` workflow as a child workflow.

::: code-group

```python [Python]
from awa.sdk.models.chunking_models import ChunkDocumentInput, ChunkerType

# Create parameters
workflow_input = ChunkDocumentInput(
    content="Your long document text here...",
    chunker_type=ChunkerType.RECURSIVE,
    max_chunk_size=512,
    chunk_overlap=50
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "awa-chunk-document",
    workflow_input
)

# Access the chunks
for chunk in result.chunks:
    print(f"Chunk: {chunk.text[:50]}...")
    print(f"Tokens: {chunk.token_count}")
```

```typescript [TypeScript]
// Define the parameters interface
interface ChunkDocumentInput {
  content: string;
  chunkerType?: "token" | "sentence" | "recursive";
  maxChunkSize?: number;
  chunkOverlap?: number;
}

// Create parameters
const workflowInput: ChunkDocumentInput = {
  content: "Your long document text here...",
  chunkerType: "recursive",
  maxChunkSize: 512,
  chunkOverlap: 50,
};

// Execute the child workflow and wait for completion
const result = await executeChild("awa-chunk-document", {
  args: [workflowInput],
});

// Access the chunks
result.chunks.forEach((chunk) => {
  console.log(`Chunk: ${chunk.text.substring(0, 50)}...`);
  console.log(`Tokens: ${chunk.tokenCount}`);
});
```

```csharp [.NET]
// Define the parameters class
public class ChunkDocumentInput
{
    public string Content { get; set; }
    public string ChunkerType { get; set; } = "recursive";
    public int? MaxChunkSize { get; set; }
    public int? ChunkOverlap { get; set; }
}

// Create parameters
var workflowInput = new ChunkDocumentInput
{
    Content = "Your long document text here...",
    ChunkerType = "recursive",
    MaxChunkSize = 512,
    ChunkOverlap = 50
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync("awa-chunk-document", workflowInput);

// Access the chunks
foreach (var chunk in result.Chunks)
{
    Console.WriteLine($"Chunk: {chunk.Text.Substring(0, Math.Min(50, chunk.Text.Length))}...");
    Console.WriteLine($"Tokens: {chunk.TokenCount}");
}
```

```java [Java]
// Define the parameters class
public class ChunkDocumentInput {
    public String content;
    public String chunkerType = "recursive";
    public Integer maxChunkSize;
    public Integer chunkOverlap;
}

// Create parameters
ChunkDocumentInput workflowInput = new ChunkDocumentInput();
workflowInput.content = "Your long document text here...";
workflowInput.chunkerType = "recursive";
workflowInput.maxChunkSize = 512;
workflowInput.chunkOverlap = 50;

// Execute the child workflow and wait for completion
ChunkDocumentOutput result = Workflow.executeChildWorkflow(
    "awa-chunk-document",
    workflowInput,
    ChunkDocumentOutput.class
);

// Access the chunks
for (ChunkResult chunk : result.chunks) {
    System.out.println("Chunk: " + chunk.text.substring(0, Math.min(50, chunk.text.length())) + "...");
    System.out.println("Tokens: " + chunk.tokenCount);
}
```

```go [Go]
// Define the parameters struct
type ChunkDocumentInput struct {
    Content      string  `json:"content"`
    ChunkerType  string  `json:"chunker_type,omitempty"`
    MaxChunkSize *int    `json:"max_chunk_size,omitempty"`
    ChunkOverlap *int    `json:"chunk_overlap,omitempty"`
}

// Create parameters
maxChunkSize := 512
chunkOverlap := 50
workflowInput := ChunkDocumentInput{
    Content:      "Your long document text here...",
    ChunkerType:  "recursive",
    MaxChunkSize: &maxChunkSize,
    ChunkOverlap: &chunkOverlap,
}

// Execute the child workflow and wait for completion
var result ChunkDocumentOutput
err := workflow.ExecuteChildWorkflow(ctx, "awa-chunk-document", workflowInput).Get(ctx, &result)
if err != nil {
    return err
}

// Access the chunks
for _, chunk := range result.Chunks {
    fmt.Printf("Chunk: %.50s...\n", chunk.Text)
    fmt.Printf("Tokens: %d\n", chunk.TokenCount)
}
```

```php [PHP]
// Define the parameters class
class ChunkDocumentInput {
    public string $content;
    public string $chunkerType = 'recursive';
    public ?int $maxChunkSize = null;
    public ?int $chunkOverlap = null;
}

// Create parameters
$workflowInput = new ChunkDocumentInput();
$workflowInput->content = "Your long document text here...";
$workflowInput->chunkerType = 'recursive';
$workflowInput->maxChunkSize = 512;
$workflowInput->chunkOverlap = 50;

// Execute the child workflow and wait for completion
$result = yield Workflow::executeChildWorkflow(
    'awa-chunk-document',
    [$workflowInput]
);

// Access the chunks
foreach ($result->chunks as $chunk) {
    echo "Chunk: " . substr($chunk->text, 0, 50) . "...\n";
    echo "Tokens: " . $chunk->tokenCount . "\n";
}
```

:::

## SDK Utility

The AWA SDK provides a utility method for easier access to this workflow:

```python
from awa.sdk.utils.workflow_utils import WorkflowUtils
from awa.sdk.models.chunking_models import ChunkerType

# Using the utility method
result = await WorkflowUtils.chunk_document(
    content="Your document text here...",
    chunker_type=ChunkerType.RECURSIVE,
    max_chunk_size=512,
    chunk_overlap=50
)
```

## Notes

- The workflow uses the Chonkie library (base package) which provides three chunking strategies without requiring torch dependencies
- For cross-platform compatibility, advanced chunkers (SEMANTIC, CODE, NEURAL, etc.) are not available
- The default chunker (RECURSIVE) works well for most general text documents
- Consider using TOKEN chunker when you need precise control over chunk sizes
- Use SENTENCE chunker when preserving sentence boundaries is important
