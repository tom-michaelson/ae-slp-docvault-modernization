# Anthropic

## Anthropic Configuration

### 1. Set environment variables

Set your environment variables in your `.env` file.

:::code-group

```sh [.env]
#------------------------------#
#         LLM Providers        #
#------------------------------#
ANTHROPIC_API_KEY=your_key
```

:::

### 2. Configure models in config.yaml

Set up one or more models in `config.yaml`.

:::code-group

```yaml [config.yaml]
llm:
  default_model: my-anthropic-claude-4
  # ...
  providers:
    # The anthropic section is optional. You can:
    # 1. Omit it entirely (recommended if using default settings)
    # 2. Include it with no values: anthropic:
    # 3. Include it with custom settings
    anthropic:# This creates default settings (same as omitting)
    # base_url: https://custom.anthropic.api  # Optional custom base URL
  models:
    - name: my-anthropic-claude-4
      provider: anthropic
      model: claude-sonnet-4-20250514
      temperature: 0.7
      max_tokens: 4096
      use_cache: true
    - name: my-anthropic-claude-4-opus
      provider: anthropic
      model: claude-opus-4-20250514
      temperature: 0.7
      max_tokens: 4096
      use_cache: true
```

:::

## Available Models

For the latest model list and capabilities, visit [Anthropic's documentation](https://docs.anthropic.com/claude/docs/models-overview).
