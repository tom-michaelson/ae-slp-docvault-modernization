# Developer Workflow: Local vs Packaged AWA

**Related Documentation:**

- [Package Installation Guide](../installation/package.md) - End-user installation guide

## Overview

AWA development presents a choice between running local development code and using the installed package. Each approach has distinct advantages and considerations that may influence which works better for different scenarios.

## Import Resolution Behavior

Python resolves imports in this order:

1. Current working directory (local code)
2. PYTHONPATH directories
3. site-packages (installed packages)

## Development Scenarios

### Scenario 1: Local Development

```bash
# In the AWA repo directory - uses LOCAL code
$ uv run python -m awa.main start
```

✅ **Result**: Your local changes are reflected immediately.

### Scenario 2: uv-managed CLI in AWA Repo (Development Mode)

```bash
# In the AWA repo directory - uses LOCAL code via uv's editable install
$ uv run awa start
```

✅ **Result**: Your local changes are reflected immediately due to uv's automatic editable install.

### Scenario 3: Installed CLI Outside AWA Repo (Normal Usage)

```bash
# In any other directory - uses installed package
$ uv run awa start
```

✅ **Result**: Works as intended for end users.

## Recommended Development Workflow

### For AWA Core Development:

#### 1. **uv automatically handles editable installs**

When working in a uv-managed project, uv creates an editable install of the current project, so both `awa` and `uv run -m awa.main` use your local development code.

#### 2. **Use either execution method:**

```bash
# Both methods use local development code in uv projects
$ uv run awa start
$ uv run -m awa.main start

# For specific commands
$ uv run awa init
$ uv run -m awa.main init
```

#### 3. **For testing packaged behavior:**

```bash
# Build wheel locally
$ uv build

# Install locally built version in isolated environment
$ uv run pip install dist/slalom_agentic_workflow_accelerator-*.whl --force-reinstall

# Test the installed version
$ uv run awa start
```

## Testing and Quality Assurance

### Running Tests

```bash
# Run all tests
$ make test

# Run specific test files
$ uv run pytest tests/unit/scripts/test_install.py -v

# Run tests with coverage
$ uv run pytest --cov=awa

# Run linting
$ make lint

# Fix (some) linting issues automatically
$ make lint-fix
```

### Pre-commit Checks

Pre-commit hooks are automated scripts that run before a commit is finalized, helping to enforce code quality standards and prevent common mistakes. Integrating pre-commit hooks into the developer workflow ensures that code adheres to predefined guidelines, such as formatting or linting, before it is added to the repository.

```bash
$ make pre-commit # for staged files
$ make pre-commit-all # for all files
```

### Manual Code Generation Commands

AWA includes several code generation scripts that normally run automatically but can be executed manually when needed:

```bash
# Generate TypeScript models from Pydantic API models
$ make generate-typescript-models

# Generate BAML client after modifying BAML files
$ make baml

# Generate CLI documentation
$ uv run scripts/generate_cli_docs.py

# Generate API reference documentation
$ uv run -m scripts.generate_api_reference_docs

# Generate configuration schema and docs
$ uv run python scripts/generate_config_schema.py
$ uv run scripts/generate_config_reference_docs.py
```

**When to use manual generation:**

- TypeScript models: When you modify `awa/core/models/api.py` outside of git commits
- BAML client: After editing any `.baml` files in `awa/core/baml_src/`
- Documentation: When developing docs locally or troubleshooting build issues

## Configuration Management

### Development Configuration

- Use local `.env` files for development-specific settings
- Global config in `~/.config/awa/` is for production use
- Local config files override global settings

### Testing Configuration

```bash
# Create test-specific config
$ cp ~/.config/awa/config.yaml tests/test-config.yaml
$ cp ~/.config/awa/.env tests/test-env

# Use test config for development
$ export AWA_CONFIG_FILE=tests/test-config.yaml
```

## Troubleshooting

### "My changes aren't working!"

**Symptoms**: Code changes don't appear to take effect
**Diagnosis**:

```bash
# Check which version is running
$ awa --version

# In uv projects, both should show the same local version
$ uv run -m awa.main --version
```

**Solution**: In uv projects, both commands use local development code. If changes aren't reflected, check for syntax errors or restart the process.

### Import errors or unexpected behavior

**Symptoms**: ModuleNotFoundError or unexpected imports
**Diagnosis**:

```bash
# Check Python path
$ uv run python -c "import sys; print(sys.path)"

# Check which awa module is being imported
$ uv run python -c "import awa; print(awa.__file__)"
```

**Solution**:

- Use virtual environment: `uv venv`
- Use editable installation: `uv run pip install -e .`
- Check for conflicting installations

### Configuration not found

**Symptoms**: "No global configuration found" error
**Diagnosis**:

```bash
# Check if config directory exists
$ ls -la ~/.awa/

# Check if config files exist
$ ls -la ~/.awa/config.yaml
$ ls -la ~/.awa/.env
```

**Solution**:

- Run `awa init` to create initial configuration
- Check file permissions on config directory
- Verify config file syntax

### Version conflicts

**Symptoms**: Different behavior between local and installed versions
**Diagnosis**:

```bash
# Check installed version
$ uv run pip show slalom-agentic-workflow-accelerator

# Check local version
$ uv run python -c "import awa; print(awa.__version__)"
```

**Solution**:

- Uninstall conflicting versions: `uv run pip uninstall slalom-agentic-workflow-accelerator`
- Use virtual environments for isolation
- Use editable installation for development

## Best Practices

### Code Development

1. **Both execution methods work for development in uv projects**

   ```bash
   # Both use local development code in uv projects
   $ uv run awa start                        # ✅ Uses local code via editable install
   $ uv run -m awa.main start         # ✅ Uses local code directly
   ```

2. **Test both local and packaged behavior**

   ```bash
   # Test local changes
   $ uv run python -m awa.main start

   # Build and test packaged version
   $ uv build
   $ uv run pip install dist/slalom-agentic-workflow-accelerator-*.whl
   $ uv run awa start
   ```

### Testing Strategy

1. **Unit tests for individual functions**

   - Test in isolation with mocked dependencies
   - Fast execution for development feedback

2. **Integration tests for workflows**

   - Test complete installation and configuration flows
   - Verify cross-platform compatibility

3. **End-to-end tests for user scenarios**
   - Test complete user workflows
   - Verify error handling and edge cases

### Configuration Management

1. **Use hierarchical configuration**

   - Global config for defaults
   - Local config for project-specific settings
   - Environment variables for secrets

2. **Validate configuration early**
   - Check required fields during `uv run awa init`
   - Provide helpful error messages
   - Support configuration validation

### Deployment and Distribution

1. **Build and test wheels locally**

   ```bash
   $ uv build
   $ uv run pip install dist/slalom_agentic_workflow_accelerator-*.whl --force-reinstall
   $ uv run awa --help
   ```

2. **Test installation script**

   ```bash
   $ ./scripts/install.py
   $ uv run awa init
   $ uv run awa start
   ```

3. **Verify cross-platform compatibility**
   - Test on Windows, macOS, Linux
   - Verify path handling differences
   - Check platform-specific dependencies

## Common Development Tasks

### Adding New CLI Commands

1. Create command in `awa/core/cli/commands/`
2. Add to CLI router in `awa/core/cli/`
3. Write unit tests
4. Test locally: `uv run python -m awa.main new-command`
5. Test packaged: Build wheel and test `awa new-command`

### Modifying Configuration

1. Update Pydantic models in `awa/core/models/config/`
2. Update CLI commands in `awa/core/cli/commands/init.py`
3. Test configuration creation: `awa init`
4. Test configuration loading in your code
5. Update documentation

### Adding New LLM Providers

1. Add provider enum in `awa/core/models/config/llm_providers_config.py`
2. Update provider setup logic in `awa/core/cli/commands/init.py`
3. Add provider-specific validation
4. Test with `uv run awa init` workflow
5. Update integration tests

## Workflow Exposure Patterns

When developing workflows in AWA, you need to decide whether a workflow should be **exposed** (publicly available) or **internal** (private).

### When to Use `@exposed` Decorator

Use the `@exposed` decorator when a workflow should be:

- Available through the REST API (`/v1/workflows/list`)
- Accessible via MCP server for AI assistants
- Visible in the Web UI workflow dropdown
- Invocable by external systems or users

```python
from temporalio import workflow
from awa.core.decorators.exposed import exposed

@exposed("Generate a personalized poem based on user preferences")
@workflow.defn
class HelloPoemWorkflow:
    """Creates poems using AI."""

    @workflow.run
    async def run(self, name: str, topic: str) -> str:
        # Workflow implementation
        ...
```

**Do NOT use `@exposed` for:**

- Child workflows (called by other workflows)
- Utility workflows (internal orchestration)
- Test workflows (development/testing only)
- SDK helper workflows (internal framework code)

### Child Workflow Pattern (Not Exposed)

Child workflows are meant to be called by parent workflows and should **not** be exposed:

```python
from temporalio import workflow

@workflow.defn
class ProcessDataChunkWorkflow:
    """Internal child workflow for processing data chunks."""

    @workflow.run
    async def run(self, chunk_id: str) -> dict:
        # Child workflow implementation - not exposed
        ...
```

**Why not exposed?**

- Child workflows are implementation details of parent workflows
- They often require specific initialization from parent workflows
- Direct invocation by users would be confusing or error-prone
- They're part of a larger workflow composition

### Utility Workflow Pattern (Not Exposed)

Utility workflows are internal helpers for orchestration and should **not** be exposed:

```python
from temporalio import workflow

@workflow.defn
class BatchProcessingUtilityWorkflow:
    """Internal utility for batch processing with controlled concurrency."""

    @workflow.run
    async def run(self, items: list[str], max_concurrent: int) -> list[str]:
        # Utility workflow implementation - not exposed
        ...
```

**Why not exposed?**

- Utility workflows are low-level building blocks
- They should be composed into higher-level user-facing workflows
- Direct invocation would expose unnecessary complexity to users
- They're meant for internal use by other workflows

### Exposure Behavior

**With `@exposed(description)`:**

- Workflow appears in API `/v1/workflows/list` endpoint
- Shows up in MCP server tool list
- Visible in Web UI dropdown with description
- Can be started via API, MCP, or UI

**Without `@exposed` (internal-only):**

- Workflow is registered with Temporal
- Can be called by other workflows (child workflow pattern)
- Hidden from API, MCP, and UI
- Only accessible programmatically

### Best Practices

1. **User-facing workflows**: Always use `@exposed` with clear, descriptive text
2. **Child workflows**: Never use `@exposed` - keep internal
3. **Utility workflows**: Keep internal unless they provide standalone value
4. **Description quality**: Write clear, actionable descriptions for exposed workflows
5. **Avoid over-exposure**: Only expose workflows that external users should invoke

## Summary

- **Development**: Use `uv run python -m awa.main` (always uses local code)
- **Testing packaged version**: Build and install local wheel in isolated environment
- **Production use**: Use global `awa` command
- **Configuration**: Use hierarchical config with local overrides
- **Quality**: Run tests and linting before commits
- **Workflow exposure**: Use `@exposed` for user-facing workflows, keep child/utility workflows internal

This workflow ensures you're always testing the right code and provides a clear path from development to production deployment.

## Quick Reference

| Task              | Local Development                                                   | Packaged Testing         |
| ----------------- | ------------------------------------------------------------------- | ------------------------ |
| Run AWA           | `uv run python -m awa.main start`                                   | `awa start`              |
| Run tests         | `uv run pytest`                                                     | `pytest` (after install) |
| Run linting       | `make lint`                                                         | `make lint`              |
| Build package     | `uv build`                                                          | N/A                      |
| Install package   | `uv run pip install dist/slalom-agentic-workflow-accelerator-*.whl` | `./scripts/install.py`   |
| Initialize config | `uv run python -m awa.main init`                                    | `awa init`               |
