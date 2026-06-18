# Contributing

Contributions to AWA are welcome!

## Onboarding

We are using the following resources in our development process. Request access in the [#ae-awa](https://grid-slalom.enterprise.slack.com/archives/C094ZRQC6P6) Slack channel.

- [Bitbucket Repo](https://bitbucket.org/slalom-consulting/agentic-workflow-accelerator)
- [Jira Project](https://slalom.atlassian.net/jira/software/projects/AWA/boards/6894) (open a help.slalom.com [ticket](https://slalom.service-now.com/help?id=sc_cat_item&sys_id=bd990c111b2070904c03419ead4bcbfe&table=sc_cat_item&searchTerm=jira) if you need a license)
- [Miro Board](https://miro.com/app/board/uXjVIqmc3bs=/?moveToWidget=3458764631154068383&cot=14)
- Slack Channels
  - [Public Community: #ae-awa](https://grid-slalom.enterprise.slack.com/archives/C094ZRQC6P6)
  - [Contributing Developers: #ae-awa-dev](https://grid-slalom.enterprise.slack.com/archives/C090UJ17TMG)
  - [Pull Requests: #ae-awa-pr](https://grid-slalom.enterprise.slack.com/archives/C0915TJLGSD)

### Core Team

The core team will also have access to the following resources:

- [AWS Dev Account](https://devaws.slalom.com)
- Standup meetings (daily)
- Refinement meeting (weekly)
- Slack Channels
  - [Core Team: #ae-awa-core](https://grid-slalom.enterprise.slack.com/archives/C090GHDFAKG)

## Learning Resources

- [Temporal Documentation](https://docs.temporal.io)
- [Temporal Python SDK Documentation](https://docs.temporal.io/docs/python/getting-started)

### Walkthroughs

- [Deep-Dive: AI Agent Code Walkthrough](https://www.youtube.com/watch?v=LBGeejpKh5o)
- [AI Agent Github Repo](https://github.com/temporal-community/temporal-ai-agent)

## Demo Resources

For creating training videos and documentation demos, we provide structured templates and guidelines:

- **[Demo Script Template](/contributing/demo/demo_script)** - Comprehensive template for creating professional training videos and demonstrations of AWA features
- **[Video Publishing & Embedding Guide](/contributing/demo/video_publishing)** - Steps for hosting and embedding demo videos in documentation

This template includes:

- Pre-recording checklists and setup guidelines
- Structured video flow with proven sections (Introduction, Overview, Step-by-Step Demo, Benefits)
- Recording best practices for audio, visual, and content quality
- Post-production quality assurance checklists

Use this template when creating any video demonstrations or training materials for AWA features and workflows.

## Development Resources

- **[API Testing](./api-testing.md)** - Auto-generated API tests for the AWA system with comprehensive testing strategies
- **[API Test Generation - Developer Guide](./api-test-generation-developer.md)** - Implementation details for extending the API test generation system
- **[Authentication](./authentication.md)** - Development aspects of AWA's authentication system
- **[Debugging](./debugging.md)** - API debugging with breakpoints in VS Code and troubleshooting guide
- **[Developer Workflow](./developer-workflow.md)** - Local vs packaged AWA development patterns
- **[Cross-Platform Considerations](./cross-platform-considerations.md)** - Platform-specific development considerations

## Repo Structure

The agentic-workflow-accelerator project follows a modular structure designed for extensibility and clear separation of concerns:

### Core Directories

- **`awa/`** - Main Python package containing the framework
  - `core/` - Framework core components
    - `activities/` - Reusable Temporal activities
    - `api/` - FastAPI-based REST API with versioned routes
    - `baml_src/` - Core BAML function definitions
    - `cli/` - Typer-based CLI commands and service management
    - `engine/` - Temporal server, client, and worker management
    - `logger/` - Structured logging system
    - `mcp/` - Model Context Protocol server implementation
    - `models/` - Data models for configuration, API, and workflows
    - `scripts/` - Setup and generation scripts
    - `utils/` - Utility functions for file operations, config, etc.
    - `workflows/` - Reusable Temporal workflows
  - `baml_src/` - BAML function definitions for LLM interactions
  - `schemas/` - JSON schemas for configuration validation
  - `workflows/` - AWA workflows (non-reusable)
- **`docs/`** - VitePress documentation source
- **`ui/`** - Astro-based web interface
- **`tests/`** - Comprehensive test suite
  - `ui/` - Playwright-based UI tests
  - `unit/` - Unit tests mirroring the source structure
  - `workflow/` - Workflow integration tests
