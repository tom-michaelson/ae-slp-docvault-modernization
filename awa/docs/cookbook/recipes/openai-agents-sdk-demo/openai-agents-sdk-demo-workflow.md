# OpenAI Agents SDK Demo Workflow

A simple Temporal workflow that demonstrates usage of the [official OpenAI Agents SDK Temporal integration](https://temporal.io/blog/announcing-openai-agents-sdk-integration) via the [AWA wrapper child workflow](/usage/features/openai-agents-sdk), leveraging agents-as-tools functionality by creating haiku poems through orchestrated AI agent collaboration.

## Overview

The `awa-openai-agents-sdk-demo` workflow showcases the powerful agents-as-tools pattern available in the OpenAI Agents SDK framework. This demonstration workflow creates beautiful haiku poems from any topic or Jira issue, coordinating multiple specialized AI agents working together as a cohesive system. It illustrates how complex workflows can be built by orchestrating specialized agents, each with distinct capabilities and responsibilities.

## How It Works

1. **Orchestrator Initialization**: The main orchestrator agent receives a topic and determines if it's a Jira issue ID or general topic
2. **Conditional Jira Integration**: If the topic appears to be a Jira issue ID (e.g., "ABC-123"), the orchestrator uses the Jira Operator agent-as-tool to fetch detailed issue information
3. **Haiku Creation**: The orchestrator leverages the Haiku Author agent-as-tool to create a traditional haiku (5-7-5 syllable structure) based on the topic or Jira issue details
4. **Handoff to Finisher**: The orchestrator hands off structured data (haiku content and optional Jira issue key) to the Finisher agent
5. **ASCII Art Formatting**: The Finisher agent formats the haiku into an attractive ASCII art presentation with borders and headers
6. **Result Return**: The complete formatted haiku is returned as the workflow output

## Key Features

- **Agents-as-Tools Architecture**: Demonstrates the OpenAI Agent framework's ability to use other agents as specialized tools within an orchestrator pattern
- **Jira Integration**: Seamlessly connects with Atlassian Jira through MCP (Model Context Protocol) server integration
- **Multi-Model Support**: Configurable to use different LLM providers (OpenAI GPT-4, AWS Bedrock Claude, etc.) via the LiteLLM SDK (within the OpenAI Agents SDK).
- **Intelligent Topic Detection**: Automatically recognizes Jira issue IDs and fetches relevant context for haiku creation
- **Traditional Haiku Structure**: Ensures proper 5-7-5 syllable pattern adherence in generated poems

## Architecture

### Orchestrator Pattern with Agents as Tools

The workflow implements a sophisticated orchestrator pattern where a central agent coordinates multiple specialized agents:

```
Orchestrator Agent
├── Agent Tool: Jira Operator (fetch_jira_details)
│   └── Fetches Jira issue details using Atlassian MCP server
├── Agent Tool: Haiku Author (create_haiku)
│   └── Creates traditional 5-7-5 syllable haiku poems
└── Handoff: Finisher Agent
    └── Formats haiku into ASCII art with borders and headers
```

### Agent Responsibilities

- **Orchestrator Agent**: Main coordinator that determines workflow flow and coordinates between specialized agents
- **Jira Operator Agent**: Specialized tool for fetching and summarizing Jira issue details through MCP server integration
- **Haiku Author Agent**: Poetry specialist focused on creating traditional haiku with proper syllable structure
- **Finisher Agent**: Formatting specialist that creates visually appealing ASCII art presentations

## Usage

### Input Parameters

The workflow requires a `OpenAIAgentsDemoInput` object with:

- `topic` (string): The subject for the haiku poem. Can be:
  - A Jira issue ID (e.g., "AWA-123", "PROJ-456")
  - Any general topic (e.g., "autumn leaves", "morning coffee", "software development")
  - Default: "autumn leaves"

### Output

Returns a beautifully formatted ASCII art haiku containing:

- **Header section**: Includes Jira issue key if applicable
- **Haiku poem**: Traditional 5-7-5 syllable structure
- **Decorative borders**: ASCII art presentation with visual appeal

### Example Output

```
╔══════════════════════════════════╗
║          AWA-123 Haiku           ║
╠══════════════════════════════════╣
║                                  ║
║     Code flows like water        ║
║   Through digital pathways deep  ║
║     Innovation blooms            ║
║                                  ║
╚══════════════════════════════════╝
```

## Command Line Execution

You can execute the workflow directly using the UV command:

```bash
# Create a haiku about a general topic
uv run -m awa.main run -w "awa-openai-agents-sdk-demo" -i '{
  "topic": "spring morning"
}'
```

```bash
# Create a haiku from a Jira issue (automatically fetches issue details)
uv run -m awa.main run -w "awa-openai-agents-sdk-demo" -i '{
  "topic": "AWA-123"
}'
```
