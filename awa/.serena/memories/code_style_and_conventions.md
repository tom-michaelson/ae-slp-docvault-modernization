# AWA Code Style and Conventions

## Code Formatting & Linting

### Primary Tool: Ruff
- **Configuration**: `ruff.toml`
- **Python Version**: 3.12+
- **Line Length**: 120 characters
- **Cache Directory**: `./.cache/ruff`

### Ruff Configuration Details
```toml
target-version = "py312"
line-length = 120
extend-select = ["ALL"]  # Enable all rules, then ignore specific ones
```

### Ignored Rules (By Design)
- **Docstring Rules**: D100-D104, D107 (Missing docstrings allowed)
- **Boolean Arguments**: FBT001, FBT002 (Boolean function args allowed)
- **Complexity**: C901, PLR0913, PLR0912, PLR0911 (Complex functions allowed)
- **TODO Formatting**: TD002-TD004, FIX002 (Relaxed TODO requirements)
- **Exception Handling**: TRY003, EM101, EM102 (Flexible exception messages)
- **Commented Code**: ERA001 (Commented code allowed)
- **Return Statements**: RET504 (Assignment before return allowed)

### Per-File Ignores
- **Tests**: INP001, S101, PT011, SLF001, PLR2004, PLC0415
- **Scripts**: S603, S607, T201 (Shell execution and print allowed)

## Python Code Standards

### Naming Conventions
- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private Members**: `_single_leading_underscore`
- **Files**: `lowercase_with_underscores.py`

### Type Hints
- **Required**: All function signatures should have type hints
- **Pydantic Models**: Use for data validation and serialization
- **Generic Types**: Use `typing` module for complex types
- **Return Types**: Always specify return types

### Example Function Signature
```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

async def process_workflow_data(
    workflow_id: str,
    input_data: Dict[str, Any],
    timeout: Optional[int] = None
) -> WorkflowResult:
    """Process workflow data with proper typing."""
    pass
```

## File Organization Patterns

### Workflow Files
- **Naming**: `*_workflow.py`
- **Classes**: `*Workflow` (e.g., `DataProcessingWorkflow`)
- **Decorators**: `@workflow.defn` on workflow classes

### Activity Files
- **Naming**: `*_activity.py` or in `activities/` directories
- **Classes**: `*Activity` (e.g., `FileProcessingActivity`)
- **Methods**: Individual activity methods within classes

### BAML Files
- **Extension**: `.baml`
- **Location**: `awa/core/baml_src/`
- **Generation**: Run `make baml` after changes

### Configuration Files
- **Pattern**: `config.*.yaml`
- **Main Config**: `config.yaml`
- **Examples**: `config.example.yaml`

## Code Organization Standards

### Import Order (handled by Ruff)
1. Standard library imports
2. Third-party imports
3. Local application imports

### Example Import Block
```python
# Standard library
import os
import asyncio
from typing import Optional, Dict, Any

# Third-party
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from temporalio import workflow, activity

# Local
from awa.core.models.config import ConfigModel
from awa.core.engine.temporal_client import TemporalClient
```

## Documentation Standards

### Docstring Style
- **Format**: Google-style docstrings preferred
- **Not Required**: Per Ruff configuration, but recommended for public APIs

```python
def process_data(data: Dict[str, Any]) -> ProcessedResult:
    """Process the input data and return results.

    Args:
        data: Input data dictionary to process

    Returns:
        ProcessedResult containing the processed information

    Raises:
        ProcessingError: If data processing fails
    """
    pass
```

## BAML-Specific Conventions

### BAML Function Structure
```baml
function extract_information(input: string) -> Information {
  client GPT4
  prompt #"
    {{ _.role("system") }}
    You are an information extraction expert.

    {{ _.role("user") }}
    Extract information from: {{ input }}

    {{ ctx.output_format }}
  "#
}
```

### BAML Best Practices
- **Always use** `{{ ctx.output_format }}` for type safety
- **Never make arrays optional** - use empty arrays instead
- **Use descriptive enums** instead of numeric confidence scores
- **Structure prompts** with clear role definitions
- **Avoid recursive types** in BAML schemas

## Temporal Patterns

### Workflow Naming
```python
@workflow.defn
class DataProcessingWorkflow:
    """Workflow for processing data with durability."""

    @workflow.run
    async def run(self, input: DataProcessingInput) -> DataProcessingResult:
        """Main workflow execution method."""
        pass
```

### Activity Naming
```python
class FileOperationsActivity:
    """Activities for file system operations."""

    @activity.defn
    async def read_file(self, file_path: str) -> str:
        """Read file content with proper error handling."""
        pass

    @activity.defn
    async def write_file(self, file_path: str, content: str) -> bool:
        """Write file content idempotently."""
        pass
```

## Testing Conventions

### Test File Naming
- **Unit Tests**: `test_*.py` in `tests/unit/`
- **Integration Tests**: `test_*.py` in `tests/api/` or `tests/workflow/`
- **Mirror Structure**: Test file structure mirrors source structure

### Test Method Naming
```python
class TestWorkflowExecution:
    """Test workflow execution patterns."""

    async def test_successful_workflow_execution(self):
        """Test that workflow executes successfully with valid input."""
        pass

    async def test_workflow_handles_invalid_input(self):
        """Test that workflow properly handles invalid input data."""
        pass
```

## Error Handling Patterns

### Exception Classes
```python
class AWAError(Exception):
    """Base exception for AWA-specific errors."""
    pass

class WorkflowExecutionError(AWAError):
    """Raised when workflow execution fails."""
    pass

class ConfigurationError(AWAError):
    """Raised when configuration is invalid."""
    pass
```

### Activity Error Handling
```python
@activity.defn
async def external_api_call(self, endpoint: str) -> APIResult:
    """Call external API with proper error handling and retries."""
    try:
        # Implementation
        pass
    except HTTPException as e:
        # Log error and re-raise with context
        logger.error(f"API call failed: {endpoint}", exc_info=True)
        raise ActivityExecutionError(f"API call to {endpoint} failed") from e
```

## Configuration Management

### Pydantic Settings
```python
from pydantic_settings import BaseSettings

class LLMConfig(BaseSettings):
    """LLM provider configuration."""

    default_model: str = Field(description="Default model to use")
    api_key: Optional[str] = Field(default=None, description="API key")

    class Config:
        env_prefix = "LLM_"
```

## Package Management

### UV Usage
- **Primary Manager**: Always use `uv` instead of `pip`
- **Dependencies**: Defined in `pyproject.toml`
- **Scripts**: Use `[project.scripts]` section for entry points
- **Dev Dependencies**: Use `[dependency-groups]` for development tools

### Dependency Categories
- **Core**: Runtime dependencies in main `dependencies` list
- **Dev**: Development tools in `[dependency-groups].dev`
- **Optional**: Feature-specific dependencies with extras
