# Agent - GitHub Copilot CLI

This document provides instructions on how to install and configure GitHub Copilot CLI for use with AWA.

For detailed information, refer to the official [GitHub Copilot CLI documentation](https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli).

## Installation

See the official documentation for information about how to install GitHub Copilot CLI on your system:

* [Installing GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli)

## Configuration

Using GitHub Copilot CLI requires authentication with GitHub. You must authenticate with the GitHub CLI before using the agent.

You can log in by running:

```bash
gh auth login
```

You will be prompted to authenticate with GitHub. Follow the interactive prompts to complete authentication.

Verify your authentication status:

```bash
gh auth status
```
