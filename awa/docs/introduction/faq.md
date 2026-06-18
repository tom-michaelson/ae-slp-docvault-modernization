# FAQs

## General

### How long does it take to get started with AWA?

Most developers can get AWA running locally within 15-30 minutes using our Quick Start guide. Building your first workflow typically takes 1-2 hours, depending on complexity.

### What LLM providers does AWA support?

AWA natively supports OpenAI, Azure OpenAI, AWS Bedrock, GitHub Copilot, and any provider accessible through LiteLLM (which includes virtually every major LLM provider). Configuration is handled through environment variables and config.yaml.

See [Configuration - LLMs](/configuration/llms/) for complete details.

### What CLI agents does AWA support?

<!--@include: ../installation/agents/parts/agent_list.md-->

### What are the benefits of AWA compared to other agentic frameworks?

See [Alternatives](/introduction/alternatives) for a list of benefits of AWA, as well as a list of alternatives.

## For Developers

### Do I need to know Python to use AWA?

While AWA's core is written in Python, you can build your workflows in any language supported by Temporal's SDKs (Python, TypeScript, .NET, Java, Go, or PHP). Temporal supports polyglot deployments, so you can leverage AWA's Python components while writing your application code in your preferred language.

### Can I run AWA without Docker?

Yes! AWA is specifically designed to run natively on Mac, Windows, and Linux (without Docker or WSL). However, Docker support is available for containerized deployments.

### How does AWA handle workflow persistence and reliability?

AWA uses Temporal as its workflow engine, which provides automatic state persistence, crash recovery, and retry policies. Workflows can run for days, weeks, months, or indefinitely and automatically resume from failures. All workflow state is durably persisted. When running locally (outside Docker), a SQLite database is used to store workflow state. With Docker, a PostgreSQL database is used to store workflow state.

### Can I test my workflows locally?

Yes! AWA is designed to be local-first. You can run the entire stack locally without Docker, test (and debug) workflows end-to-end, and use BAML's built-in playground to iterate on prompts directly in your IDE.

### How do I integrate with existing systems?

AWA provides multiple integration points:

- **REST API**: Integrate via HTTP endpoints, event-driven systems
- **CLI**: Script workflow execution in CI/CD pipelines or locally
- **MCP**: Use with agentic IDEs like GitHub Copilot or Cursor

### How do I handle sensitive data and API keys?

AWA uses environment variables and `.env` files for sensitive configuration. API keys and secrets are never committed to code.

### How do I debug workflows that aren't working correctly?

AWA provides multiple debugging tools:

- Standard debugging tools for custom code in your target language (or Python if debugging AWA itself)
- Temporal UI for detailed workflow tracing and time-travel debugging
- Comprehensive logging to the `logs/` directory
- BAML playground for prompt testing and iteration
- Integration with Langfuse for LLM observability

### How do I justify the learning curve for AWA, Temporal, and BAML?

Investment rationale:

- **Temporal**: Industry-standard workflow engine with broad applicability
- **BAML**: Simplifies complex LLM integration patterns that gives you full control over the entire prompt, ensuring future portability if needed
- **Transferable skills**: Knowledge applies beyond AWA projects &mdash; agentic workflows are broadly applicable
- **Accelerated delivery**: Initial learning pays dividends on first project

## For Account Leaders

### What's the business value proposition of AWA?

AWA accelerates delivery of agentic workflow solutions through:

- Pre-built components reducing development time
- Enterprise-grade reliability from day one
- Universal compatibility eliminating environment constraints
- Rich examples and recipes for rapid client demos
- Clear path from prototype to production

### Can AWA be used in restrictive client environments?

Yes! AWA is specifically designed for maximum compatibility:

- Runs on any OS without Docker requirements
- No external dependencies or licensing complications
- Works with client's existing LLM providers and cloud infrastructure
- Can be deployed entirely within client networks
- Built on 100% open source technologies

### What are the licensing and cost implications?

AWA itself is a Slalom code accelerator with no licensing fees or complications. All underlying technologies (Temporal, BAML, FastAPI) are open source. Clients only pay for their chosen LLM provider and cloud infrastructure. There are no per-user fees or ongoing licensing costs.

### How do we position AWA against competitors?

AWA's key differentiators:

- **Universal compatibility** vs. platform-specific solutions
- **Enterprise-grade reliability** vs. experimental tools
- **Code-based workflows** vs. no-code/low-code limitations
- **Polyglot support** vs. single-language frameworks
- **Local-first development** vs. cloud-only solutions

### What training is required for teams?

- **Account teams**: 30-minute overview session covering capabilities and use cases
- **Developers**: ~1 day to get up and running and build basic example workflows
- **Ongoing support**: Available through #ae-awa Slack channel

## Technical Architecture

### Why did you choose Temporal over other workflow engines?

See [Architecture - Temporal](/introduction/architecture#temporal) for more details on the decision, and [Development - Temporal](/development/temporal) to learn more about Temporal itself.

### How does BAML integration work?

See [Development - BAML](/development/baml) for more on how to leverage BAML.

Within AWA, our BAML integration works as follows:

- Developers define BAML prompts in their client solution
- At runtime, the [transform](/reference/workflow/transform) (or [transform-batch](/reference/workflow/transform-batch)) activity takes the BAML content itself (the string representation of the BAML file) and dynamically generates the BAML client
- AWA then executes the BAML call using the generated client, and returns the typed result to the calling client workflow

This means that you can leverage BAML in your client solution no matter what language you're using, and we can bundle error handling and resiliency logic within AWA core for maximum reusability.

### How does the MCP integration work?

MCP comes into play in AWA in three primary ways:

1. AWA itself can be used as an MCP server. This means you can allow your agent (e.g. Claude Code) or agentic IDE (e.g. GitHub Copilot) to execute and monitor AWA workflows directly. Provide workflows as tools.
2. AWA has an [invoke-mcp-tool](/reference/activity/invoke-mcp-tool) activity that can be used to invoke MCP tools from within a workflow.
3. AWA includes an [execute-agent](/reference/workflow/execute-agent) workflow that can be used to execute an agent (e.g. Claude Code, Goose, Codex) that itself can use MCP tools.

## Support & Community

### Where can I get help if I'm stuck?

Don't hesitate to reach out in the [#ae-awa](https://grid-slalom.enterprise.slack.com/archives/C094ZRQC6P6) channel in Slack to get help from the core team and the larger AWA user community.

You can also reach out directly to [David Lawton](mailto:david.lawton@slalom.com) or [Ryan Henderson](mailto:ryan.henderson@slalom.com) to arrange dedicated project support.

### How do I contribute back to AWA?

We're open for pull requests! We're always looking for additional cookbook recipes, but we're also open to new features or fixes.

Let us know what you're thinking in the [#ae-awa](https://grid-slalom.enterprise.slack.com/archives/C094ZRQC6P6) channel in Slack and we can point you in the right direction to make a contribution.
