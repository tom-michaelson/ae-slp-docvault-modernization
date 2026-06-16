# Azure OpenAI

## Get Credentials

- Reference [Using OpenAI in Azure Innovation Lab](https://slalom.service-now.com/help?id=kb_article&table=kb_knowledge&sys_id=3c238db0474e1250ceea6621e36d43ee&recordUrl=%2Fkb_view.do%3Fsys_kb_id%3D3c238db0474e1250ceea6621e36d43ee) in Slalom Help for information accessing OpenAI within the Slalom Azure Innovation Lab

- If you don't have access to the Azure Innovation Lab [Fill out an Azure Innovation Lab request form
  ](https://slalom.service-now.com/help?id=kb_article&table=kb_knowledge&sys_id=e8fb622733e996d0c81333a45d5c7b0d&recordUrl=%2Fkb_view.do%3Fsys_kb_id%3De8fb622733e996d0c81333a45d5c7b0d)

## Azure OpenAI Configuration

AWA supports two authentication methods for Azure OpenAI:

1. **Entra ID Authentication (Recommended)**: Uses DefaultAzureCredential for seamless authentication
2. **API Key Authentication**: Traditional method using API keys

Choose the method that best fits your deployment environment.

### 1. Get values from Azure Portal

Get the configuration values you need from the Azure Portal. This is a tricky step many people have trouble with, so here are some notes to help you ensure you get the right values.

1. Navigate to the Azure AI Foundry "Deployments" page: <https://ai.azure.com/resource/deployments>
2. Deploy a new model, or select the existing deployment you want to use.
3. In the top left corner of the deployment page, copy the "Target URI" value (pictured below).

![Azure OpenAI Target URI](/images/azure-openai-target-uri.png)

4. All the values you need are in this URI. here's how to parse it:

```
https://houston-build-opnai.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2025-01-01-preview

https://{{resource_name}}.openai.azure.com/openai/deployments/{{deployment_name}}/chat/completions?api-version={{api_version}}
```

This will give you the following `config.yaml` values:

- **resource_name** = `houston-build-opnai` (used in `config.yaml` as `llm.providers.azure_openai.resource_name`)
- **api_version** = `2025-01-01-preview` (used in `config.yaml` as `llm.providers.azure_openai.api_version`)
- **deployment_name** = `gpt-4` (used in `config.yaml` as `llm.models[*].model`)

:::warning Deployment Name vs. Model Name

The `deployment_name` is the name of the deployment in the Azure AI Foundry. It _can_ match the model name, but doesn't have to. Be careful to use the **deployment name**, as that is what is required by the Azure OpenAI API. The actual model name itself is not used anywhere in this configuration.

:::

5. Repeat this step for the embeddings model you want to use (for `llm.gpt_embedding.model`, `llm.services.azure_open_ai.embeddings_endpoint` and `llm.services.azure_open_ai.embeddings_api_version`).

## Option A: Entra ID Authentication (Recommended)

Entra ID authentication uses DefaultAzureCredential to automatically authenticate using your Azure identity. This is the recommended approach for production deployments.

### 1. Azure Requirements

Ensure your environment has one of the following authentication methods available:

- **Azure CLI**: Run `az login` to authenticate
- **Managed Identity**: Available when running on Azure resources (VMs, App Service, etc.)
- **Environment Variables**: Set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID`
- **Visual Studio Code**: Sign in to Azure through VS Code

### 2. Azure Permissions

Your Azure identity needs the following permissions on the Azure OpenAI resource:

- **Cognitive Services OpenAI User** role, or
- **Cognitive Services OpenAI Contributor** role

### 3. Configure provider and models in config.yaml

Set up one or more models in `config.yaml` with Entra authentication enabled:

:::code-group

```yaml [config.yaml - Entra ID]
llm:
  default_model: my-azure-gpt-4.1
  # ...
  providers:
    azure_openai:
      resource_name: my-azure-ai-foundry
      api_version: "2025-01-01-preview"
      domain: "openai.azure.com"  # Use "cognitiveservices.azure.com" for Cognitive Services multi-service
      use_entra_auth: true  # Enable Entra ID authentication
  models:
    - name: my-azure-gpt-4.1
      provider: azureopenai
      model: gpt-4.1
      temperature: 0.1
      max_tokens: 32000
      use_cache: true
```

:::

### 4. Test your configuration

You can test your Entra authentication with this Python script:

```python
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

# Use token provider for proper bearer token authentication
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

client = AzureOpenAI(
    api_version="2025-01-01-preview",
    azure_endpoint="https://YOUR-RESOURCE-NAME.openai.azure.com/",
    azure_ad_token_provider=token_provider  # Proper bearer token authentication
)

response = client.chat.completions.create(
    model="YOUR-DEPLOYMENT-NAME",  # Use your deployment name (e.g., "gpt-4.1")
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)
print(response.choices[0].message.content)
```

**Note:** AWA automatically handles token refresh and uses proper Bearer token authentication via the `Authorization` header, so you don't need to worry about token expiration in your application code.

**Implementation Details:**
- AWA uses `AzureCliCredential` for clean error handling (no credential chain stack traces)
- Tokens are passed as `Authorization: Bearer <token>` headers to BAML clients
- Fresh tokens are acquired for each request to ensure validity

## Option B: API Key Authentication

If you prefer to use API keys or cannot use Entra authentication, follow this approach.

### 1. Set environment variables

Set your environment variables in your `.env` file.

:::code-group

```sh [.env]
#------------------------------#
#         LLM Providers        #
#------------------------------#
AZURE_OPENAI_API_KEY=YOUR_KEY_HERE
```

:::

### 2. Configure provider and models in config.yaml

Set up one or more models in `config.yaml` with API key authentication:

:::code-group

```yaml [config.yaml - API Key]
llm:
  default_model: my-azure-gpt-4.1
  # ...
  providers:
    azure_openai:
      resource_name: my-azure-ai-foundry
      api_version: "2025-01-01-preview"
      domain: "openai.azure.com"  # Use "cognitiveservices.azure.com" for Cognitive Services multi-service
      use_entra_auth: false  # Use API key authentication (default)
  models:
    - name: my-azure-gpt-4.1
      provider: azureopenai
      model: gpt-4.1
      temperature: 0.1
      max_tokens: 32000
      use_cache: true
```

:::
