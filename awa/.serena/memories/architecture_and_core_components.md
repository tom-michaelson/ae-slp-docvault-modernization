# AWA Architecture and Core Components

## Architecture Overview
AWA follows a **durable agentic workflow** architecture built around Temporal for orchestration, providing reliability and fault tolerance for long-running AI operations.

### Core Architecture Layers

#### 1. Interface Layer
- **CLI (Typer)**: Command-line interface for development and operations
- **REST API (FastAPI)**: HTTP endpoints with OpenAPI documentation
- **MCP Server**: Model Context Protocol for AI tool integrations
- **WebUI**: Frontend interface for workflow management

#### 2. Orchestration Layer
- **Temporal Workflows**: Define business logic with durable execution
- **Temporal Activities**: Perform external operations (atomic, idempotent)
- **Workflow Engine**: Manages execution, retries, and state persistence

#### 3. AI Integration Layer
- **BAML Functions**: Structured LLM interactions with type safety
- **LLM Providers**: OpenAI, Azure OpenAI, Google Vertex, Anthropic
- **Agent Modes**: Containerized AI agents (Claude, Goose, Codex, OpenCode)
- **Vector Database**: ChromaDB for embeddings and retrieval

#### 4. Data & Storage Layer
- **SQLite**: Default local database (Temporal persistence)
- **File System**: Local file operations and workspace management
- **Configuration**: YAML-based runtime configuration
- **Observability**: Langfuse for LLM monitoring

## Key Components

### MCP (Model Context Protocol) Server
**Location**: `awa/core/mcp/mcp_server.py`
**Framework**: FastMCP
**Purpose**: Provides AI tools and workflow execution capabilities

#### Current MCP Tools
- **`health()`**: Health check endpoint
- **`start_workflow()`**: **BLOCKING** workflow execution
- **Auto-discovered workflow tools**: Dynamic tool registration via `register_all_workflow_tools()`

#### MCP Architecture Components
- **Tool Registration**: `_registered_workflow_tools` global registry
- **Schema Conversion**: `_convert_schema_to_function_params()` for dynamic tool creation
- **Workflow Discovery**: `discover_mcp_workflows()` scans available workflows
- **Parameter Validation**: `_validate_input_data()` for input sanitization
- **Execution**: `_execute_workflow_tool()` handles tool execution

#### Planned MCP Extension: Non-Blocking Workflows
**New Tools to Add**:
- `start_workflow_async()` - Non-blocking workflow initiation
- `get_workflow_status()` - Check workflow progress
- `get_workflow_result()` - Retrieve completed results
- `list_active_workflows()` - Show all running workflows

**Implementation Strategy**:
- Use existing `TemporalClient.start_workflow()` (already non-blocking)
- In-memory `WorkflowHandle` storage for result retrieval
- Leverage existing `WorkflowManagementClient` for status queries
- Maintain backward compatibility with blocking `start_workflow()`

### Temporal Integration
**Location**: `awa/core/engine/`

#### TemporalClient
**Key Methods**:
- **`execute_workflow()`**: BLOCKING - waits for completion, returns final result
- **`start_workflow()`**: NON-BLOCKING - returns `WorkflowHandle` immediately
- **`list_workflow_runs()`**: Query workflow status
- **`get_workflow_run(run_id)`**: Get specific workflow details
- **`get_workflow_ui_link()`**: Generate Temporal UI links

#### WorkflowManagementClient
**Purpose**: Workflow lifecycle and status management
**Key Methods**:
- **`list_workflow_runs()`**: Lists all workflows with status
- **`get_workflow_run(run_id)`**: Gets specific workflow details
- **`get_workflow_ui_link()`**: Gets Temporal UI links
- **`sort_workflows_by_status()`**: Organize workflows by execution status

#### ServiceManager
**Purpose**: High-level service orchestration
- **`execute_workflow()`**: Blocking execution (used by current MCP)
- Manages service lifecycle
- Coordinates between different AWA components

### BAML Integration
**Location**: `awa/core/baml_src/` and `awa/core/baml_client/`

- **Function Definitions**: `.baml` files defining LLM interactions
- **Generated Client**: Type-safe Python client for BAML functions
- **Type Safety**: Structured input/output with Pydantic models
- **Multi-Provider**: Supports multiple LLM providers with fallbacks

### API Layer
**Location**: `awa/core/api/`

- **FastAPI Application**: RESTful API with automatic OpenAPI docs
- **Route Versioning**: Structured endpoint versioning
- **Health Checks**: Service health and status endpoints
- **Authentication**: JWT-based authentication support

### CLI Interface
**Location**: `awa/core/cli/`

- **Command Structure**: Hierarchical command organization
- **Workflow Commands**: Start, stop, query workflows
- **Development Commands**: Setup, testing, deployment helpers
- **Configuration Commands**: Environment and service management

### Activity System
**Location**: `awa/core/activities/`

Activities are the building blocks of workflows, performing specific operations:

- **File Operations**: Read, write, manipulate files
- **LLM Operations**: Call BAML functions, process responses
- **Git Operations**: Version control interactions
- **Agent Execution**: Run containerized AI agents
- **External APIs**: Call third-party services
- **Data Processing**: Transform and validate data

### Workflow Patterns
**Location**: `awa/core/workflows/`

Common workflow patterns implemented:

- **Linear Workflows**: Sequential step execution
- **Parallel Workflows**: Concurrent activity execution
- **Child Workflows**: Nested workflow composition
- **Saga Patterns**: Compensating transaction support
- **State Machines**: Complex state transitions

## Configuration Architecture

### Hierarchical Configuration
1. **config.yaml**: Primary runtime configuration
2. **Environment Variables**: Override configuration values
3. **CLI Arguments**: Runtime parameter overrides
4. **Default Values**: Fallback configuration

### Configuration Categories
- **LLM Providers**: Model configurations and credentials
- **Temporal**: Connection and execution settings
- **Logging**: Log levels and output configuration
- **Services**: External service integrations (Jira, etc.)
- **Development**: Debug and development-specific settings

## Data Models
**Location**: `awa/core/models/`

- **Pydantic Models**: Type-safe data structures
- **Configuration Models**: Settings and environment configuration
- **Workflow Models**: Input/output schemas for workflows
- **API Models**: Request/response schemas for REST endpoints
- **MCP Models**: `WorkflowExecutionResult` and related types

## Extension Points

### MCP Server Extensions (Current Focus)
- **New Tool Registration**: Add tools via `mcp.tool("tool_name")(function)`
- **Handle Storage**: In-memory workflow handle management
- **Error Handling**: Custom `ToolError` subclasses
- **Status Management**: Workflow lifecycle tracking

### Custom Workflows
- Create new workflow classes inheriting base patterns
- Define custom activities for specific use cases
- Register workflows in the workflow registry

### Custom Activities
- Implement idempotent operations
- Handle failures gracefully with retries
- Follow activity naming conventions (`*Activity` classes)

### LLM Integration
- Add new BAML functions for specific AI operations
- Configure new LLM providers in configuration
- Implement custom prompt templates and schemas

### API Extensions
- Add new FastAPI routes with proper versioning
- Implement custom middleware for cross-cutting concerns
- Extend authentication and authorization

## Design Principles

1. **Durability**: All workflows survive process restarts
2. **Idempotency**: Activities can be safely retried
3. **Type Safety**: Strong typing throughout with Pydantic
4. **Observability**: Comprehensive logging and monitoring
5. **Modularity**: Clear separation of concerns
6. **Testability**: Comprehensive test coverage at all levels
7. **Backward Compatibility**: Extensions don't break existing functionality
