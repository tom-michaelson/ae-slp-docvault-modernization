# Alternatives

AWA is not the only tool available! There are a lot of agentic frameworks, and situations vary widely. So you should always evaluate the points below in the context of your situation. AWA may not be the best choice for all situations.

:::warning Take it with a grain of salt
Please do not rely on this document as a comprehensive or authoritative review of any specific tool, or an exhaustive list of all tools available. If you are familiar with a tool and spot an inaccuracy, or notice a tool that is missing, please let us know so we can update this guide!

We have tried our best not to fall into the trap...

<img src="/images/competitor-comparison.jpg" alt="Competitor Comparisons" width="300"/>
:::

## Why Workflows?

The articles below outline the reasons "workflows" as an abstraction are a good fit for agentic applications.

- [Agents are just workflows, really](https://www.amplifypartners.com/blog-posts/agents-are-just-workflows-really)
- [The fallacy of the graph: Why your next agentic workflow should be code, not a diagram](https://temporal.io/blog/the-fallacy-of-the-graph-why-your-next-workflow-should-be-code-not-a-diagram)

## Benefits of AWA

Below are some of the benefits of AWA compared to other agentic frameworks.

- **Full low-level prompt control**: Many agentic frameworks obscure the actual prompts being executed. This works great for demos and POCs, but when you need to go deep on improving the reliability of a workflow, having full control over the entire prompt is a powerful capability.
- **Workflows, not graphs**: Graphs can be used to model nearly any program, and they have become popular for agents, but they come with a learning curve and often have [many shortcomings](https://temporal.io/blog/the-fallacy-of-the-graph-why-your-next-workflow-should-be-code-not-a-diagram). AWA (using Temporal) allows you to write agents and agentic workflows in normal control flow logic without thinking about nodes or edges. Opinions vary, but we generally find this to be easier to design, reason about, debug, and test.
- **Polyglot architecture**: Temporal has SDKs in many languages, and you can build on top of AWA in any of them: Python, TypeScript, C#, Java, Go, PHP. This means we can meet client teams where they are, rather than pushing them into Python or Node where the don't have much in-house expertise.
- **Reusable toolbox**: A large (and growing) set of child workflows and activities let you start fast and move quickly.
- **Robust durable workflow platform**: AWA uses Temporal as its core workflow engine, providing out-of-the-box durable workflows with a platform already trusted across the industry. Durability, resiliency, and observability come built-in.
- **BAML integration**: BAML is a powerful tool that allows your team to iterate quickly on prompts (which are the core of any agentic system) with a flexible template syntax and Playground VS Code extension, and AWA integrates with it out of the box.
- **Integration of best-of-breed CLI agents**: A simple agent loop is easy to build, and AWA allows for this as well. But AWA also offers an easy way to orchestrate and parallelize CLI agents (like Claude Code, Codex CLI, OpenCode, Goose).
- **Platform-independent**: Some frameworks are closely tied to specific platforms or providers. AWA is usable with any LLM, any cloud (or local via CLI or MCP).
- **Maximum compatibility**: Built to run on Windows, Mac, or Linux, all without Docker (but also with Docker if preferred). Run and manage workflows via CLI, API, MCP, and UI.
- **Flexible integration with any LLM APIs**: Client environment only allows access to one specific LLM API? No problem, AWA can talk to a virtually any LLM API (including GitHub Copilot's API directly).
- **Flexible workflow orchestration engine**: AWA's workflow orchestration engine can be used both as a black box or customized as needed. You can just write your own client workers / workflows / activities, or go deep and customize the underlying AWA core if needed (not true or easy for some existing frameworks).

## Related Tools

Certain categories of tools will be out of scope for this guide, primarily because they target categorically different use cases than AWA. There is some overlap, but generally speaking the tools that are out of scope would not be considered direct alternatives to a tool like AWA.

### Agentic Code-based Frameworks

These are the closest alternatives to compare to AWA.

- [LangGraph](https://www.langchain.com/langgraph)
- [LlamaIndex](https://www.llamaindex.ai/)
- [Semantic Kernel](https://github.com/microsoft/semantic-kernel)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) (now supported [directly in Temporal and AWA](/usage/features/openai-agents-sdk))
- [Google ADK (Agent Development Kit)](https://google.github.io/adk-docs/)
- [AWS Strands Agents SDK](https://strandsagents.com/latest/)
- [Agno](https://www.agno.com/)
- [CrewAI](https://www.crewai.com/)
- [Mastra](https://mastra.ai/)
- [Autogen](https://microsoft.github.io/autogen/stable//index.html)
- [BrainyFlow](https://github.com/zvictor/BrainyFlow)
- [PocketFlow](https://github.com/The-Pocket/PocketFlow/tree/main)

### Visual Workflow Builders

- [n8n](https://n8n.io/)
- [Dify](https://dify.ai/)
- [Rivet](https://rivet.ironcladapp.com/)
- [Make](https://www.make.com/)

### Hosted Agent Platforms

- [Microsoft Copilot Studio](https://www.microsoft.com/en-us/microsoft-copilot/microsoft-copilot-studio)
- [Dust](https://dust.tt/)
- [Lindy](https://lindy.ai/)
- [Writer](https://www.writer.com/)

### Inner-Loop Coding Agents

#### Agentic IDEs

- [Github Copilot (VS Code)](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)
- [Cursor](https://cursor.com/)
- [Windsurf](https://windsurf.com/)
- [Zed](https://zed.dev/)

#### CLI Agents

- [Anthropic Claude Code](https://www.anthropic.com/claude-code)
- [OpenAI Codex CLI](https://github.com/openai/codex)
- [Google Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [Block Goose](https://github.com/block/goose)
- [Plandex](https://plandex.ai/)
- [OpenCode](https://github.com/sst/opencode)
- [Qodo Command](https://www.qodo.ai/products/qodo-command/)

### Outer-Loop Coding Agents & Platforms

- [Factory](https://factory.dev/)
- [Devin](https://devin.ai/)
- [OpenAI Codex (Platform)](https://chatgpt.com/codex)
- [Google Jules](https://jules.google.com/)
- [Github Copilot Agent (Platform)](https://github.com/features/copilot)
