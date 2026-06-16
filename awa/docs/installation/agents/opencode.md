# Agent - OpenCode

This document provides instructions on how to install and configure the OpenCode AI coding agent for use with AWA.

OpenCode is an AI coding agent built for the terminal by SST. It provides an interactive development environment with multiple AI model support and MCP (Model Context Protocol) integration. For complete details, refer to the official [OpenCode Installation Documentation](https://opencode.ai/).

## Installation

See the [official docs](https://opencode.ai/) for information about how to install OpenCode on your system.

### Quick Installation

#### Windows (without WSL)

OpenCode works natively on Windows without requiring WSL. Before installing OpenCode, you must install the required dependencies:

**Option 1: Using Chocolatey**

```powershell
# Install dependencies via Chocolatey
choco install ripgrep fzf

# Then install OpenCode
npm install -g opencode
```

**Option 2: Using Scoop**

```powershell
# Install dependencies via Scoop
scoop install ripgrep fzf

# Then install OpenCode
npm install -g opencode
```

**Option 3: Direct Installation**

1. Download ripgrep from the [official releases page](https://github.com/BurntSushi/ripgrep/releases)
2. Download fzf from the [official releases page](https://github.com/junegunn/fzf/releases)
3. Extract both tools and add to your PATH
4. Then install OpenCode:

```bash
npm install -g opencode
```

#### macOS/Linux

```bash
# Install OpenCode globally
npm install -g opencode
```

> **Note**: On macOS and Linux, ripgrep is typically included with OpenCode or can be installed via package managers.

## Configuration

OpenCode is configured through a `opencode.json` configuration file in your project root. AWA includes a pre-configured setup that provides:

- **Multiple AI Models**: Support for GPT-4.1, GPT-4o, GPT-4o-mini, and Claude 3.5 Sonnet
- **GitHub Copilot Integration**: Uses GitHub Copilot as the model provider
- **MCP Integration**: Includes Python LSP server for enhanced code intelligence
- **Customizable Settings**: Theme, logging, and instruction configuration

### Example Configuration

The AWA project includes an `opencode.json` file with the following structure:

:::code-group

<<< @/../opencode.example.json

:::

## Usage with AWA

OpenCode integrates with AWA through the `OpenCodeAgent` class, which provides:

- **Command Execution**: Execute OpenCode prompts through AWA workflows
- **Working Directory Support**: Run commands in specific project directories
- **Error Handling**: Proper error detection and status reporting
- **Async Operations**: Non-blocking command execution

### Example Usage

```python
from awa.core.activities.agent_modes.opencode_agent import OpenCodeAgent

# Initialize the agent
agent = OpenCodeAgent()

# Execute a prompt
result = await agent.execute_prompt(
    prompt="Create a new Python function to calculate fibonacci numbers",
    working_dir="/path/to/project"
)

# Check the result
if result.status:
    print(f"Success: {result.result}")
else:
    print(f"Error: {result.result}")
```

## Requirements

- **Node.js**: Required for OpenCode installation
- **ripgrep & fzf**: Required prerequisites for Windows users (see installation instructions above)
- **Python LSP Server**: For enhanced Python development (optional)

## Troubleshooting

If you encounter issues:

1. **Installation Issues**: Ensure Node.js and npm are properly installed
2. **Windows Dependencies**: If OpenCode fails to run, verify that both ripgrep and fzf are properly installed and available in your PATH
3. **"Error: agent coder not found"**: This typically indicates missing dependencies. Verify installation with:
   ```bash
   # Check if dependencies are available
   ripgrep --version
   fzf --version
   ```
4. **Configuration File**: If you see JSON syntax errors, check that your `opencode.json` file is properly formatted
5. **Model Access**: Verify GitHub Copilot subscription and authentication
6. **Permissions**: Ensure OpenCode has necessary file system permissions

> **Note**: See [OpenCode Issue #291](https://github.com/opencode-ai/opencode/issues/291) for additional Windows-specific troubleshooting details.

For more troubleshooting help, refer to the [OpenCode documentation](https://opencode.ai/) or the AWA project's issue tracker.
