# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Awa.Client SDK is a .NET client library for Agentic Workflow Accelerator (AWA) services and APIs. It provides workflow utilities, models, and constants for building Temporal-based workflows with agent execution capabilities.

## Development Commands

### Building and Testing

- `dotnet clean -c Release` - Clean previous builds
- `dotnet restore` - Restore NuGet packages
- `dotnet build -c Release` - Build project in Release mode
- `dotnet test` - Run unit tests using NUnit
- `dotnet pack -c Release` - Create NuGet package

### NuGet Package Building

Use the cross-platform build script for packaging:

```powershell
# Basic build and package
./build-nuget.ps1

# Build with specific version
./build-nuget.ps1 -Version "1.2.3"

# Build and publish to NuGet.org
./build-nuget.ps1 -Publish -ApiKey "YOUR_API_KEY"
```

The build script (`build_nuget.py`) handles:
- Cross-platform compatibility (Windows, macOS, Linux)
- Automatic version management
- Package validation
- Clean builds with proper error handling

### Manual Commands

```bash
# Alternative shell script (Unix-like systems)
./build-nuget.sh

# Python script directly
python3 build_nuget.py
```

## Architecture

### Core Components

**Models (`Awa.Client.Models`)**
- Auto-generated C# models from JSON schemas
- Includes workflow configuration classes: `AgentConfiguration`, `BuildPromptParams`, `InputParams`
- Agent execution models: `IsolatedAgentParams`, `IsolatedAgentEnvironmentResult`
- JIRA integration models: `JiraIssueRequest`, `JiraIssueResponse`
- Enums for agent modes (Act, Analyze) and providers (Claude, Goose, Codex, etc.)

**Utilities (`Awa.Client.Utilities.WorkflowUtilities`)**
- Static utility class for workflow operations
- File I/O operations: `ReadFileAsync`, `WriteFileAsync`, file bytes handling
- Directory operations: `ListDirectoryAsync`, `CopyDirectoryAsync`, `ReadDirectoryAsync`
- Workflow path management: `GetWorkflowPathsDirect`, `FindProjectRoot`
- Agent execution: `ExecuteAgentAsync`, `BuildPromptAsync`
- BAML transform operations: `ExecuteBamlTransformAsync`, batch processing
- JIRA integration: `ReadJiraIssueAsync`, `UpsertJiraIssueAsync`, `AddJiraCommentAsync`
- Concurrency control: `RunWithControlledConcurrencyAsync`

**Constants (`Awa.Client.Constants.AwaConstants`)**
- Task queue names: `AwaDefaultTaskQueue`
- Timeout configurations: File I/O (30s), Agent (15min), BAML (2min), MCP (30s)
- Activity names: All activities use `awa-` prefix (e.g., `awa-read-file`, `awa-execute-agent`)
- Workflow names: All workflows use `awa-` prefix (e.g., `awa-transform`, `awa-isolated-agent`)

### Temporal Integration

The SDK is built around Temporal workflow orchestration:

- **Task Queues**: Uses `awa_default` as the primary task queue
- **Activities**: All operations (file I/O, agent execution, transforms) are implemented as Temporal activities
- **Child Workflows**: Agent execution, transforms, and prompt building use child workflows
- **Timeouts**: All activity calls include proper timeout configurations
- **Retry Policies**: Configurable retry policies for activity execution

### Agent Integration

Supports multiple agent providers:
- **Claude**: Anthropic's Claude agent
- **Goose**: Block's Goose agent
- **Codex**: OpenAI's Codex agent
- **OpenCode**: Open source code agent
- **Q**: Additional agent provider

Agent execution modes:
- **Act**: Agent performs actions and makes changes
- **Analyze**: Agent analyzes and provides recommendations

## Development Standards

### Project Configuration

- **Target Framework**: .NET 8.0
- **Language Version**: C# 12.0
- **Nullable Reference Types**: Enabled
- **Package Generation**: Automatic on build
- **Documentation**: XML documentation file generation enabled
- **Symbol Packages**: Generated in snupkg format

### Dependencies

- **Temporalio**: Version 1.7.0 for workflow orchestration
- **Newtonsoft.Json**: Version 13.0.3 for JSON serialization
- **NUnit**: Testing framework with test adapters

### Coding Conventions

- **Async Methods**: All I/O operations are async with proper Task return types
- **Constants**: Use `AwaConstants` class for all activity/workflow names and timeouts
- **Error Handling**: Proper exception handling with meaningful error messages
- **Documentation**: XML documentation comments for all public APIs
- **Naming**: Use PascalCase for public APIs, follow .NET naming conventions

### Testing

- **Framework**: NUnit with NUnit3TestAdapter
- **Test Structure**: Organized in `Awa.Client.Tests` project
- **Coverage**: Uses coverlet.collector for code coverage
- **Test Categories**: Unit tests for utilities and models

## File Organization

```
Awa.Client/
├── Constants/
│   └── Constants.cs          # AWA constants and activity names
├── Models/
│   └── Models.cs            # Auto-generated models from JSON schemas
└── Utilities/
    └── WorkflowUtilities.cs # Static utility methods for workflows

Awa.Client.Tests/
└── Utilities/
    └── WorkflowUtilitiesTests.cs # Unit tests for utilities
```

### Key Files

- **Awa.Client.csproj**: Project configuration with NuGet package metadata
- **build_nuget.py**: Cross-platform build script with version management
- **Models.cs**: Auto-generated C# models (do not manually edit)
- **WorkflowUtilities.cs**: Core utility methods for workflow operations
- **Constants.cs**: Centralized constants for activity names and timeouts

## Workflow Patterns

### Standard Workflow Structure

1. **Path Setup**: Use `GetWorkflowPathsDirect` to establish workflow directory structure
2. **File Operations**: Use async file utilities (`ReadFileAsync`, `WriteFileAsync`)
3. **Agent Execution**: Use `ExecuteAgentAsync` with proper configuration
4. **Transform Operations**: Use `ExecuteBamlTransformAsync` for BAML-based transforms
5. **Error Handling**: All operations include timeout and retry configurations

### Example Usage

```csharp
// Get workflow paths
var paths = WorkflowUtilities.GetWorkflowPathsDirect(workflowDir, workflowType, workflowId);

// Read input file
var content = await WorkflowUtilities.ReadFileAsync(paths.Input + "/input.txt");

// Execute agent
var agentConfig = new AgentConfiguration { /* config */ };
var result = await WorkflowUtilities.ExecuteAgentAsync(agentConfig);

// Write output
await WorkflowUtilities.WriteFileAsync(paths.Output + "/result.txt", result);
```

## Deployment

The project uses automated NuGet package generation with:
- Version management through project file and build scripts
- Cross-platform build support (Windows, macOS, Linux)
- Automatic package validation
- Symbol package generation for debugging
- README and documentation inclusion

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "Analyze the codebase structure and key files", "status": "completed", "priority": "high"}, {"id": "2", "content": "Examine existing documentation and configuration files", "status": "completed", "priority": "high"}, {"id": "3", "content": "Create comprehensive CLAUDE.md file", "status": "completed", "priority": "high"}]
