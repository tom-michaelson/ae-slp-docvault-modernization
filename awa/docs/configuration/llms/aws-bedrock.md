# AWS Bedrock

## Get Credentials

- To request an AWS account, refer to the [https://cloud.slalom.com](https://cloud.slalom.com/) and  [Fill out an AWS Innovation Lab request form article.](https://slalom.service-now.com/kb_view.do?sysparm_article=KB0015056)

- AWS Profile ID. Refer to Slalom [AWS SSO Setup Docs](https://twodegrees1.sharepoint.com/:w:/r/teams/InnovationLabOwners/Shared%20Documents/General/AWS%20CLI%20using%20Azure%20SSO%20Setup%20Instructions.docx?d=we3bd8c341cf442e6aece05c37e8be59a&csf=1&web=1&e=JSlQ7x) to setup AWS profile for Slalom Innovation Labs

## AWS Bedrock Configuration

### 1. Set environment variables

Set your environment variables in your `.env` file.

Refer to Slalom [AWS SSO Setup Docs](https://twodegrees1.sharepoint.com/:w:/r/teams/InnovationLabOwners/Shared%20Documents/General/AWS%20CLI%20using%20Azure%20SSO%20Setup%20Instructions.docx?d=we3bd8c341cf442e6aece05c37e8be59a&csf=1&web=1&e=JSlQ7x) to setup AWS profile for Slalom Innovation Labs.

:::code-group

```sh [.env]
#------------------------------#
#           AWS                #
#------------------------------#
AWS_REGION=YOUR_AWS_REGION

# Either use aprofile (use this for Slalom SSO)
AWS_PROFILE=YOUR_AWS_PROFILE

# Or use an access key
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
```

:::

### 2. Configure models in config.yaml

Set up one or more models in `config.yaml`.

:::warning Model Format
Depending on the account and model you are using, you may or may not need to use the full ARN format for your inference profile (model name). Try first with just the Inference Profile ID, and if that does not work, try the full ARN.

- **Inference Profile ARN**: `arn:aws:bedrock:<AWS Region>:<AWS Account ID>:inference-profile/<Model Name>`
- **Inference Profile ID**: `us.anthropic.claude-sonnet-4-20250514-v1:0`

You can find the values enabled for your account in the console here: [Amazon Bedrock / Infer / Cross-region inference](https://us-east-1.console.aws.amazon.com/bedrock/home#/inference-profiles).

:::

:::code-group

```yaml [config.yaml]
llm:
  default_model: my-bedrock-claude-sonnet-4
  # ...
  providers:
    # Nothing is needed in `providers` for AWS Bedrock
    # ...
  models:
    - name: my-bedrock-claude-sonnet-4
      provider: awsbedrock
      model: arn:aws:bedrock:us-east-1:662450577015:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0
      temperature: 0.1
      max_tokens: 32000
      use_cache: true
```

:::

### Leapp for SSO

:::danger Leapp may not work for Slalom Innovation Labs
At this time, Leapp does not work with Slalom Innovation Lab accounts. We're not sure why, but for now you'll need to follow the steps outlined in [AWS SSO Setup Docs](https://twodegrees1.sharepoint.com/:w:/r/teams/InnovationLabOwners/Shared%20Documents/General/AWS%20CLI%20using%20Azure%20SSO%20Setup%20Instructions.docx?d=we3bd8c341cf442e6aece05c37e8be59a&csf=1&web=1&e=JSlQ7x).
:::

<!--@include: /../../.shared/leapp.md -->
