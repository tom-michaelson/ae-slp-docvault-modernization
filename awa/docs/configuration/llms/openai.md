# OpenAI

:::danger OpenAI != Azure OpenAI
If you're looking to use Azure OpenAI, see [Azure OpenAI](./azure-openai.md) instead.
:::

## OpenAI Configuration

### 1. Set environment variables

Set your environment variables in your `.env` file.

:::code-group

```sh [.env]
#------------------------------#
#         LLM Providers        #
#------------------------------#
OPENAI_API_KEY=your_key
```

:::

### 2. Configure models in config.yaml

Set up one or more models in `config.yaml`.

:::code-group

```yaml [config.yaml]
llm:
  default_model: my-openai-gpt-4.1
  # ...
  providers:
    openai:
      # Optional overrides for OpenAI-compatible endpoints (e.g., Databricks)
      # base_url: https://adb-12345.18.azuredatabricks.net/serving-endpoints
    # ...
  models:
    - name: my-azure-gpt-4.1
      provider: openai
      model: gpt-4.1
      temperature: 0.1
      max_tokens: 32000
      use_cache: true
```

:::

### 3. Using Databricks or other OpenAI-compatible endpoints

Databricks and several other vendors expose OpenAI-compatible APIs. Configure two pieces:

1. Set `OPENAI_API_KEY` to your Databricks personal access token.
2. Provide the custom `base_url` under `llm.providers.openai`.

```yaml
llm:
  providers:
    openai:
      base_url: https://<workspace-host>/serving-endpoints
```

AWA reads the token from `OPENAI_API_KEY`, so no additional environment variables are required.
