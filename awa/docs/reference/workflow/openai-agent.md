# `awa-openai-agent`

Workflow for executing OpenAI agents with AWA model configuration resolution and MCP server support.

This workflow integrates the OpenAI Agents SDK with AWA's configuration system, allowing agents to use AWA-configured models (OpenAI, Azure OpenAI, LiteLLM, Anthropic, Google Vertex, AWS Bedrock, GitHub Copilot) while supporting MCP (Model Context Protocol) servers and structured outputs. The workflow implements the Temporal Runner pattern for durable agent execution.

## Parameters

| Name           | Type                | Description                                                                               |
| :------------- | :------------------ | :---------------------------------------------------------------------------------------- |
| `agent_config` | `OpenAIAgentConfig` | Configuration object containing agent settings, model reference, and execution parameters |

### OpenAIAgentConfig Fields

| Name              | Type                                                                         | Description                                                                                 |
| :---------------- | :--------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------ |
| `name`            | `str`                                                                        | Name identifier for the agent                                                               |
| `instructions`    | `str`                                                                        | System instructions that define the agent's behavior and capabilities                       |
| `model`           | `str`                                                                        | LiteLLM model name                                                                          |
| `mcp_servers`     | `List[Union[StdioMCPConfig, SSEMCPConfig, StreamableHttpMCPConfig]] \| None` | Optional list of MCP server configurations for extended agent capabilities                  |
| `timeout_seconds` | `int`                                                                        | Maximum execution time in seconds (default: 300, min: 1, max: 3600)                         |
| `response_format` | `ResponseFormat`                                                             | Output format: TEXT (default) or JSON_SCHEMA for structured responses                       |
| `response_schema` | `Dict[str, Any] \| None`                                                     | JSON schema for validating structured output (required when response_format is JSON_SCHEMA) |
| `workflow_id`     | `str \| None`                                                                | Optional Temporal workflow ID for tracking and correlation                                  |
| `metadata`        | `Dict[str, Any] \| None`                                                     | Additional metadata to attach to the agent execution                                        |
| `agent_tools`     | `List[Union[OpenAIAgentConfig, AgentToolConfig]] \| None`                   | Optional list of agents to expose as tools for orchestration patterns                      |
| `handoffs`        | `List[Union[str, HandoffConfig, OpenAIAgentConfig]] \| None`                | Optional list of handoff configurations for agent delegation                                |

### Agent Tools Configuration

AWA supports using agents as tools within other agents through the `agent_tools` field. This enables orchestration patterns where a coordinator agent calls specialized sub-agents while maintaining control flow.

#### AgentToolConfig Fields

| Name                        | Type                                           | Description                                                                         |
| :-------------------------- | :--------------------------------------------- | :---------------------------------------------------------------------------------- |
| `target_agent`              | `OpenAIAgentConfig \| Agent`                   | The agent configuration or instance to expose as a tool                            |
| `tool_name_override`        | `str \| None`                                  | Override the tool name (if not provided, uses agent name)                          |
| `tool_description_override` | `str \| None`                                  | Override the tool description for better context                                    |
| `is_enabled`                | `bool`                                         | Whether this agent tool is enabled (default: True)                                 |

### Handoff Configuration

AWA supports agent handoffs through the `handoffs` field, enabling one agent to delegate control to specialized sub-agents. Handoffs provide a mechanism for sequential agent execution where control transfers from the coordinating agent to the target agent.

#### HandoffConfig Fields

| Name                        | Type                                           | Description                                                                         |
| :-------------------------- | :--------------------------------------------- | :---------------------------------------------------------------------------------- |
| `target_agent`              | `str \| OpenAIAgentConfig \| Agent`            | The agent to hand off control to (by name, config, or instance)                    |
| `tool_name_override`        | `str \| None`                                  | Override the handoff tool name (if not provided, uses target agent name)           |
| `tool_description_override` | `str \| None`                                  | Override the handoff tool description for better context                            |
| `input_type`                | `Dict[str, Any] \| None`                       | JSON schema defining the expected input structure for typed handoffs               |
| `is_enabled`                | `bool`                                         | Whether this handoff is enabled (default: True)                                    |

#### input_type Field

The `input_type` field in HandoffConfig accepts a JSON schema that defines the expected structure of input data when handing off control to another agent. This provides:

- **Type Safety**: Automatic validation of handoff inputs against the defined schema
- **Clear Interfaces**: Explicit definition of what data the target agent expects
- **Error Prevention**: Early validation prevents runtime errors from malformed inputs
- **Documentation**: Schema serves as self-documenting interface specification

**Supported JSON Schema Features:**
- Basic types: `string`, `integer`, `number`, `boolean`, `array`, `object`
- Nested objects and arrays
- Required field validation
- Property descriptions
- Constraints (minimum, maximum, enum, pattern, etc.)
- Array item specifications

**Implementation Details:**
- The JSON schema is converted to a Python type for SDK integration
- A no-op callback function is used internally to satisfy SDK requirements
- Input validation occurs automatically when the handoff is invoked
- Validation failures result in clear error messages to the coordinating agent

### MCP Server Configuration Types

#### StdioMCPConfig

| Name        | Type                     | Description                                       |
| :---------- | :----------------------- | :------------------------------------------------ |
| `transport` | `MCPServerTransport`     | Always set to STDIO for subprocess-based servers  |
| `command`   | `str`                    | Command to execute for the MCP server             |
| `args`      | `List[str] \| None`      | Command line arguments for the server             |
| `env`       | `Dict[str, str] \| None` | Environment variables for the subprocess          |
| `cwd`       | `str \| None`            | Working directory for the subprocess              |
| `enabled`   | `bool`                   | Whether this MCP server is active (default: True) |

#### SSEMCPConfig

| Name              | Type                     | Description                                       |
| :---------------- | :----------------------- | :------------------------------------------------ |
| `transport`       | `MCPServerTransport`     | Always set to SSE for Server-Sent Events servers  |
| `url`             | `str`                    | SSE endpoint URL                                  |
| `headers`         | `Dict[str, str] \| None` | HTTP headers for authentication and configuration |
| `timeout_seconds` | `int \| None`            | Connection timeout in seconds (default: 30)       |
| `enabled`         | `bool`                   | Whether this MCP server is active (default: True) |

#### StreamableHttpMCPConfig

| Name              | Type                     | Description                                              |
| :---------------- | :----------------------- | :------------------------------------------------------- |
| `transport`       | `MCPServerTransport`     | Always set to STREAMABLE_HTTP for streaming HTTP servers |
| `endpoint`        | `str`                    | HTTP endpoint URL                                        |
| `method`          | `str`                    | HTTP method to use (default: "POST")                     |
| `headers`         | `Dict[str, str] \| None` | HTTP headers for authentication and configuration        |
| `timeout_seconds` | `int \| None`            | Request timeout in seconds (default: 30)                 |
| `enabled`         | `bool`                   | Whether this MCP server is active (default: True)        |

## Returns

| Type                  | Description                                                                                |
| :-------------------- | :----------------------------------------------------------------------------------------- |
| `OpenAIAgentResponse` | Response object containing the agent's output, execution metadata, and performance metrics |

### OpenAIAgentResponse Fields

| Name                     | Type                     | Description                                                 |
| :----------------------- | :----------------------- | :---------------------------------------------------------- |
| `content`                | `str`                    | The agent's response content (text or JSON string)          |
| `execution_id`           | `str`                    | Unique identifier for this execution (UUID format)          |
| `agent_name`             | `str`                    | Name of the agent that executed                             |
| `model_used`             | `str`                    | The actual model that was used for execution                |
| `execution_time_seconds` | `float`                  | Total time taken for the agent execution                    |
| `error`                  | `str \| None`            | Error message if the execution failed                       |
| `error_type`             | `str \| None`            | Type of error that occurred (e.g., ValueError, ImportError) |
| `metadata`               | `Dict[str, Any] \| None` | Additional metadata from the execution                      |
| `agent_tool_events`      | `List[AgentToolEvent] \| None` | List of agent tool invocations that occurred during execution |
| `handoff_events`         | `List[HandoffEvent] \| None` | List of handoff events that occurred during execution        |

### Agent Tool Events

When an agent uses other agents as tools, each tool invocation is recorded as an `AgentToolEvent`:

| Name            | Type     | Description                                                 |
| :-------------- | :------- | :---------------------------------------------------------- |
| `tool_name`     | `str`    | Name of the tool that was called                           |
| `target_agent`  | `str`    | Name of the agent that was invoked as a tool               |
| `timestamp`     | `float`  | Unix timestamp when the tool was called                    |
| `duration_ms`   | `int`    | Duration of the tool execution in milliseconds             |
| `success`       | `bool`   | Whether the tool execution was successful                   |
| `error`         | `str \| None` | Error message if the tool execution failed              |

## Runner Pattern Implementation

This workflow implements the Temporal Runner pattern from the `temporalio.contrib.openai_agents` module, which provides:

1. **Durable Execution**: Agent runs are durable and can be replayed if interrupted
2. **Timeout Management**: Configurable timeouts with proper cleanup
3. **State Management**: Agent state is managed by Temporal's workflow engine
4. **Error Recovery**: Automatic retry and error handling capabilities

The Runner pattern executes within a Temporal workflow sandbox environment, ensuring deterministic execution while allowing for external API calls through the OpenAI Agents SDK.

## Model Configuration Resolution

The workflow automatically resolves AWA model references to provider-specific configurations:

### Supported Providers

| Provider       | Configuration Source           | Notes                                             |
| :------------- | :----------------------------- | :------------------------------------------------ |
| OpenAI         | `llm.providers.openai`         | Direct OpenAI API integration                     |
| Azure OpenAI   | `llm.providers.azure_openai`   | Supports both API key and Entra ID authentication |
| LiteLLM        | `llm.providers.lite_llm`       | Unified interface for multiple providers          |
| Anthropic      | `llm.providers.anthropic`      | Claude models via LiteLLM bridge                  |
| Google Vertex  | `llm.providers.google_vertex`  | Gemini models with project/location configuration |
| AWS Bedrock    | Provider auto-configured       | AWS credentials from environment                  |
| GitHub Copilot | `llm.providers.github_copilot` | GitHub Copilot integration                        |

### Model Resolution Process

1. Agent references a model by name (e.g., `"my-gpt-4"`)
2. Workflow loads the model configuration from AWA's `config.yaml`
3. Provider-specific settings are extracted and formatted
4. Appropriate client (OpenAI, Azure, or LiteLLM) is configured
5. Model parameters (temperature, max_tokens) are applied

## Error Handling

The workflow implements comprehensive error handling for various failure scenarios:

### Error Types

| Error Type     | Cause                                           | Response                                              |
| :------------- | :---------------------------------------------- | :---------------------------------------------------- |
| `ImportError`  | OpenAI Agents SDK not installed                 | Returns error response with installation instructions |
| `ValueError`   | Invalid configuration or parameters             | Returns error response with validation details        |
| `TimeoutError` | Agent execution exceeds timeout_seconds         | Terminates execution and returns partial results      |
| `RuntimeError` | Provider configuration or authentication issues | Returns error response with provider-specific details |

### Error Response Format

When an error occurs, the workflow returns an `OpenAIAgentResponse` with:

- Empty `content` field
- Populated `error` and `error_type` fields
- `execution_time_seconds` showing time until failure
- Original `metadata` preserved for debugging

## Timeout Configuration

Timeouts are enforced at multiple levels:

1. **Workflow Level**: Overall workflow timeout (default: unlimited)
2. **Agent Level**: Configured via `timeout_seconds` parameter (1-3600 seconds)
3. **MCP Server Level**: Individual server connection timeouts
4. **Provider Level**: API call timeouts based on provider configuration

The workflow uses Temporal's activity timeout semantics to ensure proper cleanup when timeouts occur.

## Structured Output Support

For JSON schema validation, the workflow:

1. Sets the agent's response format to JSON mode
2. Appends schema instructions to the agent's system prompt
3. The agent is instructed to conform to the provided JSON schema
4. Response content is returned as a JSON string (parsing is left to the caller)

## Usage

The following examples show how to start the `awa-openai-agent` workflow as a child workflow.

::: code-group

```python [Python]
from awa.sdk.models.openai_agents import (
    OpenAIAgentConfig,
    ResponseFormat,
    StdioMCPConfig,
    SSEMCPConfig
)

# Basic agent configuration
agent_config = OpenAIAgentConfig(
    name="code-reviewer",
    instructions="You are a helpful code review assistant",
    model="openai/gpt-4.1",
    timeout_seconds=600
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "awa-openai-agent",
    agent_config
)

print(result.content)  # Agent's response
print(f"Execution took {result.execution_time_seconds:.2f} seconds")

# With MCP servers and structured output
agent_config = OpenAIAgentConfig(
    name="data-extractor",
    instructions="Extract entities from the provided text",
    model="openai/gpt-5",
    mcp_servers=[
        StdioMCPConfig(
            command="mcp-server-filesystem",
            args=["--root", "/workspace"]
        ),
        SSEMCPConfig(
            url="https://api.example.com/mcp/sse",
            headers={"Authorization": "Bearer token"}
        )
    ],
    response_format=ResponseFormat.JSON_SCHEMA,
    response_schema={
        "type": "object",
        "properties": {
            "entities": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"}
        },
        "required": ["entities", "summary"]
    }
)

result = await workflow.execute_child_workflow(
    "awa-openai-agent",
    agent_config
)

# Parse the JSON response
import json
data = json.loads(result.content)
print(f"Found {len(data['entities'])} entities")

# Agent Tools Example - Orchestration Pattern
from awa.sdk.models.openai_agents import AgentToolConfig

# Define specialized agents
file_analyzer = OpenAIAgentConfig(
    name="FileAnalyzer",
    instructions="Analyze file contents and extract key information",
    model="openai/gpt-4o",
    mcp_servers=["filesystem"]
)

report_generator = OpenAIAgentConfig(
    name="ReportGenerator",
    instructions="Generate professional reports from analysis data",
    model="openai/gpt-4o",
    mcp_servers=["filesystem"]
)

# Orchestrator agent using other agents as tools
orchestrator_config = OpenAIAgentConfig(
    name="DataOrchestrator",
    instructions="""You coordinate data analysis workflows.

    Use analyze_files tool to analyze data files, then use
    generate_report tool to create professional reports.

    Always analyze first, then generate a comprehensive report.""",
    model="openai/gpt-4o",
    agent_tools=[
        AgentToolConfig(
            target_agent=file_analyzer,
            tool_name_override="analyze_files",
            tool_description_override="Analyze data files and extract insights"
        ),
        AgentToolConfig(
            target_agent=report_generator,
            tool_name_override="generate_report",
            tool_description_override="Generate professional reports from analysis"
        )
    ]
)

# Execute orchestrator with agent tools
result = await workflow.execute_child_workflow(
    "awa-openai-agent",
    orchestrator_config
)

print(result.content)  # Final orchestrated result
print(f"Agent tools used: {len(result.agent_tool_events) if result.agent_tool_events else 0}")

# Handoff Configuration with input_type Example
from awa.sdk.models.openai_agents import HandoffConfig

# Define a handoff with typed input schema
handoff_config = OpenAIAgentConfig(
    name="task-coordinator",
    instructions="You coordinate tasks and delegate to specialized agents with structured inputs",
    model="openai/gpt-4o",
    handoffs=[
        HandoffConfig(
            target_agent="data_processor",
            tool_name_override="process_data",
            tool_description_override="Process data with specific parameters and return results",
            input_type={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["analyze", "transform", "validate"],
                        "description": "Type of data processing operation"
                    },
                    "dataset": {
                        "type": "string",
                        "description": "Path or identifier of the dataset to process"
                    },
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "threshold": {"type": "number", "minimum": 0, "maximum": 1},
                            "algorithm": {"type": "string", "enum": ["linear", "polynomial", "neural"]}
                        },
                        "required": ["threshold"]
                    }
                },
                "required": ["operation", "dataset", "parameters"]
            }
        )
    ]
)

# Execute handoff configuration
result = await workflow.execute_child_workflow(
    "awa-openai-agent",
    handoff_config
)

print(result.content)  # Result from handoff execution
print(f"Handoffs executed: {len(result.handoff_events) if result.handoff_events else 0}")
```

```typescript [TypeScript]
import { executeChild } from "@temporalio/workflow";

// Basic agent configuration
const agentConfig = {
  name: "code-reviewer",
  instructions: "You are a helpful code review assistant",
  model: "openai/gpt-4.1",
  timeout_seconds: 600,
};

// Execute the child workflow and wait for completion
const result = await executeChild("awa-openai-agent", {
  args: [agentConfig],
});

console.log(result.content); // Agent's response
console.log(
  `Execution took ${result.execution_time_seconds.toFixed(2)} seconds`
);

// With MCP servers and structured output
const agentConfigWithMCP = {
  name: "data-extractor",
  instructions: "Extract entities from the provided text",
  model: "openai/gpt-4.1",
  mcp_servers: [
    {
      transport: "STDIO",
      command: "mcp-server-filesystem",
      args: ["--root", "/workspace"],
    },
    {
      transport: "SSE",
      url: "https://api.example.com/mcp/sse",
      headers: { Authorization: "Bearer token" },
    },
  ],
  response_format: "JSON_SCHEMA",
  response_schema: {
    type: "object",
    properties: {
      entities: { type: "array", items: { type: "string" } },
      summary: { type: "string" },
    },
    required: ["entities", "summary"],
  },
};

const result = await executeChild("awa-openai-agent", {
  args: [agentConfigWithMCP],
});

// Parse the JSON response
const data = JSON.parse(result.content);
console.log(`Found ${data.entities.length} entities`);
```

```csharp [.NET]
using Temporalio.Workflows;

// Basic agent configuration
var agentConfig = new OpenAIAgentConfig
{
    Name = "code-reviewer",
    Instructions = "You are a helpful code review assistant",
    ModelName = "my-gpt-4", // References model in config.yaml
    TimeoutSeconds = 600
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync("awa-openai-agent", agentConfig);

Console.WriteLine(result.Content); // Agent's response
Console.WriteLine($"Execution took {result.ExecutionTimeSeconds:F2} seconds");

// With MCP servers and structured output
var agentConfigWithMCP = new OpenAIAgentConfig
{
    Name = "data-extractor",
    Instructions = "Extract entities from the provided text",
    ModelName = "my-claude-3.5",
    McpServers = new List<IMCPConfig>
    {
        new StdioMCPConfig
        {
            Command = "mcp-server-filesystem",
            Args = new[] { "--root", "/workspace" }
        },
        new SSEMCPConfig
        {
            Url = "https://api.example.com/mcp/sse",
            Headers = new Dictionary<string, string>
            {
                { "Authorization", "Bearer token" }
            }
        }
    },
    ResponseFormat = ResponseFormat.JSON_SCHEMA,
    ResponseSchema = new Dictionary<string, object>
    {
        ["type"] = "object",
        ["properties"] = new Dictionary<string, object>
        {
            ["entities"] = new Dictionary<string, object>
            {
                ["type"] = "array",
                ["items"] = new Dictionary<string, string> { ["type"] = "string" }
            },
            ["summary"] = new Dictionary<string, string> { ["type"] = "string" }
        },
        ["required"] = new[] { "entities", "summary" }
    }
};

var result = await Workflow.ExecuteChildAsync("awa-openai-agent", agentConfigWithMCP);

// Parse the JSON response
var data = JsonSerializer.Deserialize<Dictionary<string, object>>(result.Content);
Console.WriteLine($"Found {((JsonElement)data["entities"]).GetArrayLength()} entities");
```

```java [Java]
import io.temporal.workflow.Workflow;

// Basic agent configuration
OpenAIAgentConfig agentConfig = new OpenAIAgentConfig.Builder()
    .setName("code-reviewer")
    .setInstructions("You are a helpful code review assistant")
    .setModelName("my-gpt-4") // References model in config.yaml
    .setTimeoutSeconds(600)
    .build();

// Execute the child workflow and wait for completion
OpenAIAgentResponse result = Workflow.executeChildWorkflow(
    "awa-openai-agent",
    agentConfig
);

System.out.println(result.getContent()); // Agent's response
System.out.printf("Execution took %.2f seconds%n", result.getExecutionTimeSeconds());

// With MCP servers and structured output
OpenAIAgentConfig agentConfigWithMCP = new OpenAIAgentConfig.Builder()
    .setName("data-extractor")
    .setInstructions("Extract entities from the provided text")
    .setModelName("my-claude-3.5")
    .setMcpServers(Arrays.asList(
        new StdioMCPConfig.Builder()
            .setCommand("mcp-server-filesystem")
            .setArgs(Arrays.asList("--root", "/workspace"))
            .build(),
        new SSEMCPConfig.Builder()
            .setUrl("https://api.example.com/mcp/sse")
            .setHeaders(Map.of("Authorization", "Bearer token"))
            .build()
    ))
    .setResponseFormat(ResponseFormat.JSON_SCHEMA)
    .setResponseSchema(Map.of(
        "type", "object",
        "properties", Map.of(
            "entities", Map.of("type", "array", "items", Map.of("type", "string")),
            "summary", Map.of("type", "string")
        ),
        "required", Arrays.asList("entities", "summary")
    ))
    .build();

OpenAIAgentResponse result = Workflow.executeChildWorkflow(
    "awa-openai-agent",
    agentConfigWithMCP
);

// Parse the JSON response
ObjectMapper mapper = new ObjectMapper();
Map<String, Object> data = mapper.readValue(result.getContent(), Map.class);
List<String> entities = (List<String>) data.get("entities");
System.out.printf("Found %d entities%n", entities.size());
```

```go [Go]
import (
    "go.temporal.io/sdk/workflow"
    "encoding/json"
    "fmt"
)

// Basic agent configuration
agentConfig := OpenAIAgentConfig{
    Name:           "code-reviewer",
    Instructions:   "You are a helpful code review assistant",
    ModelName:      "my-gpt-4", // References model in config.yaml
    TimeoutSeconds: 600,
}

// Execute the child workflow and wait for completion
var result OpenAIAgentResponse
err := workflow.ExecuteChildWorkflow(ctx, "awa-openai-agent", agentConfig).Get(ctx, &result)
if err != nil {
    return err
}

fmt.Println(result.Content) // Agent's response
fmt.Printf("Execution took %.2f seconds\n", result.ExecutionTimeSeconds)

// With MCP servers and structured output
agentConfigWithMCP := OpenAIAgentConfig{
    Name:         "data-extractor",
    Instructions: "Extract entities from the provided text",
    ModelName:    "my-claude-3.5",
    MCPServers: []interface{}{
        StdioMCPConfig{
            Transport: "STDIO",
            Command:   "mcp-server-filesystem",
            Args:      []string{"--root", "/workspace"},
        },
        SSEMCPConfig{
            Transport: "SSE",
            URL:       "https://api.example.com/mcp/sse",
            Headers:   map[string]string{"Authorization": "Bearer token"},
        },
    },
    ResponseFormat: "JSON_SCHEMA",
    ResponseSchema: map[string]interface{}{
        "type": "object",
        "properties": map[string]interface{}{
            "entities": map[string]interface{}{
                "type":  "array",
                "items": map[string]string{"type": "string"},
            },
            "summary": map[string]string{"type": "string"},
        },
        "required": []string{"entities", "summary"},
    },
}

err = workflow.ExecuteChildWorkflow(ctx, "awa-openai-agent", agentConfigWithMCP).Get(ctx, &result)
if err != nil {
    return err
}

// Parse the JSON response
var data map[string]interface{}
err = json.Unmarshal([]byte(result.Content), &data)
if err != nil {
    return err
}
entities := data["entities"].([]interface{})
fmt.Printf("Found %d entities\n", len(entities))
```

```php [PHP]
use Temporal\Workflow;

// Basic agent configuration
$agentConfig = [
    'name' => 'code-reviewer',
    'instructions' => 'You are a helpful code review assistant',
    'model' => 'openai/gpt-4.1',
    'timeout_seconds' => 600
];

// Execute the child workflow and wait for completion
$result = yield Workflow::executeChildWorkflow(
    'awa-openai-agent',
    [$agentConfig]
);

echo $result['content']; // Agent's response
echo sprintf("Execution took %.2f seconds\n", $result['execution_time_seconds']);

// With MCP servers and structured output
$agentConfigWithMCP = [
    'name' => 'data-extractor',
    'instructions' => 'Extract entities from the provided text',
    'model' => 'openai/gpt-4.1',
    'mcp_servers' => [
        [
            'transport' => 'STDIO',
            'command' => 'mcp-server-filesystem',
            'args' => ['--root', '/workspace']
        ],
        [
            'transport' => 'SSE',
            'url' => 'https://api.example.com/mcp/sse',
            'headers' => ['Authorization' => 'Bearer token']
        ]
    ],
    'response_format' => 'JSON_SCHEMA',
    'response_schema' => [
        'type' => 'object',
        'properties' => [
            'entities' => ['type' => 'array', 'items' => ['type' => 'string']],
            'summary' => ['type' => 'string']
        ],
        'required' => ['entities', 'summary']
    ]
];

$result = yield Workflow::executeChildWorkflow(
    'awa-openai-agent',
    [$agentConfigWithMCP]
);

// Parse the JSON response
$data = json_decode($result['content'], true);
echo sprintf("Found %d entities\n", count($data['entities']));
```

:::

## Technical Implementation Details

### Workflow Execution Flow

1. **Configuration Loading**: The workflow loads AWA's application configuration from `config.yaml`
2. **Model Resolution**: The referenced model name is resolved to a complete model configuration
3. **Provider Detection**: The appropriate provider (OpenAI, Azure, LiteLLM, etc.) is determined
4. **Client Setup**: Provider-specific client is initialized with authentication and endpoints
5. **Agent Creation**: OpenAI Agent is instantiated with instructions and model settings
6. **MCP Setup**: MCP servers are configured if provided (placeholder for future implementation)
7. **Runner Execution**: The agent is executed using Temporal's Runner pattern with timeout
8. **Response Processing**: Results are packaged into the response model with metadata

### Provider-Specific Configurations

Each provider requires specific configuration handling:

- **OpenAI**: Direct API key authentication
- **Azure OpenAI**: Supports both API key and Entra ID authentication, requires deployment name mapping
- **LiteLLM**: Acts as a proxy, requires base URL and model prefixing (e.g., "vertex_ai/gemini-pro")
- **Anthropic**: Uses LiteLLM bridge with optional base URL override
- **Google Vertex**: Requires project ID, location, and optional credentials path
- **AWS Bedrock**: Uses AWS credentials from environment, model prefixed with "bedrock/"
- **GitHub Copilot**: Requires base URL and API key configuration

### Security Considerations

- API keys and sensitive credentials are never logged
- MCP server connections are validated before use
- Timeout enforcement prevents resource exhaustion
- Error messages sanitize sensitive information
- Metadata is preserved but not executed

### Performance Optimization

- Model configurations are cached during workflow execution
- Client connections are reused within the same workflow
- MCP servers maintain persistent connections when possible
- Token usage is tracked for cost monitoring
- Execution time is measured for performance analysis

## Limitations and Future Enhancements

### Current Limitations

- MCP server integration is a placeholder pending full implementation
- Response schema validation occurs in the agent, not post-processing
- No support for streaming responses
- No function calling or tool use support
- No session management or conversation history
- No built-in guardrails or content filtering

### Planned Enhancements

- Full MCP server integration with all transport types
- Response streaming for long-running generations
- Function calling and activity_as_tool support
- Session management for multi-turn conversations
- Guardrails integration for content safety
- Tracing and observability improvements
- REPL utility for interactive development
