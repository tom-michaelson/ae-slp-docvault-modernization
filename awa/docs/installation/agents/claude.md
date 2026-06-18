# Agent - Claude Code

This document provides instructions on how to install and configure the Claude SWE Code for use with AWA.

For detailed information, refer to the official [Claude Code Overview](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview).

## Installation

See the [official docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) for information about how to install Claude Code on your system.

## Using AWS Bedrock

You can configure Claude Code to utilize AWS Bedrock as the backend instead of directly using Anthropic's API. This requires setting specific environment variables.

**Required Steps:**

1. **Configure AWS Credentials**: Ensure your AWS credentials are configured correctly. This typically involves running `aws configure` or setting environment variables like `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`. Refer to the [AWS documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) for details.
2. **Enable Bedrock Usage**: Set the following environment variable to instruct Claude Code to use Bedrock:

   ```bash
   # Claude code variables to use bedrock
   CLAUDE_CODE_USE_BEDROCK=1
   ANTHROPIC_MODEL='us.anthropic.claude-3-7-sonnet-20250219-v1:0'
   ANTHROPIC_SMALL_FAST_MODEL='us.anthropic.claude-3-5-haiku-20241022-v1:0'
   DISABLE_PROMPT_CACHING=1
   ```

3. **Ensure Model Access**: Verify that your AWS account has access to both `Claude 3.7 Sonnet` and `Claude 3.5 Haiku` models within the desired AWS region(s) in Bedrock.

**Setting Environment Variables:**

- **For AWA Integration**: Add the `CLAUDE_CODE_USE_BEDROCK` variable (and any other necessary AWS variables) to your `.env` file. You can use `.env.example` as a template.
- **For Direct Terminal Use**: To use Claude Code directly in your terminal with Bedrock, add the following line to your shell configuration file (e.g., `~/.zshrc`, `~/.bashrc`):

  ```bash
  CLAUDE_CODE_USE_BEDROCK=1
  ANTHROPIC_MODEL='us.anthropic.claude-sonnet-4-20250514-v1:0'
  ANTHROPIC_SMALL_FAST_MODEL='us.anthropic.claude-3-5-haiku-20241022-v1:0'
  # DISABLE_PROMPT_CACHING=1
  ```

  Remember to source your configuration file (e.g., `source ~/.zshrc`) or open a new terminal session after making changes.

Refer to the official [Claude Code documentation on using third-party APIs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#use-with-third-party-apis) for more details.
