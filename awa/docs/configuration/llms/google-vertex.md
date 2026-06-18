# Google Vertex AI

## Get Credentials

Google Vertex AI uses Google Cloud Platform (GCP) authentication. You have several options for setting up authentication:

### Option 1: Service Account Key (Recommended for local development)

1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create your GCP project
3. Go to **IAM & Admin** → **Service Accounts**
4. Create a new service account or select an existing one
5. Create a key for the service account (JSON format)
6. Download the JSON key file to a secure location
7. Enable the Vertex AI API for your project

### Option 2: Application Default Credentials

1. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
2. Run `gcloud auth application-default login`
3. Enable the Vertex AI API for your project

### Option 3: Compute Engine Default Service Account

If running on Google Compute Engine, Kubernetes Engine, or App Engine, the default service account can be used automatically.

## Google Vertex AI Configuration

### 1. Set environment variables

Set your environment variables in your `.env` file.

:::code-group

```sh [.env]
#------------------------------#
#         LLM Providers        #
#------------------------------#
# Path to your service account JSON key file (if using Option 1)
# Google Vertex AI (will automatically use gcloud auth, metadata server, or service account file)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
```

:::

:::warning Authentication Methods
Google Vertex AI will automatically try multiple authentication methods in this order:

1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable (service account key file)
2. `gcloud auth application-default login` credentials
3. Google Cloud metadata server (when running on GCP)
4. `gcloud` CLI credentials

You only need to set `GOOGLE_APPLICATION_CREDENTIALS` if you're using a service account key file.
:::

### 2. Configure provider and models in config.yaml

Set up the provider configuration and one or more models in `config.yaml`.

Use `llm.providers.google_vertex` to configure your Google Vertex provider with the following options:

- **location** (required): The GCP region where your models are deployed (e.g., `us-central1`, `us-east1`, `europe-west1`)
- **project_id** (optional): Your GCP project ID. If not specified, will use the default project from your GCP authentication
- **credentials_path** (optional): Path to service account JSON file. If not specified, will use `GOOGLE_APPLICATION_CREDENTIALS` environment variable

:::code-group

```yaml [config.yaml]
llm:
  default_model: my-gemini-pro
  # ...
  providers:
    google_vertex:
      location: us-central1 # GCP region where your models are deployed
      project_id: my-gcp-project # Optional: will use default from GCP auth if not specified
      # credentials_path: /path/to/service-account.json  # Optional: overrides GOOGLE_APPLICATION_CREDENTIALS
  models:
    - name: my-gemini-pro
      provider: googlevertex
      model: gemini-1.5-pro
      temperature: 0.1
      max_tokens: 8192
      use_cache: true
    - name: my-gemini-flash
      provider: googlevertex
      model: gemini-1.5-flash
      temperature: 0.2
      max_tokens: 8192
      use_cache: true
```

:::

### Troubleshooting

#### Authentication Issues

If you encounter authentication errors:

1. Verify your service account has the necessary permissions:

   - `Vertex AI User` role
   - `AI Platform Developer` role (for older projects)

2. Check that the Vertex AI API is enabled for your project:

   ```bash
   gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
   ```

3. Verify your credentials are working:
   ```bash
   gcloud auth application-default print-access-token
   ```

#### Region/Location Issues

- Ensure the `location` in your config matches where your models are available
- Some models may not be available in all regions
- Use `gcloud ai models list --region=YOUR_REGION` to see available models

#### Project ID Issues

- If `project_id` is not specified in config, AWA will use the default project from your GCP authentication
- Verify your default project: `gcloud config get-value project`
- Set a default project: `gcloud config set project YOUR_PROJECT_ID`
