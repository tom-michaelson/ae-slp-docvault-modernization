| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `jira` | object or null | No | `null` | Jira configuration |
| `llm` | object | Yes |  | LLM configuration |
| `logging` | object | No |  | Logging configuration |
| `recipes` | boolean | No | `true` | Enable recipe workflows and activities registration. When true, recipe workflows will be discovered and registered with the worker. |
| `s3_vector` | object or null | No | `null` | S3 Vector Store configuration |

### jira

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `api_user` | string or null | No | `null` | The API user (email address) to use for Jira API authentication. Must be the owner of the API key in JIRA_API_KEY environment variable. |
| `url` | string or null | No | `"https://slalom.atlassian.net"` | The URL of the Jira instance. |

### llm

Configuration for LLM settings.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `behavior` | object | No |  | LLM call behavior configurations |
| `default_model` | string | Yes |  | Default model name to use for LLM calls. Must match name in the `models` configuration. |
| `embedding_models` | array or null | No | `null` | Embedding models configuration |
| `models` | Array of objects | Yes |  | LLM models configuration |
| `providers` | object | No |  | LLM providers configuration |

#### behavior

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `auto_retry_parse` | object | No |  | Auto retry configuration |
| `use_cache` | boolean | No | `true` | Whether to use the cache globally. If cache is used and a cached value is found, the LLM call will not be made. Can be overridden from `llm.models[*].use_cache` |

##### auto_retry_parse

Settings for retrying LLM calls when a BAML parsing error occurs.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Whether to enable auto retry on parse error. If true, the LLM call will be retried up to `max_attempts` times. |
| `max_attempts` | integer | No | `3` | Maximum number of attempts to retry the LLM call. |
| `temperature_increment` | number | No | `0.1` | Temperature increment to use for each retry. |

#### models (array)

Configuration for an individual LLM model.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `api_version` | string or null | No | `null` | Azure OpenAI API version (for azureopenai provider) |
| `domain` | string or null | No | `null` | Azure domain for the service (for azureopenai provider). Use 'openai.azure.com' for Azure OpenAI Service or 'cognitiveservices.azure.com' for Cognitive Services multi-service. If not specified, falls backto provider-level domain. |
| `is_gpt5_model` | boolean | No | `false` | Whether this is a GPT-5 model. Enables GPT-5 specific parameters and features. |
| `max_completion_tokens` | integer or null | No | `null` | Max completion tokens for Chat Completions API (GPT-5 reasoning models) |
| `max_output_tokens` | integer or null | No | `null` | Max output tokens for Responses API (GPT-5 models) |
| `max_tokens` | integer or null | No | `null` | Max tokens, passed through to the LLM call (legacy parameter) |
| `model` | string | Yes |  | LLM model name. Must match format expected by the specific `provider` |
| `name` | string | Yes |  | User-defined model name. Used to refer to this model when executing LLM calls, or from `default_model` |
| `provider` | string (enum) | Yes |  | LLM provider Allowed values: `OpenAI`, `AzureOpenAI`, `AwsBedrock`, `GoogleVertex`, `LiteLLM`, `GithubCopilot`, `Anthropic`. |
| `reasoning_effort` | integer or string or null | No | `null` | Reasoning effort. For GPT-5: 'minimal', 'low', 'medium', 'high'. For GPT-4: integer or string. |
| `resource_name` | string or null | No | `null` | Azure OpenAI resource name (for azureopenai provider) |
| `temperature` | number | No | `0.0` | Temperature, passed through to the LLM call |
| `use_cache` | boolean or null | No | `null` | Whether to use the cache. If cache is used and a cached value is found, the LLM call will not be made. |
| `use_responses_api` | boolean | No | `false` | Whether to use the Responses API endpoint instead of Chat Completions API. |
| `verbosity` | string or null | No | `null` | GPT-5 verbosity level. Controls output length and detail. Only applies to GPT-5 models. |

#### providers

Configuration for LLM providers.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `anthropic` | object or null | No | `null` | Configuration for Anthropic |
| `azure_openai` | object or null | No | `null` | Configuration for Azure OpenAI |
| `github_copilot` | object or null | No | `null` | Configuration for GitHub Copilot |
| `google_vertex` | object or null | No | `null` | Configuration for Google Vertex AI |
| `lite_llm` | object or null | No | `null` | Configuration for LiteLLM proxy |
| `openai` | object or null | No |  | Configuration for OpenAI |

##### anthropic

Configuration for Anthropic LLM provider.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `base_url` | string or null | No | `null` | Optional base URL for Anthropic API. If not specified, uses the default Anthropic API endpoint. |

##### azure_openai

Configuration for Azure OpenAI LLM provider.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `api_version` | string | Yes |  | The API version to use for the Azure OpenAI resource. |
| `domain` | string | No | `"openai.azure.com"` | Azure domain for the service. Use 'openai.azure.com' for Azure OpenAI Service or 'cognitiveservices.azure.com' for Cognitive Services multi-service. |
| `resource_name` | string | Yes |  | The name of the Azure OpenAI resource. |
| `use_entra_auth` | boolean | No | `false` | Use Entra ID (DefaultAzureCredential) authentication instead of API key. |

##### github_copilot

Configuration for GitHub Copilot LLM provider.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `base_url` | string | No | `"https://api.githubcopilot.com"` | The base URL for the GitHub Copilot API. |

##### google_vertex

Configuration for Google Vertex AI LLM provider.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `credentials_path` | string or null | No | `null` | Path to service account credentials JSON file. If not specified, will use default GCP authentication. |
| `location` | string | No | `"us-central1"` | The GCP region/location for Vertex AI (e.g., us-central1). |
| `project_id` | string or null | No | `null` | The GCP project ID. If not specified, will use default from GCP authentication. |

##### lite_llm

Configuration for LiteLLM proxy LLM provider.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `base_url` | string | Yes |  | The base URL for the LiteLLM proxy API. |

##### openai

Configuration for OpenAI-compatible LLM provider.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `base_url` | string or null | No | `null` | Optional base URL for the OpenAI-compatible API endpoint. |

### logging

Logging configuration for AWA.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `log_level` | string or object | No | `"INFO"` | Log level configuration - either a single level or component-specific levels |

#### log_level

Component-specific log level configuration.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `activity` | string | No | `"INFO"` | Activity log level |
| `api` | string | No | `"INFO"` | API service log level |
| `auth` | string | No | `"INFO"` | Auth log level |
| `cli` | string | No | `"INFO"` | CLI log level |
| `client` | string | No | `"INFO"` | Client log level |
| `engine` | string | No | `"INFO"` | Engine log level |
| `http` | string | No | `"INFO"` | HTTP log level |
| `script` | string | No | `"INFO"` | Script log level |
| `server` | string | No | `"INFO"` | Server service log level |
| `socketio` | string | No | `"INFO"` | Socket.IO log level |
| `ui` | string | No | `"INFO"` | UI service log level |
| `uvicorn` | string | No | `"INFO"` | Uvicorn/FastAPI log level |
| `worker` | string | No | `"INFO"` | Worker service log level |
| `workflow` | string | No | `"INFO"` | Workflow log level |

### s3_vector

Configuration for S3 Vector Store.

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `data_type` | string | No | `"float32"` | Vector data type |
| `distance_metric` | string | No | `"cosine"` | Distance metric for similarity search Allowed values: `euclidean`, `cosine`. |
| `embedding_source` | string | No | `"azure_openai"` | Source of embeddings (uses existing LLM config) Allowed values: `openai`, `azure_openai`, `tfidf`. |
| `enabled` | boolean | No | `false` | Enable S3 Vector Store |
| `index_name` | string | No | `"awa-vectors"` | Default vector index name |
| `metadata_keys` | Array of string | No |  | Non-filterable metadata keys |
| `region_name` | string | No | `"us-west-2"` | AWS region name |
| `vector_bucket_arn` | string or null | No | `null` | S3 Vector bucket ARN |
| `vector_bucket_name` | string or null | No | `null` | S3 Vector bucket name |
