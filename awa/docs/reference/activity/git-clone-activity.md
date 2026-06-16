# `git_clone_repository_activity`

Clone a Git repository to a destination path with optional branch selection.

This activity clones a Git repository from a URL to a specified destination path. If no destination is provided, it creates a temporary directory. It supports checking out specific branches and handles repository access errors gracefully with proper cleanup.

## Parameters

| Name | Type | Description |
| :--- | :--- | :---------- |
| `git_url` | `str` | The Git repository URL to clone |
| `destination_path` | `str \| Path \| None` | Optional destination path. If not provided, uses a temporary directory |
| `branch` | `str \| None` | Optional branch to checkout after cloning |

## Returns

| Type | Description |
| :--- | :---------- |
| `str` | The path to the cloned repository |

## Raises

| Exception | Description |
| :-------- | :---------- |
| `GitOperationError` | Raised when Git operations fail or repository is inaccessible |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.sdk import constants

@workflow.defn
class CloneRepoWorkflow:
    @workflow.run
    async def run(self, git_url: str, destination: str = None, branch: str = None) -> str:
        repo_path = await workflow.execute_activity(
            constants.ACTIVITY_GIT_CLONE,
            args=[git_url, destination, branch],
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=constants.GIT_TIMEOUT_SECONDS)
        )
        return repo_path
```

```python [SDK Helper]
from awa.sdk.utils.activity.git_clone_activity import git_clone_activity

@workflow.defn
class CloneRepoWorkflow:
    @workflow.run
    async def run(self, git_url: str, destination: str = None, branch: str = None) -> str:
        repo_path = await git_clone_activity(
            git_url=git_url,
            destination_path=destination,
            branch=branch
        )
        return repo_path
```

:::

## Examples

### Basic Repository Clone

```python
# Clone to temporary directory
repo_path = await git_clone_activity("https://github.com/example/repo.git")
```

### Clone to Specific Path

```python
# Clone to specific directory
repo_path = await git_clone_activity(
    git_url="https://github.com/example/repo.git",
    destination_path="/path/to/destination"
)
```

### Clone Specific Branch

```python
# Clone specific branch
repo_path = await git_clone_activity(
    git_url="https://github.com/example/repo.git",
    destination_path="/path/to/destination",
    branch="feature-branch"
)
```

## Implementation Details

- **Automatic Cleanup**: If cloning fails and a temporary directory was created, it's automatically cleaned up
- **Directory Handling**: If the destination directory exists and is not empty, a subdirectory is created using the repository name
- **Subprocess Execution**: Uses `subprocess.run` with proper error handling and output capture
- **Logging**: Comprehensive activity logging for debugging and monitoring

## Error Handling

The activity handles various error scenarios:

- **Network Issues**: Repository URL is unreachable
- **Authentication**: Repository requires authentication not provided
- **File System**: Destination path permissions or disk space issues
- **Git Errors**: Invalid repository format or corrupted data

All errors are wrapped in `GitOperationError` with descriptive messages from Git's stderr output.
