# Package Installation

This guide covers installing AWA as a packaged application for end users. If you're developing AWA itself, see the [development setup guides](./mac-linux.md) instead.

**Related Documentation:**
- [Developer Workflow Guide](../contributing/developer-workflow.md) - Development and troubleshooting for AWA contributors

## Important Limitations

### UI Availability

**The AWA UI is currently not available when running as a packaged installation.** This is a temporary limitation while we work on UI packaging support.

**Affected Commands:**
- `awa ui` - Will display a warning and exit
- `awa start` - Will automatically exclude UI service and show warning
- `awa start --services ui` - Will fail with error message
- `awa start --services api,ui` - Will start only API service with warning

**Workarounds:**
- **Docker Deployment** (Recommended): Use Docker containers for full UI access. See [Docker Deployment Guide](../deployment/docker.md)
- **Development Installation**: If you need UI access for development, use the platform-specific development installation guides ([Mac & Linux](./mac-linux.md) | [Windows](./windows.md)) instead

**Services Still Available:**
- ✅ REST API (`awa start --services api`)
- ✅ Temporal Server (`awa start --services temporal_server`)
- ✅ Temporal Worker (`awa start --services temporal_worker`)
- ✅ All CLI commands and workflow execution

The API documentation will still be available at http://localhost:8001/docs when the API service is running.

## Quick Start

### Recommended Installation (UV-Managed)

We recommend using UV to manage AWA in an isolated environment for better reliability and process management:

#### Create UV Project:
```bash
# Create a new directory for AWA
mkdir awa-project && cd awa-project

# Initialize UV project
uv init

# Add AWA package
uv add path/to/awa-wheel.whl

# Run AWA commands via UV
uv run awa init
uv run awa start
uv run awa stop
```

### Alternative Installation Methods

#### Direct Python (Not Recommended):
```bash
# Run installation directly with Python
python3 scripts/install.py [path/to/awa-wheel.whl]
```

**Note**: Direct installation may cause process cleanup issues. UV-managed environments provide better subprocess handling and are the recommended approach.

## Installation Process

The UV-managed installation approach provides the following benefits:

1. **Isolated Environment** - AWA runs in its own virtual environment
2. **Better Process Management** - UV handles subprocess lifecycle properly
3. **Dependency Isolation** - Prevents conflicts with other Python packages
4. **Reliable Cleanup** - UV ensures proper process termination
5. **Easy Updates** - Simple package management with UV

For direct installation, the script performs these steps:

1. **Platform Detection** - Identifies your operating system and architecture
2. **Dependency Checking** - Verifies Python 3.12+ and Temporal CLI are installed
3. **Global Configuration Setup** - Creates `~/.awa/` directory for global settings
4. **Package Installation** - Installs the AWA wheel package using pip
5. **Installation Verification** - Confirms the `awa` command is available
6. **Initial Setup** - Optionally runs `awa init` for configuration

## Prerequisites

For detailed prerequisites installation instructions, see the [Prerequisites section in our Installation documentation](./parts/dependency_check.md).

The main requirements are:
- **UV** (recommended package manager)
- **Python 3.12+**
- **Temporal CLI**

### Access AWA Services:
- UI: http://localhost:8000
- API: http://localhost:8001/docs
- Temporal UI: http://localhost:8002

## Configuration

### Global Configuration

AWA stores global configuration in `~/.awa/`:
- `~/.awa/config.yaml` - Main configuration file
- `~/.awa/.env` - Environment variables (API keys, etc.)
- `~/.awa/services.json` - Service state tracking

### Local Configuration

You can override global settings for specific projects:
- `./config.yaml` - Local configuration (takes precedence)
- `./.env` - Local environment variables (takes precedence)

### UV Project Configuration

When using UV-managed environments, you can also configure AWA within the project:
```bash
# Create local configuration files in your UV project
cd awa-project
cp ~/.awa/config.yaml ./config.yaml
cp ~/.awa/.env ./.env

# These local files will take precedence over global settings
```

## Troubleshooting

### Common Issues

1. **"Python not found"**:
   - Ensure Python 3.12+ is installed and in PATH
   - On Windows, reinstall Python and check "Add Python to PATH"

2. **"Temporal CLI not found"**:
   - Install Temporal CLI using platform-specific instructions above
   - Verify with `temporal --version`

3. **"Permission denied"**:
   - On Unix systems, make sure script is executable: `chmod +x scripts/install.sh`
   - On Windows, run Command Prompt as Administrator if needed

4. **"Installation failed"**:
   - Check that the wheel file path is correct
   - Ensure you have write permissions to Python site-packages
   - Try running with `--force-reinstall` flag

5. **"command not found: awa"**:
   - Verify AWA was installed correctly: `uv run pip show slalom-agentic-workflow-accelerator`
   - Check if Python scripts directory is in PATH
   - For UV-managed installations, use `uv run awa` instead of just `awa`
   - Try reinstalling the package or reactivating your environment

### Manual Installation

If the automated script fails, you can install manually:

#### UV-Managed (Recommended):
```bash
# Create UV project
mkdir awa-project && cd awa-project
uv init

# Install the wheel directly
uv add path/to/awa-wheel.whl --force-reinstall

# Create global config directory
mkdir -p ~/.awa

# Run initial setup
uv run awa init

# Start services
uv run awa start
```

#### Direct Installation:
```bash
# Install the wheel directly
uv run pip install path/to/awa-wheel.whl --force-reinstall

# Create global config directory
mkdir -p ~/.awa

# Run initial setup
awa init

# Start services
awa start
```

## Next Steps

After successful installation:
1. Run `awa init` to set up your configuration
2. Run `awa start` to begin using AWA
3. Access AWA services at the URLs provided during startup

For development and contribution workflows, see the [Contributing documentation](../contributing/index.md).
