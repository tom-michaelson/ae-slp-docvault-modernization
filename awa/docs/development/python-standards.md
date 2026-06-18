# Python Development Standards

Essential Python coding standards for all AWA development.

## Code Style

- **Style Guides**: Follow PEP 8 for code style and PEP 257 for docstrings.
- **Type Hints**: All functions and methods must include type hints.

## Configuration

- **Source**: Use `config.yaml` for general settings and `.env` files for secrets.
- **Access**: Load configuration using AWA's models (`AppConfig`, `LLMConfig`) via `awa.core.utils.config_loader`.
- **Security**: Never commit secrets or API keys to version control.

## Error Handling

- **Exceptions**: Catch specific exceptions, not bare `except:` clauses.
- **Logging**: Use `awa.core.logger` for structured logging. Never log sensitive data.
- **Control Flow**: Avoid using exceptions for normal control flow; check conditions proactively.

## AWA-Specific Patterns

- **Utilities**: Use AWA's utility modules for common tasks:
  - `awa.core.utils.file_system_utils` for file I/O.
  - `awa.core.utils.command_utils` for running shell commands.
- **Path Handling**: Use `pathlib.Path` for all filesystem path operations.
- **Data Validation**: Use Pydantic models to validate all external data.

```python
# Good: Using AWA utilities for safe file operations
from pathlib import Path
from awa.core.utils.file_system_utils import read_file_safe

async def get_file_content(path: Path) -> str | None:
    # Safely reads a file, returning None if it doesn't exist
    return await read_file_safe(path)

# Bad: Using built-in open without error handling
# This can crash if the file doesn't exist or permissions are wrong.
def get_file_content_unsafe(path: str) -> str:
    with open(path, "r") as f:
        return f.read()
```

## Logging

For comprehensive logging guidance, see the [Logging Documentation](../usage/features/logging.md).

**Key Requirements:**
- Always call `init_logging()` once at application startup
- Use `get_logger(LoggerComponent.X)` for component-specific loggers
- Never use raw loguru or Python logging directly
- Never log sensitive data

## Common Anti-Patterns to Avoid

- **Mutable Defaults**: Don't use mutable default arguments like `[]` or `{}` in function definitions.
- **Resource Leaks**: Always close file handles and network connections, preferably with a context manager (`with` or `async with`).
- **Blocking I/O in Async Code**: Use `async` libraries for I/O in `async` functions.
