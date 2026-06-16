# AWA Task Completion Requirements

## When a development task is completed, ALWAYS run these commands in order:

### 1. Code Quality Checks (REQUIRED)

```bash
make lint              # Check for linting issues with Ruff
make format            # Format code with Ruff
make lint              # Verify formatting was applied correctly
```

**Must Pass**: No linting errors or warnings should remain

### 2. Testing Validation (REQUIRED)

```bash
make test              # Run unit tests
```

**Optional but Recommended**:
```bash
make test-coverage     # Run with coverage report
make test-verbose      # Run with detailed output if issues arise
```

**Must Pass**: All unit tests must pass successfully

### 3. BAML Regeneration (if BAML files modified)

```bash
make baml              # Regenerate BAML client after .baml changes
```

**When Required**: Only if you modified any `.baml` files in `awa/core/baml_src/`

### 4. Pre-commit Validation (REQUIRED)

```bash
make pre-commit        # Run all pre-commit hooks
```

**Alternative for comprehensive check**:
```bash
make pre-commit-all    # Run on all files (not just staged)
```

**Must Pass**: All pre-commit hooks must pass without errors

### 5. Integration Testing (for major changes)

**API Changes**:
```bash
make test-api          # Test API endpoints
```

**Workflow Changes**:
```bash
make run-test-workflow # Run workflow integration tests (auto service management)
```

**UI Changes**:
```bash
make test-ui           # Run Playwright UI tests
```

### 6. Service Verification (for infrastructure changes)

```bash
make clean-start       # Clean build and start all services
```

**Verify**: All services start without errors and health checks pass

## Error Resolution Priority

### If `make lint` fails:
1. Try `make lint-fix` to auto-fix issues
2. Manually resolve remaining lint errors
3. Re-run `make lint` to verify

### If `make test` fails:
1. Read test output carefully
2. Fix failing tests or underlying code
3. Re-run `make test` to verify
4. Use `make test-verbose` for more details if needed

### If `make pre-commit` fails:
1. Address each failing hook individually
2. Common fixes:
   - Run `make format` for code formatting
   - Fix trailing whitespace or line endings
   - Resolve import sorting issues
3. Re-run `make pre-commit` to verify

### If services fail to start:
1. Check logs with `make docker-logs` if using Docker
2. Verify configuration files (`config.yaml`)
3. Check required environment variables
4. Try `make clean` then `make clean-start`

## Special Cases

### After Dependency Changes
```bash
uv sync                # Sync dependencies if pyproject.toml changed
make install           # Alternative: full reinstall
```

### After Configuration Changes
```bash
make stop              # Stop all services
make start             # Restart with new configuration
```

### After BAML Schema Changes
```bash
make baml              # REQUIRED: Regenerate client
make test              # Verify integration works
```

### Before Creating Pull Requests
```bash
make pre-commit-all    # Run hooks on all files
make test-coverage     # Verify test coverage
make test-api          # Test API integration (if API changed)
make run-test-workflow # Test workflows (if workflows changed)
```

## Critical Success Criteria

**NEVER commit or submit work unless ALL of these pass**:

1. ✅ `make lint` - No linting errors
2. ✅ `make test` - All unit tests pass
3. ✅ `make pre-commit` - All hooks pass
4. ✅ Services start successfully (if infrastructure changed)
5. ✅ Integration tests pass (if applicable)

## Package Manager Rules

**ALWAYS use UV instead of pip/python directly**:
- ✅ `uv run -m pytest` instead of `python -m pytest`
- ✅ `uv sync` instead of `pip install`
- ✅ `make` commands (which use uv internally)

## Quick Validation Workflow

For typical development tasks, this sequence should always work:

```bash
# Quick validation sequence
make format            # Format code
make lint              # Check linting
make test              # Run tests
make pre-commit        # Final validation

# If all pass, your task is ready for commit/PR
```

## Time Estimates

- **Code Quality + Tests**: ~30-60 seconds
- **BAML Regeneration**: ~10-20 seconds
- **Pre-commit Hooks**: ~20-40 seconds
- **Integration Tests**: ~2-5 minutes
- **Service Restart**: ~1-2 minutes

**Total Time**: Usually under 2 minutes for typical tasks, up to 5-10 minutes for major changes requiring integration testing.
