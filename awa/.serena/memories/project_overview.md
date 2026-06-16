# Slalom Agentic Workflow Accelerator (AWA) - Project Overview

## Purpose
AWA is an accelerator for building agentic workflows designed to provide a toolbox that Slalom teams can use to ramp up and deliver value quickly. It serves as either:
- Foundation of a client deliverable (building an agentic workflow _for_ a client project)
- Starting point for building agentic workflows to assist with a client project (building an agentic workflow to _accelerate_ a client project)

## Core Technology Stack

### Primary Languages & Runtime
- **Python**: 3.12+ (primary language)
- **Node.js**: For documentation and UI components
- **TypeScript**: For UI development

### Core Frameworks & Libraries
- **FastAPI**: Web API framework with OpenAPI support
- **Temporal**: Workflow orchestration engine for durable execution
- **BAML**: LLM interaction framework with type safety
- **Typer**: CLI framework for command-line interface
- **ChromaDB**: Vector database for embeddings
- **Pydantic**: Data validation and settings management

### LLM & AI Integration
- **OpenAI**: Primary LLM provider
- **Azure OpenAI**: Enterprise LLM integration
- **Google Vertex AI**: Alternative LLM provider
- **Anthropic Claude**: Additional LLM option
- **Langfuse**: LLM observability and monitoring

### Development & Build Tools
- **UV**: Modern Python package manager (primary)
- **Ruff**: Code formatting and linting
- **Pytest**: Testing framework
- **Pre-commit**: Git hooks for code quality
- **Docker**: Containerization and deployment

## Project Structure

### Core Directories
- `awa/` - Main Python package
  - `core/` - Core business logic
    - `workflows/` - Temporal workflow definitions
    - `activities/` - Temporal activities (external operations)
    - `api/` - FastAPI routes and endpoints
    - `cli/` - Typer CLI commands
    - `engine/` - Temporal client and workflow engine
    - `models/` - Pydantic data models
    - `mcp/` - MCP (Model Context Protocol) server
    - `baml_src/` - BAML function definitions
    - `baml_client/` - Generated BAML client code
- `tests/` - Comprehensive test suite
  - `unit/` - Unit tests
  - `api/` - API integration tests
  - `workflow/` - Temporal workflow tests
  - `ui/` - Playwright UI tests
- `docs/` - Documentation and guides
- `ui/` - Frontend user interface
- `infra/` - Infrastructure and deployment configs
- `examples/` - Example workflows and implementations

### Key Configuration Files
- `pyproject.toml` - Python project configuration and dependencies
- `config.yaml` - Runtime configuration (LLM providers, services)
- `Makefile` - Cross-platform development commands
- `ruff.toml` - Code style and linting configuration
- `pytest.ini` - Test framework configuration
- `docker-compose.yml` - Container orchestration

## Entry Points
- **CLI**: `awa` command (via `awa.main:main`)
- **API Server**: FastAPI application with OpenAPI docs
- **MCP Server**: Model Context Protocol server for AI integrations
- **Temporal Worker**: Workflow execution engine

## Documentation
- **Primary Docs**: https://awa.slalomdev.io/docs/
- **Local Docs**: Built with VitePress (`pnpm run docs:dev`)

## Architecture Pattern
AWA follows a **durable agentic workflow** architecture:
1. CLI/API receives requests
2. Temporal workflows orchestrate execution
3. Activities perform atomic operations (file I/O, LLM calls, agent execution)
4. BAML handles structured LLM interactions
5. Results returned through durable execution guarantees
