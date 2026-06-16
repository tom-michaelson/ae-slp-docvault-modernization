# C# SDK Usage

This guide explains how to consume the AWA C# SDK (`Awa.Client`) published to AWS CodeArtifact.

## Setup and Authentication

<!--@include: /../../.shared/sdk-client-usage.md -->

:::danger Prerequisites
Be sure you have fulfilled the [prerequisites](./index.md#prerequisites) before attempting to use this SDK.
:::

### 1. Install CodeArtifact Credential Provider

The CodeArtifact credential provider handles authentication automatically:

```bash
# Install the global tool
dotnet tool install -g AWS.CodeArtifact.NuGet.CredentialProvider

# Install the credential provider
dotnet codeartifact-creds install
```

::: warning Mac Users
On macOS, you may need to add dotnet tools to your PATH:

```bash
export PATH="$PATH:$HOME/.dotnet/tools"
```

Add this to your `.zshrc` or other shell configuration file for persistence.
:::

### 2. Configure AWS Profile (Optional)

If using a specific AWS profile:

```bash
dotnet codeartifact-creds configure set profile <your-profile-name>
```

### 3. Add CodeArtifact as Package Source

Configure your project or global NuGet settings to use CodeArtifact:

```bash
# Login to CodeArtifact (adds the source automatically)
aws codeartifact login \
  --tool dotnet \
  --domain slalom-all \
  --domain-owner 825505919920 \
  --repository slalom-nuget \
  --profile <your-profile>

# Verify the source was added
dotnet nuget list source
```

## Installing the C# SDK

### In a .NET Project

Add the AWA Client package to your project:

```bash
# Install the latest version
dotnet add package Awa.Client

# Install a specific version
dotnet add package Awa.Client --version 1.0.6
```

:::warning Don't Specify `--source`
You may be tempted to explicitly specify the source (e.g. `--source slalom-all/slalom-nuget`) when installing the package (this author was). However, this seems to trip up the dotnet CLI in way that causes the package to not be found at all. Instead, ensure you've authenticated to CodeArtifact (`aws codeartifact login` as shown above) then try `dotnet add ...` without specifying a source at all.
:::

## Using the C# SDK

```csharp
using Awa.Client.Models;
using Awa.Client.Constants;
using Awa.Client.Utilities;

// Use AWA models
var config = new ConfigurationModel
{
    // ... configuration properties
};

// Access constants
var version = Constants.SDK_VERSION;

// Use utility functions
var result = UtilityFunctions.ProcessData(input);
```
