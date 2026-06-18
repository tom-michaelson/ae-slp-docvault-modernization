client<llm> OpenAIWithFinishReasonError {
  provider openai
  options {
    api_key env.OPENAI_API_KEY
    model "gpt-4.1"
    max_completion_tokens 100
    temperature 0.0
    finish_reason_allow_list ["stop"]
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

client<llm> LiteLLM {
  provider "openai-generic"
  options {
    base_url "http://0.0.0.0:4002"
    api_key sk-awa
    model "gpt-4.1"
  }
}
