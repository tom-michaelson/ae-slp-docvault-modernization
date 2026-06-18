# Architecture

The Agentic Workflow Accelerator (AWA) follows a layered architecture design that adheres to our [guiding principles](/introduction/guiding-principles): **Easy. Compatible. Useful.**

## Diagram

### Simplified

![AWA Architecture Diagram - Simplified](/images/awa-architecture-simple.jpg)

### Detailed

![AWA Architecture Diagram](/images/awa-architecture.png)

## Tech Stack

**Core (CLI, API)**

- **Python**: AWA's core logic (and the Temporal SDK we're using) is Python. This allows us to leverage a large ecosystem of LLM-related libraries and tools. This **DOES NOT** mean applications built with AWA must be written in Python &mdash; Temporal is polyglot by default.
- **[Temporal](https://temporal.io/)**: Workflow engine for reliable, scalable workflow execution. Cloud-agnostic, polyglot, and fully open source. Written in Go. Read more about this choice [below](#temporal).
- **[BAML](https://www.boundaryml.com/)**: BAML is an LLM invocation and structured output parsing library written in Rust. LLM-agnostic, polyglot, and fully open source Read more about this choice [below](#baml).
- **[PydanticAI](https://ai.pydantic.dev/)**: Built-in agent framework providing type-safe LLM interactions with streaming support. Integrated directly into AWA for high-performance native agent execution.
- **[FastAPI](https://fastapi.tiangolo.com/)**: FastAPI is a modern, fast web framework for building APIs in Python. Used for the AWA API.
- **[Typer](https://typer.tiangolo.com/)**: Written by the same team as FastAPI, Typer is a library for building CLI applications in Python. Used for the AWA CLI.

**UI**

- **TypeScript**: TypeScript is a superset of JavaScript that adds static typing.
- **[React](https://react.dev/)**: React is a popular JavaScript library for building user interfaces.
- **[Astro](https://astro.build/)**: Astro is a full-stack meta-framework for building apps with any major frontend framework (including React).
- **[MUI](https://mui.com/)**: MUI is a library of components for building consistent, accessible, and beautiful user interfaces.
- **[Vite](https://vite.dev/)**: Vite is a fast build tool for modern web projects.

**Other**

- **[LiteLLM](https://github.com/BerriAI/litellm)**: Optional for AWA. Proxy interface to multiple LLM providers. Free and open source.
- **[Langfuse](https://langfuse.com/)**: Optional for AWA. Observability and monitoring platform. Free and open source.
- **[Dagger](https://dagger.io/)**: Using Dagger for our CI/CD pipelines means they can are locally-runnable and portable to any cloud-based CI/CD provider (GitHub Actions, Bitbucket Pipelines, Jenkins, etc.).
- **[Vitepress](https://vitepress.dev/)**: Vitepress is a static site generator for building documentation websites. We use Vitepress to build this docs site.

## Components

**AWA CLI**

The Command Line Interface (CLI) is built using Typer and provides a user-friendly way to interact with AWA from the terminal. It handles:

- System configuration
- Service management (start/stop services independently)
- Running all other components, including the AWA Engine and Temporal
- Workflow execution
- Running the AWA [MCP server](/usage/mcp)
- Running the AWA [A2A agent](/usage/a2a)

**AWA API**

The core HTTP API layer built with FastAPI that:

- Exposes RESTful endpoints for all AWA operations for easy integration with larger multi-service systems
- Manages authentication and authorization
- Coordinates between different system components
- Provides a unified interface for both CLI and UI clients

**AWA Core Worker**

A Python Temporal worker that contains a set of reusable child workflows, workflow activities, and other code components that use Temporal to run workflows. This includes:

- **Built-in PydanticAI Integration**: Native support for PydanticAI agents with streaming capabilities
- **External Agent Support**: Integration with containerized agents (Claude Code, Goose, Codex, etc.)
- **Workflow Orchestration**: Durable execution patterns for complex agentic workflows
- **Activity Library**: Reusable components for file operations, transformations, and agent execution

See our Reference docs for more details on the specific [workflows](/reference/workflow/) and [activities](/reference/activity/) provided.

**AWA UI**

A simple React + Astro-based web interface that provides:

- Workflow initiation and human-in-the-loop interactions
- Integration with Temporal UI for detailed workflow monitoring
- These docs (built with Vitepress)

**AWA MCP Server**

An MCP server that allows agents to interact with AWA to run and monitor workflows. Can be used by CLI agents (like Claude Code) and agentic IDEs (like Github Copilot or Cursor).

**Temporal**

Temporal comes with a few components we're using out of the box:

- **Engine**: The core workflow engine. Technically the Temporal Engine will invoke _your_ code (and the AWA activity and workflows), but conceptually it's the "backend" of the system.
- **UI**: Highly detailed workflow monitoring UI.
- **CLI**: Used to start the engine and UI, and to manage workflow execution directly.

**Your Application**

You can of course simply extend the AWA core for your purposes. But Temporal's polyglot support means that you do not have to &mdash; you can build your application and workflows in your language of choice and still leverage all of AWA's reusable components and child workflows which are written in Python.

- Can be written in any language supported by Temporal
- Can run locally or in any cloud provider
- Can integrate with AWA core directly via the API, via an event-based approach, or via CLI scripts
- Can directly interact with Temporal for advanced use cases

## Service Management

AWA provides a robust service management system that allows for:

1. **Independent Service Control**

   - Start/stop services independently
   - Check service status
   - Manage service dependencies

2. **Service Dependencies**

   - Temporal Server (required for workflow execution)
   - Temporal Worker (executes workflows and activities)
   - API Server (REST API for system interaction)
   - UI Server (optional web interface)

3. **Service Lifecycle**

   - Services can be started with `make start`
   - Workflow execution only starts missing services
   - Services remain running until explicitly stopped

4. **Error Handling**
   - Graceful service startup and shutdown
   - Automatic cleanup on service failures
   - Service status verification before operations

## Temporal

**What is Temporal?**

Temporal is a full-featured workflow engine that allows you to build and orchestrate complex workflows.

Crucially, Temporal is _not_ a recently-invented LLM-centric workflow engine or DAG builder &mdash; it allows for building agentic workflows just like you would any other system, supporting everything required to build a full production-grade system.

**Why Temporal?**

Workflows are a common abstraction — using an established workflow engine allows us to spend our limited development on higher-leverage accelerator components.

- **It's just code** &mdash; with Temporal you build workflows with code, not a bespoke YAML-based DSL. This means maximal reuse with other (potentially pre-existing) code and libraries, dead-simple automated testing (normal unit tests!), and a great developer experience.
- **Polyglot by nature** &mdash; Temporal allows for running a system with workflows and activities running in any of their supported SDK languages (Python, TypeScript, .NET, Java, Go, or PHP).
- Provides primitives for events, queries, and signals (human-in-the-loop)
- Resilient by default with state persistence and retry policies
- Includes web UI out of the box for running and monitoring workflows
- Published as two Go binaries, Temporal runs natively on Mac, Windows, and Linux without Docker
- Free and open source (with completely optional platform option for managed hosting)
- Mature and popular, including with many large enterprises, like Netflix, Doordash, and OpenAI itself
- Runs natively, locally (without Docker) on Mac, Windows, and Linux
- Extensive high-quality documentation

We've have a collection of Temporal articles and resources for further reading: [Temporal](/development/temporal). Or read more from [Temporal's Official Docs](https://temporal.io/).

**Suggested Related Reading: Why Workflows?**

- [Agents are just workflows, really](https://www.amplifypartners.com/blog-posts/agents-are-just-workflows-really)
- [The fallacy of the graph: Why your next agentic workflow should be code, not a diagram](https://temporal.io/blog/the-fallacy-of-the-graph-why-your-next-workflow-should-be-code-not-a-diagram)

## BAML

**What is BAML?**

- LLM invocation library that includes
  - Fuzzy parsing for structured output
  - "Playground" VS Code extension for quick prompt testing
- Free and open source (with completely optional platform for observability)

**Why BAML?**

- Dramatically simplifies the complexity of LLM calling and chaining
- Solves structured output for any model
- Natively compatible with all major LLM providers, and compatible via LiteLLM with virtually any other provider
- Makes integrating LLM calls into application code as simple as calling typed native functions
- Built-in "Playground" provides way to quickly iterate on prompts
- Built-in testing framework serves as a way to build simple evals

Read more about [BAML](https://www.boundaryml.com/)
