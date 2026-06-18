# `awa-setup-isolated-agent`

Set up an isolated agent environment and return a fully configured agent config for isolated execution.

This activity encapsulates all isolated environment setup logic and returns an agent config
that is ready to execute without any knowledge of the isolated environment context.

## Parameters

| Name               | Type                 | Description                                                                       |
| :----------------- | :------------------- | :-------------------------------------------------------------------------------- |
| `source_directory` | `str`                | Path to the source directory (Git repo or regular directory)                      |
| `source_branch`    | `str \| None`        | Branch name to checkout (only used for Git repositories in ACT mode)              |
| `agent_config`     | `AgentConfiguration` | Original agent configuration to be adapted for isolated environment execution     |
| `output_directory` | `str`                | Directory name for agent outputs in analyze mode (defaults to "awa-agent-output") |

## Returns

| Type                                                                | Description                                                                                                                                                                      |
| :------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tuple[IsolatedAgentEnvironmentResult, AgentConfiguration \| None]` | Tuple containing IsolatedAgentEnvironmentResult with success status and environment information, and AgentConfiguration configured for isolated execution (None if setup failed) |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.core.activities.agent_modes.models.agent_configuration import AgentConfiguration

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, source_directory: str, source_branch: str | None, agent_config: AgentConfiguration, output_directory: str = "awa-agent-output") -> tuple:
        return await workflow.execute_activity(
            "setup_isolated_agent_activity",
            args=[source_directory, source_branch, agent_config, output_directory],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(minutes=5)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { setup_isolated_agent_activity } = proxyActivities<typeof activities>({
  startToCloseTimeout: "5 minutes",
  taskQueue: "awa_default",
});

export async function myWorkflow(
  sourceDirectory: string,
  sourceBranch: string | null,
  agentConfig: any,
  outputDirectory: string = "awa-agent-output"
): Promise<[any, any]> {
  return await setup_isolated_agent_activity(
    sourceDirectory,
    sourceBranch,
    agentConfig,
    outputDirectory
  );
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<(object, object)> RunAsync(string sourceDirectory, string? sourceBranch, object agentConfig, string outputDirectory = "awa-agent-output")
    {
        return await Workflow.ExecuteActivityAsync<(object, object)>(
            "setup_isolated_agent_activity",
            new object[] { sourceDirectory, sourceBranch, agentConfig, outputDirectory },
            new() {
                TaskQueue = "awa_default",
                StartToCloseTimeout = TimeSpan.FromMinutes(5)
            }
        );
    }
}
```

```java [Java]
import io.temporal.workflow.Workflow;
import io.temporal.activity.ActivityOptions;
import java.time.Duration;

public class MyWorkflowImpl implements MyWorkflow {
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofMinutes(5))
            .build());

    @Override
    public Object[] run(String sourceDirectory, String sourceBranch, Object agentConfig, String outputDirectory) {
        return activities.setupIsolatedAgentActivity(sourceDirectory, sourceBranch, agentConfig, outputDirectory);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, sourceDirectory string, sourceBranch string, agentConfig interface{}, outputDirectory string) ([]interface{}, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Minute * 5,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result []interface{}
	err := workflow.ExecuteActivity(ctx, "setup_isolated_agent_activity", sourceDirectory, sourceBranch, agentConfig, outputDirectory).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $sourceDirectory, ?string $sourceBranch, $agentConfig, string $outputDirectory = 'awa-agent-output'): \Generator
    {
        return yield Workflow::executeActivity(
            'setup_isolated_agent_activity',
            [$sourceDirectory, $sourceBranch, $agentConfig, $outputDirectory],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(300)
        );
    }
}
```

:::
