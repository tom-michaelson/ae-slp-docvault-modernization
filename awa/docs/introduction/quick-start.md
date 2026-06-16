# Quick Start

Use this guide to get up and running quickly with AWA.

## 1. Install AWA

Follow the instructions for your platform:

- [Mac & Linux](/installation/mac-linux)
- [Windows](/installation/windows)
- [Docker](/installation/docker)

## 2. Run AWA

### Start the AWA services

The following command starts all AWA services, including the API, UI (including docs), Temporal Server, and Temporal Worker.

```bash
make start
```

OR

```bash
uv run -m awa.main start
```

### Run Workflows Directly

The following commands will initiate the provided workflow with the given parameter (optional).

:::warning Start, then Run
You must run the `start` command above before attempting to run workflows.
:::

<!--@include: /../.shared/windows-json-cli-quirk.md -->

#### Example 1

```bash
uv run -m awa.main run -w awa-hello-world -i '{"name": "World"}'
```

#### Example 2

:::warning LLM Providers

Before running the `awa-transform-file` workflow below, ensure you have at least one LLM provider configured in `config.yaml`.

:::

```bash
uv run -m awa.main run -w awa-transform-file -i '{"input_path": "request.json", "output_path": "output/poem.txt"}'
```

### Run AWA MCP Server

<!--@include: /../.shared/mcp-usage.md -->

### Stop the AWA services

You can stop all AWA services with the following command:

```bash
make stop
```

OR

```bash
uv run -m awa.main stop
```

## Recipes

You are up and running now. One place you can go next to continue exploring is our [Cookbook](/cookbook/).
