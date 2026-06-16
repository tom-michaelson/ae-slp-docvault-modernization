# Debugging

## API Debugging

AWA provides a dedicated API debugging command that allows developers to debug API endpoints with breakpoints in VS Code or other debuggers.

### Debugging the API Only

To start the API server directly for debugging:

```bash
uv run -m awa.main api
```

This command starts the FastAPI server in the current process, making it debuggable with standard Python debuggers.

### Debugging the Entire Application

To debug the API while running the complete AWA stack (Temporal, Workers, UI), follow these steps:

#### 1. Start all services except the API

First, start the entire AWA application:

```bash
# Start everything except the API
uv run -m awa.main start --services temporal_server,temporal_worker,ui
```

Note: When starting services selectively, make sure Temporal is fully started before launching the API in debug mode.

#### 2. Launch API in Debug Mode

Now launch the API in debug mode using VS Code:

1. Open VS Code
2. Go to the **Run and Debug** panel (Ctrl/Cmd + Shift + D)
3. Select **"awa api"** from the configuration dropdown
4. Set breakpoints in your code
5. Press **F5** or click **Start Debugging**

The API will now run in debug mode and connect to the already-running Temporal server and other services.

#### 3. Verify the Setup

To verify everything is working correctly:

```bash
# Check that all services are now running
uv run -m awa.main status
```

Open the API docs in your browser (http://localhost:8001/docs) or hit an endpoint any other way, e.g.:

```
curl http://localhost:8001/api/v1/health/
```

Any breakpoints you've set in the API code in VS Code should now be hit.

### VS Code Debug Configuration

AWA includes a pre-configured VS Code launch configuration that automatically loads environment variables from a `.env` file in the workspace root:

```json
{
  "name": "awa api",
  "type": "debugpy",
  "request": "launch",
  "module": "awa.main",
  "args": ["api"],
  "console": "integratedTerminal",
  "env": {
    "PYDEVD_DISABLE_FILE_VALIDATION": "1"
  },
  "envFile": "${workspaceFolder}/.env"
}
```

**Note**: Make sure you have a `.env` file in your workspace root directory with your environment variables. The debugger will automatically load these variables when you start debugging.

### Troubleshooting

**Port Already in Use**

If you get an error that port 8001 is already in use, find and kill the process, e.g.:

```bash
lsof -ti:8001 | xargs kill -9
```

**API Can't Connect to Temporal**

If the API can't connect to Temporal:

1. Verify Temporal is running: `temporal operator cluster health`
2. Check the Temporal UI at http://localhost:8002
3. Ensure no firewall is blocking local connections
4. Check logs in the `logs/` directory

**Breakpoints Not Working**

If breakpoints aren't being hit:

- Ensure you're using the VS Code debug configuration, not running `awa api` directly
- Check that the code path actually reaches your breakpoint
