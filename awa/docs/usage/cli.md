# Components - CLI

The AWA CLI provides several commands for managing services, running workflows, and interacting with the system.

See [Reference - CLI](/reference/cli) for a complete list of commands.

## Starting Services

### All Services

To start all AWA services:

```bash
make start
```

or

```bash
uv run -m awa.main start
```

This command will:

- Start the Temporal server
- Start a Temporal worker
- Start the AWA API
- Start the AWA UI (including docs)
- Keep services running until explicitly stopped

#### UI Development

You can run the UI in development (hot reload) mode by using the `--ui` / `-u` flag with a value of `dev`.

```bash
uv run -m awa.main start --ui dev
```

#### Detached Mode

To start services in detached mode (services continue running in background after CLI exits):

```bash
uv run -m awa.main start --detach
```

or

```bash
uv run -m awa.main start -d
```

In detached mode:

- Services start and the CLI immediately exits
- Services continue running in the background
- Use the `stop` command to gracefully shut down detached services
- Service state is tracked for proper cleanup

You can combine detached mode with other options:

```bash
# Start in detached mode with production UI
uv run -m awa.main start --detach --ui-mode prod

# Start in detached mode with custom config
uv run -m awa.main start -d --config /path/to/config.yaml
```

## Stopping Services

### Detached Services

To stop services that were started in detached mode:

```bash
uv run -m awa.main stop
```

The `stop` command will:

- Find all services started in detached mode
- Gracefully shut down each service (SIGTERM)
- Force kill if graceful shutdown fails after timeout
- Clean up service state files
- Provide feedback on which services were stopped

Example output:

```
INFO     - Stopping AWA services...
INFO     - Found 4 service(s) to stop.
INFO     - Successfully stopped services: temporal_server, temporal_worker, api, ui
INFO     - Stop operation completed.
```

## Running Workflows

### Basic Workflow Execution

To run a workflow:

```bash
uv run -m awa.main run -w <workflow_name> -i <workflow_input>
```

<!--@include: /../.shared/windows-json-cli-quirk.md -->

Options:

- `-w, --workflow`: Name of the workflow to run
- `-i, --input`: Input for the workflow (can be JSON string)

Example:

```bash
uv run -m awa.main run -w awa-apply-single-file-diff -i '{"file_path": "examples/single_file_diff/sample.py", "natural_language_request": "Add a power method"}'
```

## MCP Server

<!--@include: /../.shared/running-mcp.md -->

To run the MCP server:

```bash
make mcp
```

## Documentation

To run the documentation server in development (hot reload) mode:

```bash
make docs
```

OR

```bash
uv run -m awa.main docs
```

## Service Management Details

### Service Dependencies

The AWA system consists of several interdependent services:

1. **Temporal Server**

   - Core workflow engine
   - Required for workflow execution
   - Runs on default port 7233

2. **Temporal Worker**

   - Executes workflows and activities
   - Depends on Temporal Server
   - Connects to server on port 7233

3. **API Server**

   - REST API for system interaction
   - Runs on port 8001
   - Provides endpoints for workflow management

4. **UI Server**

   - Web interface for system interaction
   - Runs on port 8000
   - Optional component
   - Includes documentation site

5. **Temporal UI**

   - Web interface for Temporal workflow management
   - Runs on port 8002
   - Provides workflow visualization and management

6. **Temporal Metrics**
   - Metrics endpoint for Temporal server
   - Runs on port 8004
   - Provides monitoring and observability data
   - Access metrics at `/metrics` endpoint (Prometheus format)

### Service Status

You can check service status through the API or by attempting to connect to the respective ports:

- AWA UI: `localhost:8000`
- AWA API Server: `localhost:8001`
- Temporal UI: `localhost:8002`
- Temporal Server: `localhost:7233`
