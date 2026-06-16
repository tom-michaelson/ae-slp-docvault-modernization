# `awa-chunk-document`

Chunks a document into smaller pieces using various chunking strategies.

This function uses the Chonkie library to split text into manageable chunks suitable for LLM processing.

## Chunking Strategies

| Strategy    | Description                                                      | Use Case                               |
| ----------- | ---------------------------------------------------------------- | -------------------------------------- |
| `token`     | Fixed-size chunks based on token count                          | Simple, consistent chunking            |
| `sentence`  | Splits at sentence boundaries                                    | Maintaining grammatical coherence      |
| `recursive` | Hierarchical splitting using multiple separators (default)       | Preserving semantic meaning            |

## Parameters

| Name             | Type            | Description                                                    |
| ---------------- | --------------- | -------------------------------------------------------------- |
| `content`        | `str`           | The text content to be chunked                                 |
| `chunker_type`   | `str`           | Type of chunker: "token", "sentence", or "recursive" (default)|
| `max_chunk_size` | `int \| None`   | Maximum size of each chunk in tokens (optional)               |
| `chunk_overlap`  | `int \| None`   | Number of tokens to overlap between chunks (optional)         |

## Returns

| Type                   | Description                                                                          |
| :--------------------- | :----------------------------------------------------------------------------------- |
| `ChunkDocumentOutput`  | Object containing list of chunks with metadata and chunking statistics               |

### ChunkDocumentOutput Structure

```python
{
    "chunks": [
        {
            "text": str,          # The chunk text content
            "token_count": int,   # Number of tokens in chunk
            "start_index": int,   # Starting character position
            "end_index": int      # Ending character position
        }
    ],
    "total_chunks": int,          # Total number of chunks created
    "chunker_used": str           # The chunker type that was used
}
```

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, content: str) -> dict:
        return await workflow.execute_activity(
            "awa-chunk-document",
            args=[{
                "content": content,
                "chunker_type": "recursive",
                "max_chunk_size": 512,
                "chunk_overlap": 50
            }],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=30)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
// Assuming activities are in an "activities.ts" file
import type * as activities from "./activities";

const { chunk_document } = proxyActivities<typeof activities>({
  startToCloseTimeout: "30 seconds",
  taskQueue: "awa_default",
});

export async function myWorkflow(content: string): Promise<ChunkDocumentOutput> {
  return await chunk_document({
    content: content,
    chunker_type: "recursive",
    max_chunk_size: 512,
    chunk_overlap: 50
  });
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<ChunkDocumentOutput> RunAsync(string content)
    {
        var input = new Dictionary<string, object>
        {
            ["content"] = content,
            ["chunker_type"] = "recursive",
            ["max_chunk_size"] = 512,
            ["chunk_overlap"] = 50
        };

        return await Workflow.ExecuteActivityAsync<ChunkDocumentOutput>(
            "awa-chunk-document",
            new object?[] { input },
            new() {
                TaskQueue = "awa_default",
                StartToCloseTimeout = TimeSpan.FromSeconds(30)
            }
        );
    }
}
```

```java [Java]
import io.temporal.workflow.Workflow;
import io.temporal.activity.ActivityOptions;
import java.time.Duration;
import java.util.Map;

public class MyWorkflowImpl implements MyWorkflow {
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(30))
            .build());

    @Override
    public ChunkDocumentOutput run(String content) {
        Map<String, Object> input = Map.of(
            "content", content,
            "chunker_type", "recursive",
            "max_chunk_size", 512,
            "chunk_overlap", 50
        );
        return activities.chunkDocument(input);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, content string) (ChunkDocumentOutput, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 30,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	input := map[string]interface{}{
		"content":        content,
		"chunker_type":   "recursive",
		"max_chunk_size": 512,
		"chunk_overlap":  50,
	}

	var result ChunkDocumentOutput
	err := workflow.ExecuteActivity(ctx, "awa-chunk-document", input).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $content): \Generator
    {
        $input = [
            'content' => $content,
            'chunker_type' => 'recursive',
            'max_chunk_size' => 512,
            'chunk_overlap' => 50
        ];

        $result = yield Workflow::executeActivity(
            'awa-chunk-document',
            [$input],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(30)
        );
        return $result;
    }
}
```

:::
