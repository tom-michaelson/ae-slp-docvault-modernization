# Recipe Configuration

AWA includes a collection of example workflows and tutorials (recipes) that can be enabled through configuration. This guide explains how to enable and use recipes in your AWA installation.

## Enabling Recipes

To enable recipes in AWA, set the `recipes` field to `true` in your `config.yaml` file:

```yaml
recipes: true
```

By default, recipes are **disabled** (`recipes: false`). When recipes are enabled, AWA automatically:

1. Registers recipe workflows with Temporal
2. Makes recipe workflows available through the API
3. Exposes recipe workflows through the MCP server
4. Loads recipe workflows into the unified worker (same worker as core workflows, using the default task queue)

## Configuration Examples

### Minimal Configuration with Recipes

```yaml
# config.yaml
recipes: true
```

### Full Configuration Example

```yaml
# config.yaml
recipes: true

temporal:
  namespace: default
  server_url: localhost:7233
# Other configuration settings...
```

## What Happens When Recipes Are Enabled

When you set `recipes: true`, AWA performs the following actions:

### 1. Workflow Registration

All recipe workflows are automatically discovered and registered with Temporal. This includes:

- Tutorial workflows (AWA 101, AWA 201, etc.)
- Sample workflows demonstrating MCP tools
- PR description and code analysis workflows
- Test automation workflows
- And more

### 2. API Registration

Recipe workflows become available through AWA's REST API at:

```
GET /v1/workflows
```

You can see all available workflows, including recipes, in the API documentation at `http://localhost:8001/docs`.

### 3. MCP Integration

Recipe workflows are exposed through AWA's Model Context Protocol (MCP) server, making them accessible to AI coding assistants like Claude Desktop.

### 4. Worker Configuration

Recipe workflows are loaded into the same unified worker as core workflows. The worker uses the default task queue (`awa_default`) for both core and recipe workflows.

## Verifying Recipes Are Enabled

You can verify that recipes are enabled in several ways:

### Check Service Status

```bash
uv run -m awa.main status
```

If recipes are enabled, you should see the worker service running with both core and recipe workflows loaded.

### Check Logs

When starting AWA with recipes enabled, you should see log entries indicating recipe workflows have been registered:

```
INFO - Recipe workflows registered: X workflows found
INFO - Worker started with X total workflows (core + recipes)
```

### Query Available Workflows via API

```bash
curl http://localhost:8001/v1/workflows | jq
```

Recipe workflows will be included in the response alongside core workflows.

### Check MCP Server

If you have the AWA MCP server configured in your AI coding assistant, recipe workflows will appear as available tools.

## Running Recipe Workflows

Once recipes are enabled, you can run them using the AWA CLI:

```bash
uv run -m awa.main run -w <workflow-name>
```

For example, to run the AWA 101 tutorial workflow:

```bash
uv run -m awa.main run -w "awa-101-simple-direct-transform"
```

Recipe workflows use the same default task queue as core workflows, so there's no need to specify a task queue when running them.

## Disabling Recipes

To disable recipes, set `recipes: false` in your `config.yaml` or omit the field entirely (default is `false`):

```yaml
# config.yaml
recipes: false
# or simply omit the recipes field
```

When recipes are disabled:

- Recipe workflows are not registered with the worker
- Recipe workflows are not available via API or MCP
- Recipe workflows cannot be executed

## Common Use Cases

### Development and Learning

Enable recipes when:

- Learning how to build workflows with AWA
- Following AWA tutorials
- Exploring example implementations
- Testing AWA functionality

### Production Deployments

Disable recipes when:

- Deploying to production environments
- Running only custom workflows
- Minimizing resource usage
- Reducing attack surface

## Troubleshooting

### Recipes Not Running

If recipe workflows are not running:

1. **Check configuration**: Verify `recipes: true` in `config.yaml`
2. **Check worker status**: Run `uv run -m awa.main status` to verify the worker is running
3. **Check logs**: Review logs for recipe workflow registration errors
4. **Restart services**: After changing `recipes` setting, restart AWA services

### Recipes Not Loading

If recipes are not loading into the worker:

1. **Verify dependencies**: Ensure all recipe dependencies are installed
2. **Check Temporal connection**: Verify AWA can connect to Temporal server
3. **Review configuration**: Check for configuration errors in `config.yaml`
4. **Check logs**: Look for error messages during worker startup

### Workflows Not Appearing in API

If recipe workflows don't appear in the API:

1. **Restart AWA**: After changing `recipes` setting, restart all AWA services
2. **Check API health**: Verify API is running at `http://localhost:8001/health`
3. **Review logs**: Look for workflow registration errors

## Additional Resources

- [Running Recipes Guide](/cookbook/#running-tutorials-and-recipes)
- [AWA 101 Tutorial](/cookbook/tutorials/awa-101/)
- [AWA 201 Tutorial](/cookbook/tutorials/awa-201/)
- [Configuration Reference](/reference/configuration/application)
