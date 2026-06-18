# AWA Client Worker Starter - Dotnet (C#)

This is a starter project for building with the [Slalom Agentic Workflow Accelerator (AWA)](https://bitbucket.org/slalom-consulting/agentic-workflow-accelerator). This starter project is located in the main AWA repository at `cookbook/client-workers/dotnet/`.

## Overview

AWA supports polyglot deployments. This means that you can build your workflows in any language you want (leveraging shared child workflows and activities within AWA core) and then use AWA to run them.

![AWA Polyglot Deployment](./../../docs/images/awa-polyglot-architecture.png)

## CRITICAL

To get VS Code (or whatever IDE you're using) to work nicely, it's important that you open the `cookbook/client-workers/dotnet` directory itself rather than the root directory of the repo. This will ensure your environment tooling works properly.

### Project Structure

```
client-workers/dotnet/
├── AgenticWorkflowApp.sln               # Visual Studio solution file
├── AgenticWorkflowApp.Console/           # Main console application
│   ├── AgenticWorkflowApp.Console.csproj
│   ├── appsettings.json                  # Application configuration
│   ├── Program.cs                        # Application entry point with auto-discovery
│   ├── Configuration/                    # Configuration models
│   ├── Converters/                       # Custom Temporal payload converters
│   ├── Extensions/                       # Service collection extensions
│   │   ├── ServiceCollectionExtensions.cs  # DI configuration with Polly integration and system setup
│   │   └── TemporalWorkerBuilder.cs        # Temporal worker configuration
│   ├── Models/                          # Core model classes
│   │   ├── TemporalInfo.cs
│   │   ├── WorkflowInfo.cs
│   │   ├── ActivityInfo.cs
│   │   ├── ParameterInfo.cs
│   │   └── RegistrationPayload.cs
│   ├── Services/                        # Consolidated core services (3 services)
│   │   ├── WorkflowDiscoveryService.cs   # Discovery + metadata extraction + info building
│   │   ├── WorkflowRegistryService.cs    # Main orchestrator service (IHostedService)
│   │   └── WorkerRegistrationClient.cs   # AWA API client + registration with Polly resilience
│   └── Workflows/
│       └── HelloWorld/                   # Sample workflow implementation
│           ├── HelloWorldWorkflow.cs     # Main workflow definition
│           ├── Activities/               # Workflow activities
│           │   ├── AddTimestampActivity.cs
│           │   └── GetHeaderActivity.cs
│           └── Models/                   # Data models
│               ├── AddTimestampActivityInput.cs
│               └── HelloWorldWorkflowInput.cs
└── AgenticWorkflowApp.Console.Tests/    # Unit tests (14 tests)
    ├── AgenticWorkflowApp.Console.Tests.csproj
    └── Services/                          # Unit tests for core services
        ├── WorkflowDiscoveryServiceTests.cs
        └── WorkerRegistrationClientTests.cs
```

## Run

### 1. Run AWA via the AWA CLI

```bash
# From the root of the AWA repo
make start
```

OR

```bash
# From the root of the AWA repo
uv run -m awa.main start
```

### 2. Run the dotnet worker (this app)

```bash
# From the `cookbook/client-workers/dotnet` directory
make starter-dotnet
```

OR

```bash
# From the `cookbook/client-workers/dotnet` directory
dotnet run --project AgenticWorkflowApp.Console/AgenticWorkflowApp.Console.csproj
```

### 3. Run the workflow via the AWA CLI

```bash
# From the root of the AWA repo
uv run -m awa.main run -w hello-world-dotnet -i "{'name': 'World'}" -q awa_client_dotnet
```

## Debug

You can debug your client worker like any other .NET application. Open the dotnet solution (`AgenticWorkflowApp.sln`), in your IDE of choice, then use F5 to debug.

## Automatic Workflow and Activity Discovery

This .NET client worker now includes **automatic workflow and activity discovery**, eliminating the need for manual hardcoded registration in `Program.cs`.

### How It Works

1. **Discovery**: Uses reflection to scan assemblies for classes with `[Workflow]` attributes and methods with `[Activity]` attributes
2. **Metadata Extraction**: Generates JSON schemas from C# types using .NET 9's JsonSchemaExporter for AWA API registration
3. **Registration**: Automatically registers discovered workflows/activities with both Temporal and the AWA API
4. **Fail-Fast Reliability**: Fails immediately on any discovery or registration errors with detailed diagnostics

### Simplified Architecture (Post-Refactoring)

The implementation uses **3 core services** with clear single responsibilities:

- **`WorkflowDiscoveryService`**: Handles discovery, metadata extraction, and info building in one consolidated service
- **`WorkflowRegistryService`**: Orchestrates the overall registration process
- **`WorkerRegistrationClient`**: Manages HTTP communication and API registration with AWA Core

### Configuration

Configure auto-discovery via `appsettings.json`:

```json
{
  "AwaCoreConfiguration": {
    "ApiBaseUrl": "http://localhost:8001",    // AWA API endpoint
    "WorkerName": "dotnet-worker",            // Worker identifier
    "WorkerVersion": "1.0.0",                 // Worker version
    "EnableAutoDiscovery": true,              // Enable/disable discovery
    "SkipRegistration": false                 // Skip API registration entirely
  }
}
```

Or via environment variables:
- `AWA_API_BASE_URL`: AWA API endpoint
- `AWA_WORKER_NAME`: Worker name
- `AWA_WORKER_VERSION`: Worker version

### Migration from Manual Registration

**Before (manual registration):**
```csharp
services
    .AddHostedTemporalWorker(...)
    .AddScopedActivities<AddTimestampActivity>()
    .AddScopedActivities<GetHeaderActivity>()
    .AddWorkflow<HelloWorldWorkflow>();
```

**After (automatic discovery):**
```csharp
services.AddWorkflowSystem(context.Configuration); // Single method setup
```

### Adding New Workflows and Activities

Simply add the appropriate attributes to your classes and methods:

**Workflow Example:**
```csharp
[Workflow("my-new-workflow")]
public class MyNewWorkflow
{
    [WorkflowRun]
    public async Task<string> RunAsync(MyWorkflowInput input)
    {
        // Workflow implementation
    }
}
```

**Activity Example:**
```csharp
public class MyActivities
{
    [Activity("my-activity")]
    public Task<string> DoSomething(MyActivityInput input)
    {
        // Activity implementation
    }
}
```

## Test

Automated tests are critical for maintaining quality in any application. A major benefit of using Temporal is that workflows and activities are just functions, which makes testing them easy.

### Running Tests

```bash
# Run all tests
dotnet test

# Run with coverage
dotnet test --collect:"XPlat Code Coverage"
```

### Test Structure

- **Unit Tests**: Located in `AgenticWorkflowApp.Console.Tests/Services/`
- **Discovery Tests**: Verify workflow/activity discovery functionality in `WorkflowDiscoveryServiceTests`
- **Registration Tests**: Test HTTP client and API integration in `WorkerRegistrationClientTests`
- **Error Handling Tests**: Verify fail-fast behavior and exception handling

See the [Temporal .NET SDK docs](https://docs.temporal.io/develop/dotnet/testing-suite) for details on testing workflows and activities.

## Performance & Reliability Features

### **Performance Optimizations**
- **Assembly Caching**: Cached reflection results for faster subsequent discoveries
- **Single-Pass Discovery**: Consolidated discovery and metadata building eliminates redundant processing
- **Discovery Metrics**: Logs show timing: "Discovery completed in Xms"
- **Efficient Scanning**: Optimized assembly filtering and type detection
- **HTTP Resilience**: Polly retry policies with exponential backoff

### **Fail-Fast Reliability**
- **No Silent Failures**: All errors throw immediately with detailed context
- **Rich Error Messages**: Specific guidance for troubleshooting issues
- **Assembly Loading**: Detailed loader exception information for dependency issues
- **Configuration Validation**: Comprehensive startup validation with clear errors

### **Architecture Benefits (Post-Refactoring)**
- **40% Less Code**: Reduced from 7 services to 3 while maintaining all functionality
- **Eliminated Redundancy**: Removed duplicate metadata models and extraction logic
- **Improved Maintainability**: Clear single responsibility for each service
- **Better Performance**: Single discovery pass instead of multiple separate operations

## Troubleshooting

### Common Issues

1. **Workflows/Activities Not Discovered**
   - Verify `[Workflow]` and `[Activity]` attributes are present
   - Check that classes are public and not abstract
   - Ensure assemblies are being scanned correctly

2. **API Registration Failing**
   - Check `AWA_API_BASE_URL` configuration
   - Verify AWA core service is running
   - Review logs for specific error messages
   - Set `SkipRegistration: true` to bypass API registration for testing

3. **JSON Schema Generation Issues**
   - Ensure input models have public properties
   - Use simple types where possible (string, int, bool)
   - Check logs for schema generation warnings
