# GitHub Copilot

This page contains information on how to use your GitHub Copilot subscription as AWA's LLM provider.

Yes, GitHub Copilot's API can be used directly as a generic OpenAI API provider. This means that if you have access to GitHub Copilot, you can use AWA (no Innovation Labs required).

## Authentication

### OAuth Device Flow (Recommended)

The easiest and most secure way to authenticate with GitHub Copilot is using the OAuth device flow:

```bash
uv run -m awa.main auth login github-copilot
```

This command will:

1. Automatically open your browser to the GitHub authorization page
2. Display a code for you to enter
3. Wait for you to complete authorization
4. Securely store your credentials in `~/.awa/credentials.json`

Once authenticated, AWA will automatically manage token refresh, so you don't need to worry about expiring credentials.

**Managing Authentication:**

```bash
# Check authentication status
uv run -m awa.main auth status

# Re-authenticate if needed
uv run -m awa.main auth login github-copilot

# Logout and remove credentials
uv run -m awa.main auth logout github-copilot
```

### Alternative: Manual API Key

Tip of the hat to Aider, where we borrowed this configuration from: https://aider.chat/docs/llms/github.html

If you prefer to use a static API key instead of OAuth, you can extract one from your IDE:

Sign in to Copilot from any JetBrains IDE (PyCharm, GoLand, etc). After you authenticate a file appears:

```sh
~/.config/github-copilot/apps.json
```

On Windows the config can be found in:

```sh
~\AppData\Local\github-copilot\apps.json
```

Copy the oauth_token value – that string is your GITHUB_COPILOT_API_KEY.

Note: tokens created by the Neovim **copilot.lua** plugin (old `hosts.json`) sometimes lack the needed scopes. If you see "access to this endpoint is forbidden", regenerate the token with a JetBrains IDE.

Set your environment variables in your `.env` file:

:::code-group

```sh [.env]
#------------------------------#
#       GitHub Copilot         #
#------------------------------#
GITHUB_COPILOT_API_KEY=your_key
```

:::

## Model Configuration

### Configure models in config.yaml

Set up one or more models in `config.yaml`.

:::code-group

```yaml [config.yaml]
llm:
  default_model: my-ghcopilot-claude-sonnet-4
  # ...
  providers:
    # Nothing is needed in `providers` for GitHub Copilot
    # ...
  models:
    - name: my-ghcopilot-claude-sonnet-4
      provider: githubcopilot
      model: claude-sonnet-4
      temperature: 0.1
      max_tokens: 32000
      use_cache: true
```

:::

## Using GitHub Copilot via LiteLLM Proxy (Recommended)

Due to a compatibility issue with BAML's parsing of GitHub Copilot API responses (missing `index` field in the response format), we recommend proxying GitHub Copilot through LiteLLM. LiteLLM normalizes the API responses to be fully compatible with BAML's expectations.

### Why Use LiteLLM Proxy?

The GitHub Copilot API returns responses that differ slightly from the OpenAI standard format that BAML expects. Specifically, the response is missing an `index` field, which causes BAML parsing errors. By routing requests through LiteLLM, the responses are normalized to match the expected format.

### Configuration Steps

<!--@include: /../../.shared/github-copilot-litellm-config.md -->

### Example Models via LiteLLM

Here are a few commonly used GitHub Copilot models that can be configured through the LiteLLM proxy:

- `ghcopilot/claude-sonnet-4.5` - Claude Sonnet 4.5 (recommended)
- `ghcopilot/claude-sonnet-4` - Claude Sonnet 4
- `ghcopilot/gpt-4o` - GPT-4 Optimized
- `ghcopilot/gpt-4` - GPT-4

:::warning Not Exhaustive
This is not a complete list of available models. GitHub Copilot provides access to many more models from OpenAI, Anthropic, Google, and other providers. See the [Discover Available Models](#discover-available-models) section below to get the full list of models available to your subscription.
:::

## Discover Available Models

Copilot hosts many models (OpenAI, Anthropic, Google, etc).

If using OAuth device flow, AWA will automatically use your stored credentials. If using a manual API key, you can list the models your subscription allows with:

```bash
curl -s https://api.githubcopilot.com/models \
  -H "Authorization: Bearer $GITHUB_COPILOT_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Copilot-Integration-Id: vscode-chat" | jq -r '.data[].id'
```

Each returned ID can be used as the `llm.models[*].model` value in `config.yaml`
