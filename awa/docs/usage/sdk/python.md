# Python SDK Usage

This guide explains how to consume the AWA Python SDK (`awa-client`) published to AWS CodeArtifact.

## Installation

<!--@include: /../../.shared/sdk-client-usage.md -->

:::danger Prerequisites
Be sure you have fulfilled the [prerequisites](./index.md#prerequisites) before attempting to use this SDK.
:::

### Option 1: uv

#### Step 1: Configure UV to Use AWS CodeArtifact

Add the AWS CodeArtifact repository as an index in your `pyproject.toml` file:

```toml
[[tool.uv.index]]
name = "slalom"
url = "https://slalom-all-825505919920.d.codeartifact.us-east-1.amazonaws.com/pypi/slalom-pypi/simple/"
explicit = true
```

#### Step 2: Install the Package

Make the following changes to your `pyproject.toml` file:

::: code-group

```toml[pyproject.toml]
[project]
# ...
dependencies = [
    # ...
    "awa-client==1.0.11", # Replace with desired version, but we recommend locking to a specific version
]

[tool.uv.sources]
awa-client = { index = "slalom" }
```

:::

#### Step 3: Authenticate to AWS CodeArtifact and `uv sync`

We have a sample script that authenticates and sets the required environment variables for UV. Run the commands below to use this script.

:::warning AWS Profile
The example scripts below assume you have configured a profile named `slalom-codeartifact`. If you have configured a different profile, you will need to update the `--profile` flag to the name of your profile. See [prerequisites](./index.md#prerequisites) for more details on how to configure your AWS profile.

You can also set the `CODEARTIFACT_AWS_PROFILE` environment variable to the name of your profile.
:::

::: code-group

```bash [Mac/Linux (Bash)]
# Directly export environment variables
eval $(bash scripts/aws-codeartifact-auth.sh --profile slalom-codeartifact --export)

# Then run your uv commands
uv sync
```

```powershell [Windows (PowerShell)]
# Directly set environment variables
. .\scripts\aws-codeartifact-auth.ps1 -Profile slalom-codeartifact -Export | Invoke-Expression

# Then run your uv commands
uv sync
```

:::

See [uv's official documentation](https://docs.astral.sh/uv/guides/integration/alternative-indexes/#aws-codeartifact) for more details on this authentication process.

### Option 2: pip

#### Step 1: Configure pip to Use AWS CodeArtifact

Use the AWS CLI to automatically configure pip:

```bash
aws codeartifact login \
  --tool pip \
  --domain slalom-all \
  --domain-owner 825505919920 \
  --repository slalom-pypi \
  --profile <your-profile>
```

This command:

- Fetches a 12-hour authentication token
- Configures pip to use CodeArtifact as the package index
- Handles token refresh automatically

#### Step 2: Install the Package

```bash
# Install the latest version
pip install awa-client

# Install a specific version
pip install awa-client==1.0.11
```

## Using the Python SDK

The AWA Python SDK provides namespace-based modules for organizing different types of utilities:

### Namespace Modules

The SDK is organized into clean namespace modules that group related functionality:

```python
from awa.client import awa_activity, awa_workflow, awa_general, awa_constants

# Access workflow utilities through the awa_workflow namespace
await awa_workflow.execute_agent(agent_config)
await awa_workflow.build_prompt(prompt_params)
await awa_workflow.chunk_document(document_input)
await awa_workflow.read_file_and_parse(parse_input)

# Access activity utilities through the awa_activity namespace
await awa_activity.read_file(file_path)
await awa_activity.write_file(file_path, content)
await awa_activity.run_command(command_input)
await awa_activity.invoke_mcp_tool(tool_params)
await awa_activity.git_clone(repo_url, destination)

# Access general utilities through the awa_general namespace
workflow_paths = awa_general.get_workflow_paths()
workflow_paths_direct = awa_general.get_workflow_paths_direct(workflow_dir, workflow_type, workflow_id)

# Access constants through the awa_constants namespace
print(f"Default task queue: {awa_constants.AWA_DEFAULT_TASK_QUEUE}")
print(f"Agent timeout: {awa_constants.AGENT_TIMEOUT_SECONDS}")
```

### Model Imports for Type Annotations

For type annotations and model instantiation, import models directly from the models module:

```python
# Import model types for type annotations and instantiation
from awa.client.models import (
    AgentConfiguration,
    AgentModeEnum,
    AgentProviderEnum,
    WorkflowPaths,
    CommandResult,
    CommandInput,
    BuildPromptParams,
    ChunkDocumentInput,
    ReadFileAndParseInput
)

# Use imported models for type annotations
def create_agent_config(mode: str, provider: str) -> AgentConfiguration:
    return AgentConfiguration(
        mode=AgentModeEnum.ACT,
        provider=AgentProviderEnum.CLAUDE
    )

# Use in function signatures
async def process_file(paths: WorkflowPaths, params: BuildPromptParams) -> CommandResult:
    # Implementation here
    pass

# Combine namespace modules with model imports
from awa.client import awa_workflow

async def example_workflow():
    # Create models using direct imports (better for type checking)
    config = AgentConfiguration(
        mode=AgentModeEnum.ACT,
        provider=AgentProviderEnum.CLAUDE
    )

    # Execute operations using namespace modules
    result = await awa_workflow.execute_agent(config)
    return result
```

## Best Practices

1. **Import Organization**:

   - **For Utilities**: Import namespace modules: `from awa.client import awa_activity, awa_workflow, awa_general, awa_constants`
   - **For Type Annotations**: Import models directly: `from awa.client.models import AgentConfiguration, WorkflowPaths`
   - **Why**: Namespace modules provide clean organization while direct model imports work better with static type checkers

2. **Recommended Usage Pattern**:

   ```python
   # At the top of your file - import namespaces and types
   from awa.client import awa_activity, awa_workflow, awa_general, awa_constants
   from awa.client.models import AgentConfiguration, CommandResult, WorkflowPaths

   # Use models for type annotations and instantiation
   def create_config() -> AgentConfiguration:
       return AgentConfiguration(...)

   # Use namespace modules for runtime operations
   async def run_workflow(config: AgentConfiguration) -> CommandResult:
       return await awa_workflow.execute_agent(config)
   ```

3. **Leverage IDE Autocomplete**:

   - **Namespace Modules**:
     - Type `awa_workflow.` to explore workflow utilities
     - Type `awa_activity.` to explore activity utilities
     - Type `awa_general.` to explore general utilities
     - Type `awa_constants.` to explore constants
   - **Model Imports**: Type `from awa.client.models import ` to see all available models

4. **Organized Access Pattern**:

   - **Utilities** (namespace modules):
     - Workflows: `awa_workflow.*`
     - Activities: `awa_activity.*`
     - General: `awa_general.*`
     - Constants: `awa_constants.*`
   - **Type Annotations** (direct imports):
     - Models: `from awa.client.models import ModelName`
