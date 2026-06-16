# SDK Usage Guide

AWA comes with SDKs that make it easier to leverage the set of reusable child workflows and activities within your own workflows. The AWA SDK is a wrapper around the native Temporal SDK with helper functions and models.

Using the AWA SDK is **not required**, it is provided as an optional convenience. AWA SDKs are not available in every language supported by AWA (meaning all languages supported by Temporal), but we hope to support all languages in the future.

Details on how AWA's SDKs are generated and maintained can be found [here](/contributing/sdk/generation.md).

## Access

AWA SDKs are published to Slalom's official package repositories in AWS CodeArtifact. Everyone at Slalom has access to these repositories via SSO authentication.

<!--@include: /../../.shared/sdk-client-usage.md -->

:::info Slalom Package Repositories
The Slalom package repositories used for the AWA SDKs are relatively new, so this may be your first experience using them. You can read more about them in [Confluence](https://slalom.atlassian.net/wiki/spaces/EAAS/pages/5215682561/CodeArtifact), or view the underlying [repository](https://bitbucket.org/slalom-consulting/slalom-codeartifact/src/main/).
:::

## Available SDKs

:::danger Prerequisites
Be sure to read about prerequisites below before attempting to use the SDKs.
:::

- **[Python SDK](./python.md)**: `awa-client`
- **[C# SDK](./csharp.md)**: `Awa.Client`

:::warning I thought AWA was polyglot? What about other languages?
Be careful not to confuse the **AWA SDK** with the **Temporal SDK**. The AWA SDK is a convenience wrapper around the Temporal SDK for the reusable child workflows and activities within AWA, but it is **not required** to use AWA &mdash; all AWA features can be used through the Temporal SDK which is available in Python, TypeScript, C#, Java, Go, and PHP.
:::

## Prerequisites

Before using AWA SDKs, ensure you have:

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed and configured
- Language-specific package manager installed (NuGet/dotnet for C#, pip for Python)
- AWS Profile credentials configured via SSO (see below)

### Leapp for AWS Profile SSO

For consistency, we recomment using the following profile name:

**Profile Name**: `slalom-codeartifact`

:::warning Alternative Instructions
Please see the alternative instructions in [Confluence](https://slalom.atlassian.net/wiki/spaces/EAAS/pages/5215682561/CodeArtifact) if you cannot get Leapp to work for you.
:::

For accessing the official Slalom AWS CodeArtifact repositories, everyone at Slalom has access to the following IAM accounts. Use this information with the instructions below to configure Leapp.

- **Account ID**: `825505919920`
- **Role Name**: `codeartifact-readonly`
- **Azure App ID**: `724f34aa-ee19-43f1-b7a2-fb3c51abc3a2`

#### Configure Leapp

Then in Leapp, configure an AWS Session with the following parameters:

- Named profile: `slalom-codeartifact`
- Aws Region: `us-east-1`
- Role ARN: `arn:aws:iam::825505919920:role/codeartifact-readonly`
- SAML 2.0 Url: `https://launcher.myapps.microsoft.com/api/signin/24f34aa-ee19-43f1-b7a2-fb3c51abc3a2?tenantId=9ca75128-a244-4596-877b-f24828e476e2`
- Identity Provider: `arn:aws:iam::825505919920:saml-provider/slalomazure`
