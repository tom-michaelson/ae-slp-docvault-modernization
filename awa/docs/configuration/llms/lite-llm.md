# LiteLLM Proxy Container

Optionally, AWA can leverage [LiteLLM's proxy container](https://docs.litellm.ai/docs/simple_proxy) (free, open source) for routing all LLM calls. Follow the steps below to set up LiteLLM for use with with AWA.

:::warning Not Required
LiteLLM is NOT required for AWA, but it is strongly recommended as it simplifies LLM configuration and supports a wide range of providers.
:::

## Supported Providers

- [Azure OpenAI](https://docs.litellm.ai/docs/providers/azure)
- [AWS Bedrock](https://docs.litellm.ai/docs/providers/bedrock)
- [Google VertexAI](https://docs.litellm.ai/docs/providers/vertex)
- [OpenAI](https://docs.litellm.ai/docs/providers/openai)
- [Anthropic](https://docs.litellm.ai/docs/providers/anthropic)
- [Many more...](https://docs.litellm.ai/docs/providers)

## Set up LiteLLM

### 1. Configure LiteLLM

Copy `litellm_config.yaml.example` to `litellm_config.yaml` and update the configuration as needed. Consult the [LiteLLM documentation](https://docs.litellm.ai/docs/providers) for configuration instructions for all supported providers.

**Example Configuration:**

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: azure_ai/gpt-4o
      api_base: <API_BASE_URL>
      api_key: <API_KEY>
      api_version: <API_VERSION>
litellm_settings:
  success_callback: ["langfuse"]
general_settings:
  master_key: sk-awa # This must match LITE_LLM_API_KEY in .env
```

:::info Langfuse
Note the `litellm_settings.success_callback` configuration above. If this is present, all traces will be sent to Langfuse automatically. With this setup, you do not need to turn `llm_trace.enabled` on in your AWA `config.yaml` file.
:::

:::warning NOTE
When using an AWS Profile with SSO, your credentials may regularly expire. When this happens, you may need to restart the LiteLLM container to pick up the new credentials after re-authenticating your AWS CLI.
:::

#### Configuring GitHub Copilot Models

GitHub Copilot models can be proxied through LiteLLM to ensure BAML compatibility. This is the recommended approach for using GitHub Copilot with AWA.

:::info BAML Compatibility
GitHub Copilot's API has a compatibility issue with BAML (missing `index` field in responses). Using LiteLLM as a proxy resolves this issue by normalizing the API responses.
:::

<!--@include: /../../.shared/github-copilot-litellm-config.md -->

For more details on using GitHub Copilot, see the [GitHub Copilot documentation](./github-copilot.md#using-github-copilot-via-litellm-proxy-recommended).

### 2. Start LiteLLM Proxy Container

- If you want to run AWA locally in a docker container along with all supporting services:
  - Run `docker compose up --build --remove-orphans -d` to launch AWA and all supporting services as defined in `docker-compose.yml`.
- If you want to run AWA locally outside a docker container (e.g., for development purposes):
  - Run `docker compose -f docker-compose.awa-supporting.yml up --remove-orphans -d` to start all supporting services but NOT AWA itself.

### 3. Set up environment variables

Update your AWA `.env` file to use the LiteLLM proxy container.

:::code-group

```bash [.env]
#------------------------------#
#         LLM Providers        #
#------------------------------#
# This must match `general_settings.master_key` in `litellm_config.yaml`
LITE_LLM_API_KEY=sk-awa
```

:::

### 4. Configure provider and models in config.yaml

:::code-group

```yaml [config.yaml]
llm:
  default_model: my-litellm-gpt-4o
  providers:
    lite_llm:
      base_url: http://localhost:4002 # Should be docker.host.internal:4002 if running AWA in docker
  models:
    - name: my-litellm-gpt-4o
      provider: litellm
      model: gpt-4o
      temperature: 0.1
      max_tokens: 32000
      use_cache: true
```

:::
