<!-- This file is auto-generated. Do not edit manually. -->
<!-- Run 'make docs-prep' or 'python scripts/generate_cli_docs.py' to regenerate. -->

# AWA CLI Reference

**Usage**:

```console
$ awa [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `run`: Run the AWA Engine, API, and UI (including...
* `mcp`: Run the AWA MCP server.
* `api`: Start the AWA API server directly (useful...
* `docs`: Run the AWA docs.
* `ui`: Run the AWA UI in the specified mode.
* `start`: Start AWA services.
* `status`: Check the status of AWA services.
* `stop`: Stop AWA services.
* `stop-all`: Aggressively stop all AWA-related...
* `server`: Start the Temporal Server.
* `worker`: Start the Temporal Worker.
* `init`: Initialize AWA global configuration with...
* `workflows`: Access Workflow data with subcommands.
* `auth`

## `awa run`

Run the AWA Engine, API, and UI (including docs).

**Usage**:

```console
$ awa run [OPTIONS]
```

**Options**:

* `-w, --workflow TEXT`: Workflow to run
* `-i, --input TEXT`: Input for workflow (can be JSON string)
* `-q, --task-queue TEXT`: Task queue to use
* `--help`: Show this message and exit.

## `awa mcp`

Run the AWA MCP server.

**Usage**:

```console
$ awa mcp [OPTIONS]
```

**Options**:

* `-e, --env TEXT`: Optional .env path, overwriting any defaults or values from local
* `-c, --config TEXT`: Optional config.yaml path, overwriting any defaults or values from local
* `--help`: Show this message and exit.

## `awa api`

Start the AWA API server directly (useful for debugging).

**Usage**:

```console
$ awa api [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `awa docs`

Run the AWA docs.

**Usage**:

```console
$ awa docs [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `awa ui`

Run the AWA UI in the specified mode.

**Usage**:

```console
$ awa ui [OPTIONS]
```

**Options**:

* `-u, --ui [none|dev|prod]`: UI mode to use  [default: dev]
* `--help`: Show this message and exit.

## `awa start`

Start AWA services.

**Usage**:

```console
$ awa start [OPTIONS]
```

**Options**:

* `-u, --ui-mode [none|dev|prod]`: UI mode to use
* `-t, --terminate`: Terminate all workflows currently running
* `-d, --detach`: Start services and exit CLI (services continue running in background)
* `-s, --services TEXT`: Comma-delimited list of services to start. Available services: api, ui, temporal_server, temporal_worker
* `-e, --env TEXT`: Optional .env path, overwriting any defaults or values from local
* `-c, --config TEXT`: Optional config.yaml path, overwriting any defaults or values from local
* `--help`: Show this message and exit.

## `awa status`

Check the status of AWA services.

**Usage**:

```console
$ awa status [OPTIONS]
```

**Options**:

* `-s, --services TEXT`: Comma-delimited list of services to check. Available services: api, ui, temporal_server, temporal_worker
* `-q, --quiet`: Quiet mode - no output, only exit codes (for CI/automation)
* `--help`: Show this message and exit.

## `awa stop`

Stop AWA services.

**Usage**:

```console
$ awa stop [OPTIONS]
```

**Options**:

* `-s, --services TEXT`: Comma-delimited list of services to stop. Available services: api, ui, temporal_server, temporal_worker
* `--help`: Show this message and exit.

## `awa stop-all`

Aggressively stop all AWA-related processes including orphaned ones.

This command performs a comprehensive cleanup by:
1. Running normal stop operation first
2. Finding all orphaned AWA-related processes by pattern matching
3. Terminating discovered processes with proper signal handling
4. Cleaning up any remaining state files

Use this when &#x27;make stop&#x27; doesn&#x27;t clean up all processes after Ctrl+C.

**Usage**:

```console
$ awa stop-all [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `awa server`

Start the Temporal Server.

**Usage**:

```console
$ awa server [OPTIONS]
```

**Options**:

* `-r, --retries INTEGER`: Number of times to retry connections  [default: 3]
* `--help`: Show this message and exit.

## `awa worker`

Start the Temporal Worker.

**Usage**:

```console
$ awa worker [OPTIONS]
```

**Options**:

* `-r, --retries INTEGER`: Number of times to retry connections  [default: 3]
* `--help`: Show this message and exit.

## `awa init`

Initialize AWA global configuration with interactive setup.

**Usage**:

```console
$ awa init [OPTIONS]
```

**Options**:

* `-f, --force`: Force re-initialization even if config exists
* `--help`: Show this message and exit.

## `awa workflows`

Access Workflow data with subcommands.

**Usage**:

```console
$ awa workflows [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `runs`: List Temporal Workflow Runs.
* `list`: List all available workflows in the system.

### `awa workflows runs`

List Temporal Workflow Runs.

**Usage**:

```console
$ awa workflows runs [OPTIONS]
```

**Options**:

* `-j, --json`: Output in JSON format
* `--help`: Show this message and exit.

### `awa workflows list`

List all available workflows in the system.

**Usage**:

```console
$ awa workflows list [OPTIONS]
```

**Options**:

* `-j, --json`: Output in JSON format
* `--help`: Show this message and exit.

## `awa auth`

**Usage**:

```console
$ awa auth [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `login`: Login to a provider.
* `logout`: Logout from a provider.
* `status`: Show authentication status for all providers.

### `awa auth login`

Login to a provider. Supported providers: github-copilot.

**Usage**:

```console
$ awa auth login [OPTIONS] PROVIDER
```

**Arguments**:

* `PROVIDER`: [required]

**Options**:

* `--help`: Show this message and exit.

### `awa auth logout`

Logout from a provider.

**Usage**:

```console
$ awa auth logout [OPTIONS] PROVIDER
```

**Arguments**:

* `PROVIDER`: [required]

**Options**:

* `--help`: Show this message and exit.

### `awa auth status`

Show authentication status for all providers.

**Usage**:

```console
$ awa auth status [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
