---
outline: 2
---

# SDK Generation Workflow

The SDK Generation workflow (`awa/workflows/generate_sdk/`) transforms Python models from `awa/sdk/models/` into client SDKs for different programming languages. The workflow features intelligent change detection, incremental updates, and automated publishing to package repositories.

Details on how to use AWA's SDKs can be found [here](/usage/sdk/index.md).

### Execution

#### End-to-End SDK Generation and Publishing

The complete SDK generation and publishing process involves three main stages:

##### 1. Prerequisites

Before running the SDK generation, ensure:

- Temporal services are running: `make start`
- You have authentication configured for package repositories (see Authentication section below)
- The SDK config is properly set up in `config.yaml`

##### 2. Generate SDKs

Run the SDK generation workflow to create/update SDKs for all enabled languages:

```bash
# Generate SDKs for all enabled languages
uv run -m awa.main run --workflow awa-generate-sdk

# Force regeneration (skip hash check)
uv run -m awa.main run --workflow awa-generate-sdk --input '{"force": true}'

# Bump version only (no SDK regeneration if content hasn't changed)
uv run -m awa.main run --workflow awa-generate-sdk --input '{"bump": true}'

# Use custom config path
uv run -m awa.main run --workflow awa-generate-sdk --input '{"config_path": "custom/sdk.config.yaml"}'
```

This workflow will:

- Detect changes in source models and utilities
- Generate language-specific SDKs in parallel
- Run tests and fix any failures using AI agents
- Package the SDKs for distribution

##### Optional: Manual Packaging

The SDK generation workflow automatically packages SDKs as part of its execution. However, you can also run the packaging scripts manually if needed (e.g., for testing or custom builds):

```bash
# Get the current SDK version
VERSION=$(uv run scripts/get_sdk_version.py)
echo "Current SDK version: $VERSION"

# Package Python SDK manually
uv run scripts/sdk/package_sdk_python.py --version $VERSION

# Package C# SDK manually
uv run scripts/sdk/package_sdk_csharp.py --version $VERSION
```

**Getting the SDK Version:**

- The current SDK version is stored in `sdk_dist/.hash/*.version` files
- Use `uv run scripts/get_sdk_version.py` to retrieve the latest version programmatically
- The version is automatically bumped when SDK source files change

These scripts are useful when you want to:

- Test packaging without running the full workflow
- Create custom builds with specific versions
- Debug packaging issues in isolation
- Package SDKs after manual modifications

##### 3. Publish SDKs

After successful generation, publish SDKs to their respective package repositories:

```bash
# Publish Python SDK to CodeArtifact
uv run scripts/sdk/publish_sdk_python.py --aws-profile $AWS_PROFILE

# Publish C# SDK to CodeArtifact
uv run scripts/sdk/publish_sdk_csharp.py --aws-profile $AWS_PROFILE
```

### Core Workflow Steps

1. **Change Detection** - Calculates hash of source files and compares with stored hashes
2. **Version Management** - Determines SDK version based on content changes
3. **Schema Generation** - Extracts JSON schemas from Python Pydantic models
4. **Model Generation** - Creates language-specific models using code generation tools
5. **Translation** - Converts constants and utility functions using LLM-powered transformations
6. **In-Place Updates** - Updates existing SDK files rather than wholesale replacement
7. **Facade Generation (Python)** - Auto-generates facade pattern files (`_facade.py` and `_facade.pyi`) for cleaner imports
8. **Build Verification** - Ensures test projects build successfully, commenting out problematic tests if needed
9. **Utility Function Testing** - Runs and fixes tests for each updated utility function in parallel
10. **Testing & Validation** - Runs language-specific tests and fixes failures with AI agents
11. **Publishing** - Automatically publishes SDKs to configured package repositories (PyPI, NuGet, etc.)

### Version Management

The workflow automatically manages SDK versions based on content changes:

- **Hash-Based Detection**: Calculates a SHA-256 hash of all SDK source files
- **Version Tracking**: Stores current version and hash in `sdk_dist/.hash/*.version`
- **Automatic Bumping**: Increments patch version when SDK content changes
- **Manual Bumping**: Use `bump: true` parameter to increment version without regenerating SDK (when no changes detected)
- **Consistent Versioning**: All language SDKs share the same version number

### Incremental Update System

The workflow uses a granular change detection system for efficient regeneration:

- **Component-Level Tracking**: Tracks changes to models, constants, and individual utility functions
- **Selective Regeneration**: Only regenerates changed components, not entire SDKs
- **Hash Storage**: Maintains component hashes in `.cache/generate_sdk_hashes.json`
- **Force Override**: Use `force: true` to bypass hash checking and regenerate all SDKs
- **Version Bump Override**: Use `bump: true` to increment version number only (skips regeneration when no changes detected)

### In-Place Update Pattern

Rather than deleting and recreating entire SDK directories, the workflow:

- **Preserves Structure**: Maintains existing project files and directory structure
- **Updates Selectively**: Only modifies generated files (models, constants, utilities)
- **Compares Content**: Checks if translated content differs before writing files
- **Maintains History**: Preserves git history and custom modifications to baseline files

### Python SDK Facade Pattern

The Python SDK includes an automatically generated facade pattern that provides a cleaner, organized import experience:

#### How It Works

1. **Auto-Discovery**: The facade generation activity scans all utilities, models, and constants during SDK generation
2. **Namespace Organization**: Creates organized namespaces (`AWA.workflow.*`, `AWA.activity.*`, and `AWA.general.*`) for utilities
3. **Facade Generation**: Creates `_facade.py` and `_facade.pyi` files with namespace classes
4. **Simplified Naming**: Automatically strips `_activity` and `_workflow` suffixes from function names
5. **IDE Support**: Generates `.pyi` stub files for full autocomplete and type hints

#### Generated Files

- **`_facade.py`**: Implementation file with lazy imports and property accessors
- **`_facade.pyi`**: Type stub file for IDE support
- **`__init__.py`**: Updated to export the `AWA` singleton instance

#### Benefits

- **Single Import**: `from awa.client import AWA` instead of multiple imports
- **Discoverable API**: All SDK components accessible through `AWA.` with autocomplete
- **Backward Compatible**: Traditional imports still work alongside the facade pattern
- **Auto-Updated**: Regenerated automatically when SDK is rebuilt

## Configuration

The SDK generation is controlled by `awa/sdk/sdk.config.yaml`:

:::code-group

<<< ./../../../awa/sdk/sdk.config.yaml

:::

### Configuration Options

#### Root Level

- **`output_path`** (string): Directory where generated SDKs are written, relative to project root

#### Language Configuration

Each language entry supports these options:

- **`name`** (string): Language identifier (must match `SupportedLanguage` enum in `awa/workflows/generate_sdk/models/supported_language.py`)
- **`enabled`** (boolean): Whether to generate SDK for this language
- **`ext`** (string): File extension for generated files (e.g., `.cs`, `.py`, `.java`)
- **`model_file_name`** (string): Base name for the generated models file
- **`model_path`** (string): Directory path within the language SDK where models are placed
- **`constants_file_name`** (string): Base name for the constants file
- **`constants_path`** (string): Directory path for constants file
- **`namespace`** (string, optional): Namespace/package identifier for languages that support it
- **`package`** (string, optional): Package name for languages that use package management
- **`test_command`** (string, optional): Command to run tests for the generated SDK
- **`publish_config`** (object, optional): Publishing configuration for automated deployment

#### Publishing Configuration

Each language can include a `publish_config` section with these options:

- **`enabled`** (boolean): Whether to enable automatic publishing for this language
- **`type`** (string): Repository type - `"pypi"`, `"nuget"`, `"codeartifact"`, `"npm"`
- **`repository`** (string, optional): Repository name (e.g., "slalom-pypi", "slalom-nuget")
- **`repository_url`** (string, optional): Custom repository URL (if not using default)
- **`package_name`** (string, optional): Package name to publish (e.g., "awa-client", "Awa.Client")
- **`api_token`** (string, optional): API token for authentication (PyPI, NuGet.org, npm)
- **`username`** (string, optional): Username for basic auth
- **`password`** (string, optional): Password for basic auth
- **`aws_profile`** (string, optional): AWS profile to use for CodeArtifact
- **`domain`** (string, optional): CodeArtifact domain (e.g., "slalom-all")
- **`domain_owner`** (string, optional): CodeArtifact domain owner account ID

## Manual Publishing: NuGet

### Configure Publishing Credentials

Follow the steps below to configure your local environment to publish to CodeArtifact.

More installation instructions and alternative options here: https://docs.aws.amazon.com/codeartifact/latest/ug/nuget-cli.html

1. Authenticate with an AWS profile

See our [AWS Bedrock](/configuration/llms/aws-bedrock) docs for tips on this.

2. Install CodeArtifact global dotnet tool

```bash
dotnet tool install -g AWS.CodeArtifact.NuGet.CredentialProvider
```

:::warning Mac: Add to path manually

On Mac, global dotnet tools may not be automatically added to your path. If this is the case, you will need to add the following to your `.zshrc` or other shell configuration file:

```bash
export PATH="$PATH:$HOME/.dotnet/tools"
```

:::

3. Install CodeArtifact credential provider

```bash
dotnet codeartifact-creds install
```

4. Configure CodeArtifact credential provider with AWS profile

```bash
dotnet codeartifact-creds configure set profile <profile_name>

# Example
dotnet codeartifact-creds configure set profile taskstreamdev
```

5. Log in to CodeArtifact

```bash
aws codeartifact login --tool dotnet --domain <your_domain> --domain-owner <account_id> --repository <repository_name> --profile <profile_name>

# Example
aws codeartifact login --tool dotnet --domain slalom-all --domain-owner 825505919920 --repository slalom-nuget --profile taskstreamdev
```

6. List NuGet sources, and get the name of the CodeArtifact source, e.g. `slalom-all/slalom-nuget`

```bash
dotnet nuget list source
```

7. Publish to CodeArtifact

```bash
dotnet nuget push path/to/nupkg/SamplePackage.1.0.0.nupkg --source packageSourceName

# Example
dotnet nuget push bin/Release/Awa.Client.1.0.0.nupkg --source slalom-all/slalom-nuget
```

## Manual Publishing: Python

### Publishing to PyPI

1. Build the package

```bash
cd sdk_dist/python
uv build
```

2. Publish to PyPI

```bash
# Using API token (recommended)
uv publish --token $PYPI_API_TOKEN

# Using username/password
uv publish --username __token__ --password $PYPI_API_TOKEN
```

### Publishing to AWS CodeArtifact

1. Configure AWS credentials

```bash
aws configure --profile your-profile
# or
export AWS_PROFILE=your-profile
```

2. Get CodeArtifact token

```bash
export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token \
  --domain slalom-all \
  --domain-owner 825505919920 \
  --query authorizationToken \
  --output text)
```

3. Get repository URL

```bash
export CODEARTIFACT_REPOSITORY_URL=$(aws codeartifact get-repository-endpoint \
  --domain slalom-all \
  --domain-owner 825505919920 \
  --repository slalom-pypi \
  --format pypi \
  --query repositoryEndpoint \
  --output text)
```

4. Build and publish

```bash
cd sdk_dist/python
uv build
uv publish \
  --publish-url "${CODEARTIFACT_REPOSITORY_URL}/" \
  --username aws \
  --password $CODEARTIFACT_AUTH_TOKEN
```
