---
title: Intro
---

# Welcome to AWA!

```bash
+-------------------------------------------+
|                                           |
|      /\\      \            /      /\\     |
|     /  \\      \    /\    /      /  \\    |
|    /....\\      \  /  \  /      /....\\   |
|   /  ..  \\      \/    \/      /  ..  \\  |
|  /__/  \__\\ Agentic Workflow /__/  \__\\ |
|                Accelerator                |
+-------------------------------------------+
```

## What is AWA?

AWA is an accelerator for building agentic workflows. The goal is to provide a toolbox Slalom teams can use to ramp up and deliver value quickly.

AWA can be used as the foundation of either a deliverable workflow (**agentic workflow as the product**) or agentic workflows to assist with a deliverable (**agentic workflow as a tool**).

**Easy. Compabible. Useful.** See our [Guiding Principles](/introduction/guiding-principles) for more details on the philosophy behind AWA.

- **Conceptually**, AWA provides a set of building blocks out of the box that can be used directly, remixed, and built on top of to deliver complex agentic workflows.
- **Literally**, AWA is a Python CLI and starter solution for building agentic workflows with the Temporal workflow engine. AWA comes with an API for integration into other applications and a basic UI for initiating and monitoring workflows (including Temporal's built-in UI). You build workflows as Temporal workflows using any of Temporal's SDKs (Python, TypeScript, .NET, Java, Go, or PHP). See our [Architecture](/introduction/architecture) page for more details.

**Why Workflows?**

- [Agents are just workflows, really](https://www.amplifypartners.com/blog-posts/agents-are-just-workflows-really)
- [The fallacy of the graph: Why your next agentic workflow should be code, not a diagram](https://temporal.io/blog/the-fallacy-of-the-graph-why-your-next-workflow-should-be-code-not-a-diagram)

<div style="max-width: 640px"><div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;"><iframe src="https://twodegrees1.sharepoint.com/teams/AWA/_layouts/15/embed.aspx?UniqueId=ed1f8b35-282b-41e7-bfe4-7a1cd96dcbde&embed=%7B%22hvm%22%3Atrue%2C%22ust%22%3Afalse%7D&referrer=StreamWebApp&referrerScenario=EmbedDialog.Create" width="640" height="360" frameborder="0" scrolling="no" allowfullscreen title="MVP Launch Demo (AE Weekly Demo Series) 20250709.mp4" style="border:none; position: absolute; top: 0; left: 0; right: 0; bottom: 0; height: 100%; max-width: 100%;"></iframe></div></div>

:::info Early Days
This project is in early development and actively evolving. Expect rough edges, breaking changes, and incomplete documentation. But also expect rapid iteration and responsiveness to feedback. Please submit issues and/or reach out to us on Slack in the #ae-awa channel.
:::

## What can I do with AWA?

**Automate anything**, your way. AWA gives you the power to **build your own agents and agentic workflows**. Turn any process, program, or system agentic. From pre-commit checks, code reviews, and writing docs, to running customer-facing agentic workflows in production. You define what your agentic workflows do, when they run, what tools they use, and how they respond &mdash; **all in code**.

**Key Capabilities**

- **Run Universally**: Deploy on any OS (without Docker), any cloud provider (or local), with any LLM, and in any development language. Accelerate in even the most restrictive environments.
- **Define Workflows in Code**: No complicated YAML DSL to learn &mdash; build in your language of choice with the full flexibility and testability of custom code, and leverage a large library of reusable building blocks.
- **Iterate Rapidly**: Resume in-progress workflows, debug end-to-end, and run + test all prompts directly in your IDE to iterate quickly.
- **Trigger and Interact Flexibly**: Trigger workflows from CLI locally or in CI/CD pipelines, from event-driven API hooks, from an MCP-enabled IDE, or from a web UI.
- **Run Durable, Observable Workflows**: Build workflows that run for hours, days, weeks, months, or years, and automatically resume from crashes and failures. Seamlessly time-travel to previous workflow stages. Monitor progress through a detailed low-level tracing UI and Langfuse integration.
- **Jumpstart with Recipes**: Rich set of examples and demos are available in our [Cookbook](/cookbook/) to get you started and give you ideas of what is possible.

AWA gives you everything you need to easily build, run, and scale AI agentic workflows, your way. Build. Customize. Automate.

See [Use Cases](/introduction/use-cases) for ideas on what you can do with AWA.

## Should I use AWA?

Good question!

If you are delivering an agent or agentic workflow as a client product deliverable (**agentic workflow as the product**), AWA is a great choice as a foundation. See [Alternatives](/introduction/alternatives) to see some of the advantages of AWA over other agent frameworks.

The question gets more complicated if you are building an agentic workflow to assist with a deliverable, code or otherwise (**agentic workflow as a tool**). In this case, you should first ask: do I need a formal agentic workflow?

First, think about the problem you are trying to solve. Can your problem be solved with a single prompt or simple chat? Can an off-the-shelf agent (like GitHub Copilot Agent or Claude Code) do what you need with good enough instructions? Start simple, and move to a formalized agentic workflow when necessary.

<img src="/images/problem-solving-with-ai.jpg" alt="Problem Solving with AI" />

A related mental model to help think through how this can apply to your team is the [AE Maturity Curve](https://slalom.atlassian.net/wiki/spaces/AccEng/pages/5169971308/AE+Maturity+Curve), which can be summarized as:

- Stage 1: **Enable** - Grant Access to Agentic Tools
- Stage 2: **Exploit** - Maximize Leverage of Agentic Tools with a Structured Context Library
- Stage 3: **Experiment** - Explore Manual Agentic Workflows
- Stage 4: **Encode** - Build Formal Agentic Workflows _←AWA fits here_

Jumping directly to Stage 4 before you or your team has moved through stages 1-3 can lead to wasted effort and frustration, while staying in Stage 3 for too long can lead to inconsistency and squandered leverage.

## How do I use AWA?

AWA can be used as the foundation of either a deliverable workflow (**agentic workflow as the product**) or agentic workflows to assist with a deliverable (**agentic workflow as a tool**).

See our [Use Cases](/introduction/use-cases) for ideas on how you can use AWA.

See our [Quick Start](/introduction/quick-start) guide for more details on how to get started.

AWA supports Mac, Windows, Linux, and Docker (Docker is not required). AWA can be run locally, or be deployed to any cloud provider that supports containers (AWS, Azure, GCP, etc.).

## Who can I talk to about AWA?

Find us on Slack in the [#ae-awa](https://grid-slalom.enterprise.slack.com/archives/C094ZRQC6P6) channel, or reach out to [David Lawton](mailto:david.lawton@slalom.com) or [Ryan Henderson](mailto:ryan.henderson@slalom.com) directly to start a conversation.
