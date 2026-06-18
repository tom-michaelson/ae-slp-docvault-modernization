# Logging

AWA provides a comprehensive logging system with support for component-based logging, Temporal workflow integration, workflow-specific log aggregation, and flexible output options.

## Features

- **Component-based logging**: Allows for easy separation of logs by API, CLI, UI, Engine, Server, Worker, and Workflows
- **Temporal workflow integration**: Seamless logging from within Temporal workflows using built-in Temporal logging utilities
- **Unified logging**: All logs consolidated into a single application log with component context
- **Workflow-specific logging**: Automatic aggregation of all logs from a workflow hierarchy into dedicated log files
- **Cross-process log collection**: Captures logs from workflows running in different processes (including cookbook workflows)
- **Console streaming**: Real-time streaming of workflow logs to the terminal where `awa run` was executed
- **Subprocess logging**: Clean handling of subprocess output without double-formatting
- **Configurable file rotation**: Automatic log rotation based on file size (default: 1MB)
- **File retention**: Automatic cleanup of old log files (default: 30 days)
- **File compression**: Automatic compression of rotated files (ZIP format)
- **Multiple output formats**: Console, file, and structured JSON logging
- **Rich context**: Automatic inclusion of workflow IDs, components, and execution context
- **Component-specific log levels**: Configure different log levels for each component via config.yaml

## Configuration

### Environment Variables

Configure logging behavior using environment variables in your `.env` file:

```bash
# Overall log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=DEBUG

# Log directory path (defaults to 'logs' in the project root)
LOG_PATH=logs

# File rotation settings (when to rotate log files)
LOG_FILE_ROTATION_SIZE=1 MB

# Enable/disable logging outputs
LOG_CONSOLE_ENABLED=true
LOG_FILE_ENABLED=true

# Structured JSON logging
LOG_ENABLE_JSON=true

# Workflow logging directory
LOG_WORKFLOW_DIR=logs/workflows
```

### Configuration File (config.yaml)

Configure component-specific log levels in your `config.yaml`:

```yaml
# Option 1: Single log level for all components
logging:
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Option 2: Component-specific log levels
logging:
  log_level:
    api: "INFO"
    ui: "ERROR"
    worker: "DEBUG"
    server: "WARNING"
    workflow: "INFO"
    activity: "INFO"
```

## Log Files Structure

AWA creates a structured logging hierarchy organized by workflow type:

```
logs/
├── app.log                         # All application logs with component context
├── app.json                        # Structured JSON logs (if enabled)
├── app.2024-01-15_14-30-22.log.zip # Compressed rotated files
├── app.2024-01-15_14-30-22.json.zip # Compressed JSON files
├── workers/                        # Worker-specific logs (cookbook, recipes, etc.)
│   ├── recipes-worker.log         # Recipes worker logs
│   ├── recipes-worker.json        # Structured recipes logs (if enabled)
└── workflows/                      # Workflow-specific logs organized by type
    ├── awa-hello-world/            # Core workflow type directory
    │   ├── 20250804_162851_799_65e8a/  # Individual workflow execution
    │   │   ├── workflow.log             # Main workflow execution log
    │   │   └── llm/                     # LLM call logs for this workflow
    │   │       ├── 20250804_162851_500_ExtractIntent.yaml
    │   │       └── 20250804_162852_100_GenerateResponse.yaml
    │   └── 20250804_163245_123_abcd1/
    │       ├── workflow.log
    │       └── llm/
    │           └── 20250804_163246_200_ProcessData.yaml
    ├── hello-world/                # Cookbook workflow type directory
    │   └── 20250804_164512_456_efgh2/
    │       ├── workflow.log
    │       └── llm/
    │           └── 20250804_164513_300_SimpleTransform.yaml
    └── [other-workflow-types]/
        └── [workflow-instance-id]/
            ├── workflow.log
            └── llm/
                └── [llm-call-logs]
```

### File Rotation and Management

AWA uses [loguru's](https://github.com/Delgan/loguru) built-in file management features:

- **Rotation**: Log files are rotated when they reach the configured size (default: 1 MB)
- **Retention**: Old log files are automatically deleted after 30 days
- **Compression**: Rotated files are automatically compressed using ZIP format

These settings work together in sequence:

1. When a log file reaches 1MB, it gets rotated (renamed with timestamp)
2. The old file is immediately compressed to save disk space
3. Files older than 30 days are automatically deleted

You can customize the rotation size via environment variables:

```bash
# Rotate at 512KB
LOG_FILE_ROTATION_SIZE=512 KB

# Rotate at 5MB
LOG_FILE_ROTATION_SIZE=5 MB

# Rotate at 10MB
LOG_FILE_ROTATION_SIZE=10 MB
```

## Component-Based Logging

AWA's logging system separates infrastructure setup from logger usage:

- **`init_logging()`**: One-time setup of the logging infrastructure (console, files, JSON)
- **`get_logger(component)`**: Creates component-specific loggers with automatic context
- **`setup_workflow_logging(workflow_id)`**: Sets workflow context for enhanced logging

### Available Components

- **AWA-API**: FastAPI server and HTTP endpoints
- **AWA-CLI**: Command-line interface operations
- **AWA-UI**: User interface components
- **AWA-SERVER**: Server components
- **AWA-CLIENT**: Client components
- **AWA-WORKER**: Worker components
- **AWA-WORKFLOW**: Individual workflow executions
- **AWA-ACTIVITY**: Activity executions
- **AWA-AUTH**: Authentication and authorization operations
- **HTTP**: HTTP library logs (httpx, httpcore network operations)

Note: Temporal engine and workflow orchestration logs are automatically mapped to appropriate components based on their logger names.

### Using Component Loggers

```python
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging

# Step 1: Initialize the logging infrastructure (done once per application)
init_logging()

# Step 2: Get component-specific loggers with automatic context
api_logger = get_logger(LoggerComponent.API)
cli_logger = get_logger(LoggerComponent.CLI)
ui_logger = get_logger(LoggerComponent.UI)
server_logger = get_logger(LoggerComponent.SERVER)

# Step 3: Use the loggers - they automatically include component context
api_logger.info("API server starting...")
cli_logger.info("Processing CLI command...")
ui_logger.info("UI component loaded...")
server_logger.info("Server component started...")

# Error logging automatically includes component context and stack traces
api_logger.exception("Database connection failed")

# Authentication-specific logging
auth_logger = get_logger(LoggerComponent.AUTH)
auth_logger.info("JWT token validated successfully")
auth_logger.warning("Token refresh required")
auth_logger.debug("JWKS cache hit")
```

### Logger Initialization

The logging system uses a clean separation of concerns:

```python
# Application startup - initialize logging infrastructure once
init_logging()  # Sets up console, file, and JSON logging

# For file-only logging (no console)
init_logging(file_only=True)

# Then get component-specific loggers as needed
logger = get_logger(LoggerComponent.API)
logger.info("This log will include 'AWA-API' component context")
```

## Workflow Logging

AWA provides comprehensive workflow logging with automatic log aggregation, cross-process collection, and real-time streaming.

### Workflow-Specific Log Files

When you execute a workflow using `awa run`, AWA automatically:

1. Creates a dedicated directory for that workflow execution in `logs/workflows/[workflow-type]/[workflow-id]/`
2. Captures all logs from the workflow hierarchy (parent and child workflows) in `workflow.log`
3. Saves all LLM interactions in the `llm/` subdirectory as individual YAML files
4. Collects logs from activities across all processes
5. Streams logs in real-time to your terminal

Example:

```bash
uv run -m awa.main run -w awa-hello-world -i '{"name":"Claude"}'
# Creates directory: logs/workflows/hello-world-recipe/20250130_123456_789_abc12/
#   - workflow.log: All workflow execution logs
#   - llm/*.yaml: Individual LLM call logs
# Streams all workflow logs to your terminal in real-time
```

### Cross-Process Log Collection

AWA's logging system automatically captures logs from:

- Core workflows running in the worker
- Recipe workflows (when enabled via `recipes: true` config) running in the same unified worker
- Child workflows spawned by parent workflows
- Activities executed across different processes

All these logs are aggregated into a single file for the top-level workflow, making debugging and monitoring seamless.

## LLM Call Logging

AWA provides comprehensive logging for all Large Language Model (LLM) interactions, capturing detailed information about each call for debugging, cost tracking, and performance analysis.

### LLM Log Structure

LLM logs are automatically saved as YAML files within each workflow's execution directory:

```
logs/workflows/
└── [workflow-type]/
    └── [workflow-instance-id]/
        ├── workflow.log           # Main workflow execution log
        └── llm/                   # LLM-specific logs directory
            └── [timestamp]_[function_name].yaml
```

Each LLM log file contains:

- **Request/Response Data**: Complete input and output from the LLM
- **Model Information**: Model name, provider, and configuration
- **Performance Metrics**: Token usage, latency, and timing information
- **Temporal Context**: Workflow ID, activity ID, and execution metadata
- **Error Details**: If the LLM call failed, includes error information

### LLM Log File Naming

LLM log files follow a consistent naming pattern:

```
[YYYYMMDD_HHMMSS_mmm]_[BamlFunctionName][_failure].yaml
```

- **Timestamp**: Sortable timestamp for when the LLM call was initiated
- **Function Name**: The BAML function that was executed
- **Failure Suffix**: Added if the LLM call failed

Example filenames:

- `20250804_162851_500_ExtractIntent.yaml` - Successful call
- `20250804_162852_100_GenerateResponse_failure.yaml` - Failed call

## Basic Workflow Logging

Use the `workflow.logger` object to log from within a workflow.

```python
from temporalio import workflow

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, input_data: str) -> str:
        # Use Temporal's built-in logger
        workflow.logger.info(f"Processing input: {input_data}")

        # Logs automatically include workflow context and component info
        workflow.logger.info("Executing activity...")  # Shows: AWA-WORKFLOW | workflow-id | Executing activity...

        try:
            result = await workflow.execute_activity(
                my_activity,
                input_data,
                start_to_close_timeout=timedelta(seconds=30),
            )
            workflow.logger.info(f"Activity completed: {result}")
            return result
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {e}")
            workflow.logger.exception("Full exception details")
            raise
```

### Workflow Context Integration

AWA automatically captures workflow context from Temporal and includes it in the unified log file. Workflow logs appear with enhanced context showing the workflow ID alongside the component information.

For workflows that need enhanced context tracking:

```python
from awa.core.logger.logger import setup_workflow_logging, get_logger, LoggerComponent

# Set up workflow context (enhances all logs with workflow ID)
workflow_id = f"MyWorkflow_{timestamp}"
setup_workflow_logging(workflow_id)

# Get a workflow logger - logs will include workflow context
workflow_logger = get_logger(LoggerComponent.WORKFLOW, workflow_id=workflow_id)
workflow_logger.info("Workflow started")  # Shows: AWA-WORKFLOW | my-workflow-123 | Workflow started
```

## Subprocess Logging

AWA handles subprocess output (from services like UI, API, Worker) through a clean raw output approach:

### How It Works

- **ServiceManager** launches AWA services as subprocesses
- **Raw Output**: Subprocess logs are written directly without re-processing
- **No Double Formatting**: Prevents nested/duplicate log formatting
- **Preserved Formatting**: Subprocess logs maintain their original AWA component formatting

### Example

When running `uv run -m awa.main run`, you'll see both types of logs:

```
# Main process logs (formatted by current process)
2025-07-11 15:30:33.645 | INFO | AWA-SERVER | Starting services...

# Subprocess logs (raw output from UI service)
2025-07-11 15:30:46.269 | INFO | AWA-UI | Done in 440ms using pnpm v10.6.2
2025-07-11 15:30:46.269 | INFO | AWA-UI | > astro dev
```

Both appear in the same `app.log` file but maintain clean, consistent formatting without duplication.

## Centralized Logging Architecture

AWA implements a sophisticated centralized logging system that aggregates logs from multiple workers and processes into unified workflow-specific log files.

### Architecture Overview

The logging system uses a hub-and-spoke model with the core AWA API server acting as the central log aggregation point:

```
┌─────────────────┐    SocketIO    ┌──────────────────┐
│ Unified Worker  │ ──────────────► │ Core SocketIO    │
│ (Core+Recipes)  │                 │ Server           │
└─────────────────┘                 └──────────────────┘
                                             │
                                    File Logger
                                             ▼
                                    ┌─────────────────┐
                                    │ Unified Log     │
                                    │ Files           │
                                    └─────────────────┘
```

### Key Features

- **Cross-Process Log Aggregation**: Captures logs from workflows running across different processes and workers
- **Workflow Hierarchy Support**: Automatically aggregates parent and child workflow logs into a single file
- **Real-Time Streaming**: Streams workflow logs in real-time to the terminal where `awa run` was executed
- **Worker Log Separation**: Separates infrastructure logs (AWA-WORKER) from workflow execution logs (AWA-WORKFLOW, AWA-ACTIVITY)
- **Message Truncation**: Automatically truncates messages exceeding 1MB to prevent system issues
- **Structured Organization**: Organizes logs by workflow type for easy navigation and debugging

### Log Routing Rules

The system intelligently routes different types of logs:

- **AWA-WORKER logs**: Stay in the worker terminal where they originate (not forwarded to invoking terminal)
- **AWA-WORKFLOW logs**: Forwarded to invoking terminal via SocketIO and written to workflow log files
- **AWA-ACTIVITY logs**: Forwarded to invoking terminal via SocketIO and written to workflow log files
- **All logs**: Written to appropriate log files for permanent storage

### Context Propagation

AWA uses Temporal's native context propagation to maintain workflow context across process boundaries:

- **Header-Based Propagation**: Passes workflow metadata through Temporal headers
- **Global Dictionary Fallback**: Uses in-memory cache for activities when sandbox mode prevents header propagation
- **Multi-Level Support**: Supports arbitrary workflow nesting depths (parent → child → grandchild → ...)
- **Automatic Cleanup**: Prevents memory leaks by cleaning up context when workflows complete

## Authentication and Security

### Service Authentication for Containerized Deployments

When deploying AWA in containerized environments with authentication enabled (`PUBLIC_AUTH_MODE=cognito`), workers need to authenticate with the core API for log streaming.

#### Generating Service Tokens

Generate a secure service token:

```bash
# Generate a secure random token (32+ characters recommended)
openssl rand -hex 32
# Output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

For a full production deployment, it would be better to use a secrets manager to store the service token to enable secrets rotation, revocation, and auditing. However, because AWA is designed to be cloud-agnostic, we use an environment variable for now.

#### Configuration

Configure the same service token in **both** core AWA and worker environments:

**Core AWA** (`.env`):

```bash
PUBLIC_AUTH_MODE=cognito
# ... other Cognito settings ...
AWA_SERVICE_TOKEN=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**Cookbook/Recipe Workers** (`.env`):

```bash
AWA_SERVICE_TOKEN=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

#### Authentication Modes

- **Anonymous Mode** (`PUBLIC_AUTH_MODE=none`): No authentication required - suitable for local development
- **Authenticated Mode** (`PUBLIC_AUTH_MODE=cognito`): Requires valid service token for worker connections

#### Security Best Practices

1. **Use Strong Tokens**: Generate cryptographically secure tokens (32+ characters)
2. **Environment-Specific Tokens**: Use different tokens for dev/staging/production
3. **Secure Storage**: Store tokens in environment variables, not in code
4. **Regular Rotation**: Rotate service tokens periodically in production
5. **Access Control**: Limit access to service token environment variables

#### Cloud-Native Considerations

This service token approach is designed for multi-cloud containerized deployments and works with:

- **AWS**: ECS, EKS, or container instances
- **Azure**: Container Instances, AKS
- **GCP**: Cloud Run, GKE
- **On-premises**: Docker, Kubernetes, container orchestration platforms

The service token can be managed through your cloud provider's secret management service or container orchestration secret management.

## Development

This section covers how the AWA logging system works internally and provides guidance for developers working with the logging infrastructure.

### How Logging Works Across the System

AWA's logging system is built on several key architectural principles:

#### 1. Component-Based Architecture

The logging system uses a component-based approach with predefined components:

```python
class LoggerComponent(StrEnum):
    API = "AWA-API"           # FastAPI server and HTTP endpoints
    CLI = "AWA-CLI"           # Command-line interface operations
    UI = "AWA-UI"             # User interface components
    SERVER = "AWA-SERVER"     # Server components
    CLIENT = "AWA-CLIENT"     # Client components
    WORKER = "AWA-WORKER"     # Worker components
    WORKFLOW = "AWA-WORKFLOW" # Individual workflow executions
    ACTIVITY = "AWA-ACTIVITY" # Activity executions
    ENGINE = "AWA-ENGINE"     # Engine components
    SCRIPT = "AWA-SCRIPT"     # Script executions
    AUTH = "AWA-AUTH"         # Authentication and authorization
    HTTP = "HTTP"             # HTTP library logs (httpx, httpcore)
    SOCKETIO = "SOCKETIO-SERVER" # Socket.IO server logs
    UVICORN = "UVICORN"       # Uvicorn web server logs
```

#### 2. Log Infrastructure Setup

The system separates infrastructure setup from logger usage:

```python
# Infrastructure setup (done once per application)
from awa.core.logger.logger import init_logging
init_logging()  # Sets up handlers, formatters, and configuration

# Logger usage (done throughout the application)
from awa.core.logger.logger import get_logger, LoggerComponent
logger = get_logger(LoggerComponent.API)
logger.info("Application started")
```

#### 3. Context Propagation

AWA uses Temporal's native context propagation to maintain workflow context:

- **Header-Based Propagation**: Passes workflow metadata through Temporal headers
- **Context Variables**: Uses Python's `contextvars` for thread-safe context management
- **Global Dictionary Fallback**: In-memory cache when sandbox mode prevents header propagation

### Log File Locations and Organization

Understanding where logs are written is crucial for development and debugging:

#### Primary Log Locations

```bash
# Default structure (configurable via LOG_PATH environment variable)
logs/
├── app.log                    # All application logs unified
├── app.json                   # Structured JSON logs (if LOG_ENABLE_JSON=true)
├── workers/                   # Worker-specific logs
│   ├── recipes-worker.log
│   └── recipes-worker.json
└── workflows/                 # Workflow-specific logs organized by type
    ├── awa-hello-world/       # Workflow type directory
    │   ├── 20250814_162851_799_65e8a/    # Individual workflow execution
    │   │   ├── workflow.log               # Workflow execution log
    │   │   └── llm/                       # LLM call logs
    │   │       └── *.yaml
    │   └── 20250814_163245_123_abcd1/
    │       ├── workflow.log
    │       └── llm/
    │           └── *.yaml
    └── file-based-transform/
        └── 20250814_164512_456_efgh2/
            ├── workflow.log
            └── llm/
                └── *.yaml
```

#### Environment Variable Control

```bash
# Customize log locations
LOG_PATH=custom_logs                    # Changes base directory to 'custom_logs/'
LOG_WORKFLOW_DIR=custom_logs/workflows  # Changes workflow log directory
LOG_ENABLE_JSON=true                    # Enables app.json structured logging
```

#### Workflow Log Files

Workflow-specific logs are organized in directories following this structure:

```
logs/workflows/[workflow-type]/[YYYYMMDD_HHMMSS_mmm_[random5char]]/
                                └─────┬─────┘└──┬──┘└┬┘└─────┬─────┘
                                      │        │    │       │
                                   Date    Time  Ms   Random ID
├── workflow.log    # Main workflow execution log
└── llm/           # LLM call logs directory
    └── [timestamp]_[function_name].yaml
```

### Development Environment Variables

Essential environment variables for logging during development:

```bash
# Basic Configuration
LOG_LEVEL=DEBUG                    # Set to DEBUG for verbose development logs
LOG_CONSOLE_ENABLED=true          # Enable console output (default: true)
LOG_FILE_ENABLED=true             # Enable file logging (default: true)

# File Management
LOG_PATH=logs                     # Base log directory (default: logs)
LOG_FILE_ROTATION_SIZE=1 MB       # Rotate when files reach this size
LOG_ENABLE_JSON=false            # Enable structured JSON logs (default: false)

# Workflow Logging
LOG_WORKFLOW_DIR=logs/workflows   # Directory for workflow-specific logs

# Development-Specific
DEBUG_MODE=true                   # Enable debug mode features
```

### Testing the Logging Infrastructure

AWA provides testing utilities for validating logging behavior:

#### Unit Testing Logging

```python
import pytest
from pathlib import Path
from awa.core.logger.logger import get_logger, LoggerComponent, init_logging

def test_logger_setup(tmp_path: Path):
    """Test basic logger setup and output."""
    # Initialize logging with temporary directory
    init_logging()

    logger = get_logger(LoggerComponent.API)
    logger.info("Test message")

    # Verify log file creation and content
    log_files = list(tmp_path.glob("**/*.log"))
    assert len(log_files) > 0
```

#### Integration Testing Logging

To test the complete logging infrastructure including workflow log aggregation:

1. **Start AWA services** in development mode
2. **Execute a test workflow** to generate logs
3. **Validate log files** are created with expected structure
4. **Check log content** for proper component context and workflow IDs

### Key Implementation Details

#### Log Filtering and Routing

The system uses intelligent log filtering:

```python
def _filter_application_logs(record: dict) -> bool:
    """Filter logs to exclude workflow execution logs from application log."""
    component = record["extra"].get("component", "")

    # Workflow and activity logs go to separate files
    if component in ("AWA-WORKFLOW", "AWA-ACTIVITY"):
        return False
    return True
```

#### SocketIO Log Streaming

For cross-process log collection, AWA uses Socket.IO:

```python
# Automatic setup in workflows running in separate processes
from awa.core.logger.socketio_handler import SocketIOLogHandler

handler = SocketIOLogHandler()
# Connects to central log server and streams logs in real-time
```

#### Context Variables

The system maintains workflow context using Python's `contextvars`:

```python
from awa.core.logger.workflow_context import workflow_context, top_level_workflow_context

# Context is automatically set by workflow utilities
workflow_id = workflow_context.get()
top_level_id = top_level_workflow_context.get()
```

### Debugging Logging Issues

Common debugging techniques for logging problems:

#### 1. Check Log Configuration

```python
from awa.core.logger.log_config import get_log_config
from awa.core.models.config.env_config import EnvConfig

# Check current logging configuration
log_config = get_log_config()
env_config = EnvConfig.get_env_config()

print(f"Log level: {env_config.log_level}")
print(f"Log path: {env_config.log_path}")
print(f"Console enabled: {env_config.log_console_enabled}")
print(f"File enabled: {env_config.log_file_enabled}")
```

#### 2. Verify Component Context

```python
from awa.core.logger.logger import get_logger, LoggerComponent

logger = get_logger(LoggerComponent.API)

# Check if component context is properly set
import logging
for handler in logging.getLogger().handlers:
    print(f"Handler: {handler}")
    if hasattr(handler, 'component'):
        print(f"Component: {handler.component}")
```

#### 3. Test Workflow Context

```python
from awa.core.logger.workflow_context import workflow_context

# Check if workflow context is set
current_workflow = workflow_context.get()
print(f"Current workflow: {current_workflow}")
```

### Performance Considerations

#### Log Level Configuration

Configure appropriate log levels for production vs development:

```python
# Development: Verbose logging
LOG_LEVEL=DEBUG

# Production: Essential logs only
LOG_LEVEL=INFO

# High-traffic production: Minimal logging
LOG_LEVEL=WARNING
```

## Best Practices

### 1. Use Appropriate Log Levels

```python
logger.debug("Detailed debugging information")
logger.info("General information about program execution")
logger.warning("Something unexpected happened, but program continues")
logger.error("A serious error occurred")
logger.exception("An exception occurred")  # Automatically includes stack trace
```

### 2. Include Context in Log Messages

```python
# Good: Include relevant context
workflow.logger.info(f"Processing user {user_id} with {len(items)} items")
# Output: AWA-WORKFLOW | workflow-123 | Processing user user-456 with 3 items

# Less helpful: Vague message
workflow.logger.info("Processing user")
# Output: AWA-WORKFLOW | workflow-123 | Processing user
```

### 3. Initialize Logging Properly

Follow the two-step logging setup pattern:

```python
# Step 1: Initialize logging infrastructure (once per application)
init_logging()

# Step 2: Get component-specific loggers
logger = get_logger(LoggerComponent.CLI)

# For classes, store the logger as an instance variable
class MyService:
    def __init__(self):
        # Get a logger with appropriate component context
        self.logger = get_logger(LoggerComponent.API)

    def process(self):
        # Logger automatically includes AWA-API component context
        self.logger.info("Starting process")

    def handle_error(self):
        # Exception logging includes stack trace and component context
        try:
            risky_operation()
        except Exception:
            self.logger.exception("Operation failed")

# Examples for different components
api_service = get_logger(LoggerComponent.API)      # AWA-API
ui_component = get_logger(LoggerComponent.UI)      # AWA-UI
worker_service = get_logger(LoggerComponent.WORKER) # AWA-WORKER
server_component = get_logger(LoggerComponent.SERVER) # AWA-SERVER
auth_service = get_logger(LoggerComponent.AUTH)    # AWA-AUTH
# Note: HTTP component is automatically used by httpx/httpcore libraries
```

### 4. Handle Errors Gracefully

```python
try:
    result = await workflow.execute_activity(
        risky_activity,
        input_data,
        start_to_close_timeout=timedelta(seconds=30),
    )
except Exception:
    # Use exception() to automatically include stack trace
    workflow.logger.exception(f"Activity failed with input: {input_data}")
    raise
```
