#### Configure LiteLLM with GitHub Copilot models

Create or update `litellm_config.yaml`:

:::code-group

```yaml [litellm_config.yaml]
model_list:
  - model_name: ghcopilot/claude-sonnet-4.5
    litellm_params:
      model: github_copilot/claude-sonnet-4.5
      extra_headers:
        Editor-Version: "vscode/1.99.3"
        Editor-Plugin-Version: "copilot-chat/0.26.7"
        Copilot-Integration-Id: "vscode-chat"
        User-Agent: "GitHubCopilotChat/0.26.7"

  - model_name: ghcopilot/gpt-4o
    litellm_params:
      model: github_copilot/gpt-4o
      extra_headers:
        Editor-Version: "vscode/1.99.3"
        Editor-Plugin-Version: "copilot-chat/0.26.7"
        Copilot-Integration-Id: "vscode-chat"
        User-Agent: "GitHubCopilotChat/0.26.7"

litellm_settings:
  drop_params: true
  success_callback: ["langfuse"]
```

:::

:::info VSCode Headers
The `extra_headers` simulate a VSCode editor environment, which is required for GitHub Copilot API compatibility.
:::

#### Start LiteLLM with Docker Compose

Start the LiteLLM proxy service:

```bash
make start-litellm
# Or manually:
docker compose -f docker-compose.awa-supporting.yml up -d
```

#### Authenticate with GitHub Copilot (OAuth Device Flow)

When you first start LiteLLM with GitHub Copilot models configured, you'll need to authenticate:

1. **Check the LiteLLM logs** to get the device authentication URL:
   ```bash
   docker compose -f docker-compose.awa-supporting.yml logs -f litellm
   ```

2. **Look for output similar to**:
   ```
   Please visit: https://github.com/login/device
   And enter code: XXXX-XXXX
   ```

3. **Complete the OAuth flow**:
   - Open the URL in your browser
   - Enter the device code shown in the logs
   - Authorize the application

4. **Token persistence**: The OAuth token is stored in `~/.awa` on your host machine, which is mounted into the LiteLLM container at `/root/.awa`. This means:
   - The token persists across container restarts
   - LiteLLM can automatically refresh the token when needed
   - You only need to authenticate once

:::warning Token Storage
Make sure the LiteLLM container has the `~/.awa` directory mounted. This is configured in `docker-compose.awa-supporting.yml`:

```yaml
volumes:
  - $HOME/.awa:/root/.awa:ro
```
:::

#### Configure AWA to use LiteLLM proxy

Update your `config.yaml`:

:::code-group

```yaml [config.yaml]
llm:
  providers:
    lite_llm:
      base_url: http://localhost:4002
      api_key: sk-awa

  models:
    - name: claude-sonnet-4.5
      provider: LiteLLM
      model: ghcopilot/claude-sonnet-4.5
      temperature: 0.1
      max_tokens: 32000
      use_cache: true
```

:::

#### Verify the setup

Once LiteLLM is running, you can test the GitHub Copilot models using the LiteLLM playground:

1. Open the LiteLLM UI at [http://localhost:4002](http://localhost:4002)
2. Select one of the `ghcopilot/` models from the dropdown
3. Send a test message to verify the integration is working
