# Guiding Principles

**Easy. Compatible. Useful.** Review our guiding principles below. Each core principle is followed by a list of specific actionable tactics we're using to achieve it.

## Easy

Problem solving with agentic workflows requires a new architectural mindset. The tooling to support this work should be as simple to use as possible. AWA must be **easy to understand, quick to get started with, and simple to use**.

- **Clear, Well-Organized Documentation**: This documentation site is intended to provide a quick path to getting started as well as a in-depth reference for advanced usage.
- **Rapid, Low-Friction Onboarding**: AWA's onboarding story is focused on simplicity and speed to ensure users can get up and running quickly.
- **Universal Accessibility**: AWA can be accessed and used by anyone in Slalom. There is no access gate beyond standard SSO.
- **Sensible Defaults**: Favor convention over configuration, and require explicit configuration only when necessary.
- **Clarity vs. Alternatives (Internal/External)**: AWA has a clear and distinct value proposition compared to internal/external alternatives, and AWA's documentation provides clear direction on when to use AWA vs. internal/external alternatives.
- **Stable with Thorough Tests**: Core features as well as reusable activities and workflows have comprehensive automated tests.
- **Multitude of Rich Examples**: Rich and wide-ranging set of complete out-of-the-box runnable examples help users understand what is possible.
- **No Licensing or IP Complications**: AWA is a code accelerator, which means it can be used directly in client projects and left behind. It's also built on top of 100% OSS tooling, which means no licensing or purchase decisions are required by clients before adoption.

## Compatible

Our clients have a wide array of environments and constraints. Our projects have a wide range of requirements and use cases. AWA must be **maximally compatible to meet (almost) any need**.

- **Any OS without Docker**: AWA's core is compatible with Windows, Mac, and Linux with no need for Docker containers. This ensures it can be used in even the most restrictive client environments.
- **Local First, Cloud Native**: Built on Temporal, AWA is built to run locally just as easily as in the cloud. Even our CI/CD pipelines are local-first and runnable in any hosted platform (GitHub Actions, Bitbucket Pipelines, Jenkins, etc.), built using [Dagger](https://dagger.io/).
- **Any Cloud Provider**: AWA is cloud-agnostic, deployable to any cloud provider. Our [deployment blueprints](/deployment/) provide a starting point for each major cloud provider.
- **Any LLM**: AWA natively supports OpenAI, Azure OpenAI, Bedrock, and the LiteLLM Proxy. This means even without LiteLLM, AWA supports our clients' most prominent platforms of choice. And with LiteLLM, [virtually every LLM platform](https://docs.litellm.ai/docs/providers) is supported.
- **Any Development Language (almost)**: AWA's core is written in Python, but Temporal provides SDKs in every major language including Python, TypeScript, .NET, Java, Go, and even PHP. Temporal supports polyglot deployments by default, which means you can build your app in your language of choice while still leveraging all the accelerating building blocks in AWA core.
- **Plug and Play Flexibility**: AWA can be used as a standalone local CLI/UI tool, as a scriptable CLI in deployed pipelines, as a web API service within a larger system, as an [MCP server](/usage/mcp), or as an [A2A agent](/usage/a2a). AWA also makes it easy to leverage other MCP servers and external APIs.

## Useful

Accelerator means _acceleration_. Ease and compatibility mean nothing if the tool is not useful. AWA must be **powerful out of the box, with a large set of reusable components, ready-to-demo examples, and a clear path from demo to production**.

- **Powerful Out of the Box**: Use any of our pre-baked recipes from the [Cookbook](/cookbook/) to get value immediately. Extend and build your own workflows to match your specific use cases.
- **Large Library of Reusable Components**: Wide array of reusable workflow activities and child workflows means less leg work to construct complex workflows from scratch.
- **Scales from Demo to Production**: More than a toy, AWA is built to scale to the most complex production agentic workflow use cases. From single one-off local workflows to high-scale enterprise use cases, AWA gets you there faster. Using Temporal as the foundation means reliability and cloud scalability out of the box.
- **Client Demos Ready-to-Go**: Part of the value proposition is making it easy to sell Slalom's agentic workflow capabilities to clients, and a big part of that is having a set of ready-to-demo examples that can be used to showcase the capabilities of our teams leveraging AWA.
- **We use AWA to build AWA**: We eat our own dogfood &mdash; the AWA team uses many AWA workflows in the development of AWA itself. These workflows can be viewed in the [Cookbook](/cookbook/).
