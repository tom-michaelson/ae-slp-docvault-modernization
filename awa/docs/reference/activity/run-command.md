# `awa-run-command`

Executes a shell command in a specified working directory and returns the result.

This activity provides a way to run shell commands asynchronously within workflows,
capturing both the output and exit status. It uses the AWA CommandUtils for safe
command execution with proper error handling.

## Parameters

| Name           | Type                | Description                                                        |
| -------------- | ------------------- | ------------------------------------------------------------------ |
| `command_input` | `CommandInput`      | Object containing the command to execute and optional working directory. |

### CommandInput

| Name          | Type          | Description                                                    |
| ------------- | ------------- | -------------------------------------------------------------- |
| `command`     | `str`         | The shell command to execute.                                  |
| `working_dir` | `str \| None` | Optional working directory to execute the command in.         |

## Returns

| Type            | Description                                           |
| :-------------- | :---------------------------------------------------- |
| `CommandResult` | Object containing the command execution results.      |

### CommandResult

| Name        | Type   | Description                                           |
| ----------- | ------ | ----------------------------------------------------- |
| `exit_code` | `int`  | The exit code returned by the command (0 = success). |
| `output`    | `str`  | The combined stdout and stderr output from the command. |
| `success`   | `bool` | Whether the command executed successfully (exit_code == 0). |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.core.models.command_result import CommandInput

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, command: str, working_dir: str | None = None) -> str:
        command_input = CommandInput(command=command, working_dir=working_dir)
        result = await workflow.execute_activity(
            "awa-run-command",
            command_input,
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=300)
        )
        return result.output if result.success else f"Command failed: {result.output}"
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

interface CommandInput {
  command: string;
  working_dir?: string;
}

interface CommandResult {
  exit_code: number;
  output: string;
  success: boolean;
}

const { "awa-run-command": runCommand } = proxyActivities<typeof activities>({
  startToCloseTimeout: "5 minutes",
  taskQueue: "awa_default",
});

export async function myWorkflow(
  command: string,
  workingDir?: string
): Promise<string> {
  const commandInput: CommandInput = { command, working_dir: workingDir };
  const result: CommandResult = await runCommand(commandInput);
  return result.success ? result.output : `Command failed: ${result.output}`;
}
```

```csharp [C#]
using Temporalio.Workflows;

public class CommandInput
{
    public string Command { get; set; } = "";
    public string? WorkingDir { get; set; }
}

public class CommandResult
{
    public int ExitCode { get; set; }
    public string Output { get; set; } = "";
    public bool Success { get; set; }
}

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<string> RunAsync(string command, string? workingDir = null)
    {
        var commandInput = new CommandInput { Command = command, WorkingDir = workingDir };
        var result = await Workflow.ExecuteActivityAsync<CommandResult>(
            "awa-run-command",
            new object[] { commandInput },
            new() {
                TaskQueue = "awa_default",
                StartToCloseTimeout = TimeSpan.FromMinutes(5)
            }
        );
        return result.Success ? result.Output : $"Command failed: {result.Output}";
    }
}
```

```java [Java]
import io.temporal.workflow.Workflow;
import io.temporal.activity.ActivityOptions;
import java.time.Duration;

public class CommandInput {
    private String command;
    private String workingDir;

    // getters and setters
}

public class CommandResult {
    private int exitCode;
    private String output;
    private boolean success;

    // getters and setters
}

public class MyWorkflowImpl implements MyWorkflow {
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofMinutes(5))
            .build());

    @Override
    public String run(String command, String workingDir) {
        CommandInput commandInput = new CommandInput();
        commandInput.setCommand(command);
        commandInput.setWorkingDir(workingDir);

        CommandResult result = activities.runCommand(commandInput);
        return result.isSuccess() ? result.getOutput() : "Command failed: " + result.getOutput();
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

type CommandInput struct {
	Command    string  `json:"command"`
	WorkingDir *string `json:"working_dir,omitempty"`
}

type CommandResult struct {
	ExitCode int    `json:"exit_code"`
	Output   string `json:"output"`
	Success  bool   `json:"success"`
}

func MyWorkflow(ctx workflow.Context, command string, workingDir *string) (string, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Minute * 5,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	commandInput := CommandInput{
		Command:    command,
		WorkingDir: workingDir,
	}

	var result CommandResult
	err := workflow.ExecuteActivity(ctx, "awa-run-command", commandInput).Get(ctx, &result)
	if err != nil {
		return "", err
	}

	if result.Success {
		return result.Output, nil
	}
	return "Command failed: " + result.Output, nil
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class CommandInput
{
    public function __construct(
        public string $command,
        public ?string $working_dir = null
    ) {}
}

class CommandResult
{
    public function __construct(
        public int $exit_code,
        public string $output,
        public bool $success
    ) {}
}

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $command, ?string $workingDir = null): \Generator
    {
        $commandInput = new CommandInput($command, $workingDir);

        $result = yield Workflow::executeActivity(
            'awa-run-command',
            [$commandInput],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(300)
        );

        return $result->success ? $result->output : "Command failed: " . $result->output;
    }
}
```

:::

## Examples

### Basic Command Execution

```python
# Execute a simple command
command_input = CommandInput(command="ls -la")
result = await workflow.execute_activity(
    "awa-run-command",
    command_input,
    task_queue="awa_default",
    start_to_close_timeout=timedelta(seconds=30)
)
print(f"Exit code: {result.exit_code}")
print(f"Output: {result.output}")
```

### Command with Working Directory

```python
# Execute command in specific directory
command_input = CommandInput(
    command="npm install",
    working_dir="/path/to/project"
)
result = await workflow.execute_activity(
    "awa-run-command",
    command_input,
    task_queue="awa_default",
    start_to_close_timeout=timedelta(minutes=10)
)

if result.success:
    print("npm install completed successfully")
else:
    print(f"npm install failed with exit code {result.exit_code}")
    print(f"Error output: {result.output}")
```

## Notes

- The activity combines both stdout and stderr into the output field
- Commands are executed asynchronously using AWA's CommandUtils
- The success field is automatically set based on whether exit_code equals 0
- Consider appropriate timeout values based on expected command execution time
- Working directory is optional; if not provided, the command runs in the current directory
