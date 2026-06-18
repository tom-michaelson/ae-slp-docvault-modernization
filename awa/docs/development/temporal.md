# Temporal

AWA's workflow execution engin is [Temporal](https://temporal.io/).

Read more about the decision to use Temporal in [Architecture](/introduction/architecture).

:::warning How deep do I need to go?
To get up and running with AWA, you don't need to know much about Temporal. You should not need to leverage the resources on this page until you're ready to build your own complex workflows.

At that point, how deep you go is up to you. Our suggestion is to at least familiarize yourself with Temporal's core features (the concepts covered in the **Temporal Fundamentals** tutorial series linked below), and only go deeper than that as needed.

Note that while AWA uses Temporal, Temporal itself is an open source project that is useful in other scenarios as well. Durable workflows are a powerful tool, and could be useful outside the context of their use in AWA.
:::

:::danger Temporal Cloud is Not Required
Be careful not to confuse **Temporal** (the open source durable workflow engine) with **Temporal Cloud** (the hosted service sold by the Temporal team). Temporal Cloud is compatible with AWA, but it is in no way required. The entire AWA stack is open source and can run locally or in any cloud provider.
:::

## Learn

The resources below will help you understand the basics of Temporal.

### Why Workflows?

- [Agents are just workflows, really](https://www.amplifypartners.com/blog-posts/agents-are-just-workflows-really)
- [The fallacy of the graph: Why your next agentic workflow should be code, not a diagram](https://temporal.io/blog/the-fallacy-of-the-graph-why-your-next-workflow-should-be-code-not-a-diagram)

### Temporal + Agents

### Official Docs: Temporal Basics

The best place to learn is the official documentation: [Temporal Documentation](https://docs.temporal.io/).

Here you'll find some great resources:

- [Why Temporal?](https://docs.temporal.io/evaluate/why-temporal)
- [Understanding Temporal](https://docs.temporal.io/evaluate/understanding-temporal)
- Feature explanations, including:
  - [Core application](https://docs.temporal.io/evaluate/development-production-features/core-application)
  - [Composability](https://docs.temporal.io/evaluate/development-production-features/throughput-composability)
  - [Workflow message passing](https://docs.temporal.io/evaluate/development-production-features/workflow-message-passing)
  - [Debugging](https://docs.temporal.io/evaluate/development-production-features/debugging)
  - [Observability](https://docs.temporal.io/evaluate/development-production-features/observability)
  - [Schedules](https://docs.temporal.io/evaluate/development-production-features/schedules)
- SDK guides for [Python](https://docs.temporal.io/develop/python), [.NET](https://docs.temporal.io/develop/dotnet), [Java](https://docs.temporal.io/develop/java), [TypeScript](https://docs.temporal.io/develop/typescript), [Go](https://docs.temporal.io/develop/go), [PHP](https://docs.temporal.io/develop/php), and [Ruby](https://github.com/temporalio/sdk-ruby)
- [Courses](https://learn.temporal.io/courses/) including [Temporal 101: Introducing the Temporal Platform](https://learn.temporal.io/courses/temporal_101/)
- Project-based tutorials in [Go](https://learn.temporal.io/tutorials/go/), [Java](https://learn.temporal.io/tutorials/java/), [TypeScript](https://learn.temporal.io/tutorials/typescript/), [Python](https://learn.temporal.io/tutorials/python/), and [PHP](https://learn.temporal.io/tutorials/php/)
- Guides for [troubleshooting](https://docs.temporal.io/troubleshooting/) common issues
- [Encyclopedia](https://docs.temporal.io/encyclopedia/) of Temporal concepts and terms
- And many more...

### Introduction

- **Temporal in 7 Minutes - the TL;DR Intro** - [YouTube Video](https://youtu.be/2HjnQlnA5eY?si=RxQV0ZeBfg9SfIok) (or [2 Minutes](https://www.youtube.com/watch?v=f-18XztyN6c))
- **Getting to Know Temporal** - [YouTube Video](https://youtu.be/wIpz4ioK0gI?si=xx15ibdHGs2PN6G4)
- **Temporal Fundamentals** Tutorial Series
  - [Part I: Basics](https://keithtenzer.com/temporal/Temporal_Fundamentals_Basics/)
  - [Part II: Concepts](https://keithtenzer.com/temporal/Temporal_Fundamentals_Concepts/)
  - [Part III: Timeouts](https://keithtenzer.com/temporal/Temporal_Fundamentals_Timeouts/)
  - [Part IV: Workflows](https://keithtenzer.com/temporal/Temporal_Fundamentals_Workflows/)
  - [Part V: Workflow Patterns](https://keithtenzer.com/temporal/Temporal_Fundamentals_Workflow_Patterns/)
  - [Part VI: Workers](https://keithtenzer.com/temporal/Temporal_Fundamentals_Workers/)

### Temporal + Agents

- [How To Build a Durable AI Agent with Temporal and Python](https://learn.temporal.io/tutorials/ai/durable-ai-agent/)
- [Durable Execution meets AI: Why Temporal is the perfect foundation for AI agent and generative AI applications](https://temporal.io/blog/durable-execution-meets-ai-why-temporal-is-the-perfect-foundation-for-ai)
- [Amazon Bedrock with Temporal: Rock Solid](https://temporal.io/blog/amazon-bedrock-with-temporal-rock-solid)
- [Building production-ready generative AI: How Temporal supercharges Google's Gemini and Veo](https://temporal.io/blog/build-prod-ready-gen-ai-temporal-gemini-veo)
- [Durable MCP: How to give agentic systems superpowers](https://temporal.io/blog/durable-mcp-how-to-give-agentic-systems-superpowers)
- **Build an AI Agent with Temporal** - [YouTube Video](https://youtu.be/iPwR6zWoRGo?si=7KheYH2JPVc92gjW)
- **Temporal Polyglot Microservices Orchestration** - [YouTube Video](https://youtu.be/LSXP_o6sTic?si=B6ly3rJBexVuBcc1)
- **Case Studies**
  - Managing AI Workflows at Descript with Temporal - [YouTube Video](https://youtu.be/4EaZZhmk9zg?si=Es2t-DRT4Vqk45DC)
  - How Dubber uses Temporal to Deliver Conversation Intelligence at Scale - [YouTube Video](https://youtu.be/6hJlRJmguKA?si=tGVCUkzDvZYnD7AK)
  - [End-to-end AI workflows with Temporal at Descript](https://temporal.io/resources/case-studies/descript)

## Other Resources

- [Importing Activities for a Temporal Workflow in Python](https://www.danielcorin.com/til/temporal/defining-workflows-in-python/)
- [A Developer’s Guide to Building Scalable AI: Workflows vs Agents](https://towardsdatascience.com/a-developers-guide-to-building-scalable-ai-workflows-vs-agents/)
- [Most companies building AI agents today skip the most important step: Designing the Standard Operating Procedure (SOP)](https://www.linkedin.com/posts/armand-ruiz_most-companies-building-ai-agents-today-skip-activity-7349754709009715200-eNRK/)
