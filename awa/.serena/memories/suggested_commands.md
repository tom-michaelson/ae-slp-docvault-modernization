# AWA Development Commands

## Primary Package Manager
**IMPORTANT**: Use `uv` as the primary Python package manager. Avoid direct `python`, `pip`, or `pytest` calls.

## Essential Development Commands

### Setup & Installation
```bash
make install          # Install all dependencies with UV
make verify-deps      # Verify all required dependencies are installed
make baml            # Generate BAML client code (run after .baml changes)
```

### Service Management
```bash
make start           # Start all AWA services (API, Temporal, Worker)
make start-detach    # Start services in detached mode
make stop            # Stop all AWA services
make stop-all        # Aggressively stop all services including orphaned
make clean-start     # Fresh start: clean, install, then start
make start-terminate # Start services and terminate all workflows
```

### Application Execution
```bash
make run             # Run the main AWA application
make mcp             # Run the MCP server
awa --help          # CLI help (after installation)
```

### MCP Server Commands
```bash
# Start MCP server for development
make mcp

# Test MCP server functionality
uv run -m awa.main mcp

# MCP server runs on default port (check config.yaml for port)
# Access via MCP client tools or Claude Code integration
```

### Testing Commands
```bash
make test                    # Run unit tests
make test-verbose           # Run unit tests with verbose output
make test-coverage          # Run unit tests with coverage report
make test-api               # Run API integration tests
make test-workflow          # Run workflow tests (manual service start/stop)
make run-test-workflow      # Run workflow tests (automatic service management)
make test-all               # Run all tests (unit + api + workflow)
make test-ui                # Run Playwright UI tests
make test-ui-headed         # Run UI tests in headed mode
make test-ui-debug          # Run UI tests in debug mode
```

### MCP Server Testing
```bash
# Test MCP server components
uv run -m pytest tests/unit/awa/core/mcp/

# Test MCP server integration (requires running services)
uv run -m pytest tests/api/ -k mcp

# Test workflow execution via MCP
uv run -m pytest tests/workflow/ -k mcp
```

### Code Quality & Formatting
```bash
make lint            # Check code with Ruff
make lint-fix        # Fix linting issues automatically
make format          # Format code with Ruff
make pre-commit      # Run pre-commit hooks on staged files
make pre-commit-all  # Run pre-commit hooks on all files
```

### Docker Commands
```bash
make docker-build         # Build all Docker images
make docker-build-api     # Build AWA API Docker image
make docker-build-ui      # Build AWA UI Docker image
make docker-up           # Start services with docker compose
make docker-down         # Stop and remove containers
make docker-logs         # View service logs
make start-docker        # Main command for running with Docker
make start-docker-supporting # Docker supporting services only
```

### Documentation
```bash
pnpm install              # Install Node.js dependencies
pnpm run copy-cookbook-docs # Copy cookbook documentation
pnpm run docs:dev         # Start local documentation server
pnpm run docs:build       # Build documentation site
```

### CI/CD Commands
```bash
make ci                   # Run CI using Dagger
make ci-workflow-tests    # Run CI workflow tests using Dagger
make ci-publish-sdk       # Publish SDK using Dagger
```

### AI Rules Management
```bash
make ai-rules-generate    # Generate AI rule files
make ai-rules-clean       # Clean generated AI rule files
```

### Utility Commands
```bash
make clean               # Remove temporary files and build artifacts
make help               # Show all available commands
```

## Direct UV Commands (Alternative)

### When Make is not available:
```bash
uv sync                  # Install dependencies
uv run -m pytest tests/unit  # Run unit tests
uv run -m awa.main --help    # Run AWA CLI
uv run -m awa.main start     # Start AWA services
uv run -m awa.main mcp       # Run MCP server
uv run python -m baml_client  # Generate BAML client
```

## MCP Server Development Workflow

### Starting MCP Development
```bash
make start-detach        # Start supporting services (Temporal, etc.)
make mcp                 # Run MCP server in development mode
# MCP server will auto-reload on code changes
```

### Testing MCP Changes
```bash
# Test specific MCP functionality
uv run -m pytest tests/unit/awa/core/mcp/test_mcp_server.py

# Test MCP integration with workflows
uv run -m pytest tests/workflow/ -k mcp -v

# Test new non-blocking workflow features
uv run -m pytest tests/unit/awa/core/mcp/test_async_workflows.py
```

### MCP Client Testing
```bash
# Use AWA CLI to test MCP workflows
awa workflow start --workflow my_workflow --input '{"data": "test"}'

# Test via MCP client (if available)
# Connect to MCP server at configured host:port
```

## System Commands (macOS/Darwin)

### File Operations
- `ls -la` - List files with details
- `find . -name "*.py"` - Find Python files
- `rg "pattern"` - Search in files (ripgrep - preferred over grep)
- `tree` - Show directory structure

### Git Operations
- `git status` - Check repository status
- `git log --oneline -10` - Recent commits
- `git diff` - Show changes
- `git branch -a` - List all branches

### Process Management
- `ps aux | grep awa` - Find AWA processes
- `ps aux | grep mcp` - Find MCP server processes
- `lsof -i :8000` - Check port usage (API server)
- `lsof -i :3001` - Check MCP server port
- `pkill -f "temporal"` - Kill Temporal processes
- `pkill -f "mcp"` - Kill MCP server processes

### Docker Operations
- `docker ps` - List running containers
- `docker logs <container>` - View container logs
- `docker compose ps` - List compose services
- `docker system prune` - Clean up Docker resources

## Environment Variables

### Required for LLM Integration
- `OPENAI_API_KEY` - OpenAI API key
- `AZURE_OPENAI_API_KEY` - Azure OpenAI key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint

### MCP Server Configuration
- `MCP_SERVER_HOST` - MCP server host (default: localhost)
- `MCP_SERVER_PORT` - MCP server port (check config.yaml)
- `MCP_LOG_LEVEL` - MCP server log level

### Optional Configuration
- `LANGFUSE_SECRET_KEY` - Langfuse monitoring
- `JIRA_API_TOKEN` - Jira integration
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Development Workflow

### Starting New Work
1. `make clean-start` - Fresh environment
2. `make test` - Verify tests pass
3. Make changes
4. `make lint-fix` - Fix code style
5. `make test` - Verify tests still pass
6. `make pre-commit` - Run final checks

### MCP Server Development Cycle
1. `make start-detach` - Start supporting services
2. `make mcp` - Start MCP server in dev mode
3. Make MCP server changes
4. Server auto-reloads (FastMCP feature)
5. Test changes via MCP client
6. `make test` - Run MCP server tests
7. `make stop` - Stop services when done

### After BAML Changes
1. Edit `.baml` files in `awa/core/baml_src/`
2. `make baml` - Regenerate client
3. `make test` - Verify integration works

### Non-Blocking Workflow Extension Development
1. Implement new MCP tools in `awa/core/mcp/mcp_server.py`
2. Add workflow handle storage logic
3. Update tool registration in `create_mcp_app()`
4. Add comprehensive tests in `tests/unit/awa/core/mcp/`
5. Test with actual workflows using integration tests

### Before Committing
1. `make format` - Format code
2. `make lint` - Check for issues
3. `make test-coverage` - Verify test coverage
4. `make test` - Run all unit tests
5. `make pre-commit` - Final validation

### MCP Integration Testing
```bash
# Full integration test workflow
make start-detach                    # Start services
make test                           # Unit tests
make test-api                       # API integration tests
uv run -m pytest tests/workflow/ -k mcp  # MCP workflow tests
make stop                           # Clean up
```
