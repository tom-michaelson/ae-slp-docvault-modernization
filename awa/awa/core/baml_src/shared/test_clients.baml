client<llm> OpenAIWithFinishReasonError {
  provider openai
  options {
    api_key env.OPENAI_API_KEY
    model "gpt-4.1"
    max_tokens 100
    temperature 0.0
    finish_reason_allow_list ["stop"]
  }
}
client<llm> GithubCopilotSonnet4 {
  provider openai-generic
  options {
    base_url "https://api.githubcopilot.com"
    api_key "tid=11b4f56371462999ba2c24c777f8db2c;ol=7afce0c5471894f9e467c7a9ae681dda;exp=1759442193;sku=copilot_for_business_seat_quota;proxy-ep=proxy.business.githubcopilot.com;st=dotcom;ssc=1;chat=1;sn=1;malfil=1;editor_preview_features=1;agent_mode=1;mcp=1;ccr=1;8kp=1;ip=73.77.17.122;asn=AS7922:ff43d25dcadf4500263d3cc90d9c67ac0655738e15bb6d585ffb8886dca4d282"
    model "claude-sonnet-4"
    max_tokens 32000
    temperature 0.1
    headers {
      "User-Agent" "GitHubCopilotChat/0.26.7"
      "Editor-Version" "vscode/1.99.3"
      "Editor-Plugin-Version" "copilot-chat/0.26.7"
      "Copilot-Integration-Id" "vscode-chat"
    }
  }
}

client<llm> BedrockClaude37 {
  provider aws-bedrock
  options {
    region "us-east-1"
    profile "slalomdev"
    model "arn:aws:bedrock:us-east-1:577638363028:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    inference_configuration {
        max_tokens 100
        temperature 0.0
    }
  }
}

client<llm> GoogleVertexGemini {
  provider vertex-ai
  options {
    model "gemini-1.5-pro"
    location "us-central1"
  }
}

client<llm> LiteLLM {
  provider "openai-generic"
  options {
    base_url "http://0.0.0.0:4002"
    api_key sk-awa
    model "gpt-4.1"
  }
}
