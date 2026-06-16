# Use Cases

AWA is suited for a wide range of use cases. This page outlines some generic usage models to demonstrate **how** AWA can be leveraged, as well as specific use cases to demonstrate **what** AWA can be leveraged for.

## Agentic Workflows

Agentic workflows fit within an AI tooling ecosystem, but they are not the only approach. The graphic below demonstrates one approach to evaluating your problem and possible solutions. **Problem complexity** and **solution reliability** are important facets to consider when choosing your path.

AWA is targeted at the top-right quadrant of this chart, enabling agent orchestration and agentic workflows to accomplish complex tasks in a reliable and repeatable way.

<img src="/images/problem-solving-with-ai.jpg" alt="Problem Solving with AI" />

## AWA Usage Models

| Name                                          | Environment                             | Trigger                  | AWA Entrypoint | Example Use Case(s)                                                                                |
| --------------------------------------------- | --------------------------------------- | ------------------------ | -------------- | -------------------------------------------------------------------------------------------------- |
| Local CLI Utility                             | Local Developer Machine                 | CLI command or script    | CLI            | Write my commit message, summarize what I did yesterday based on git commits                       |
| CI Pipeline                                   | CI Pipeline (Cloud-Hosted)              | Pipeline step            | CLI or API     | Write and update a detailed PR description                                                         |
| Manual UI Execution                           | Local Developer Machine or Cloud-Hosted | Manual UI Button Click   | UI             | Analyze codebase, Generate code documentation                                                      |
| Event-Driven                                  | Cloud-Hosted                            | Event (e.g. SNS)         | API            | Perform analysis and send incident report email, Respond to questions in Slack via webhook         |
| MCP via Agentic IDE (e.g. GH Copilot, Cursor) | Local Developer Machine                 | IDE Agent MCP Tool Use   | MCP            | Execute sub-agent, Refine story and propose architecture                                           |
| Scheduled Action                              | Local Developer Machine or Cloud-Hosted | Temporal Schedule (cron) | Temporal       | Send me a Slack message 5 minutes before standup containing a summary of my commits from yesterday |

## AWA Example Use Cases

:::info Only the Beginning
This list is only the beginning &mdash; the possibilities are endless. Have an idea you don't see here? Build it and let us know about it in [#ae-awa](https://grid-slalom.enterprise.slack.com/archives/C094ZRQC6P6).
:::

- **Generate Documentation Site**: Go from code to a full-fidelity, deployable Vitepress documentation site.
- **Write PR Description**: Review a changeset against a target branch, take project context into consideration, and write a detailed PR description automatically from CI.
- **Unit Test Writer**: Speed up story delivery and increase quality by automating the first pass of unit test development.
- **Investigate Incident**: React to an alert or other event to run diagnostics, search and analyze logs, and propose possible root causes with a message to the incident team.
- **Figma to Refined Story in Jira**: Go from mockup to fully-refined story in Jira.
- **Refine Story from Draft**: Generate a highly-detailed story from a bullet-level draft.
- **Generate Release Notes**: Automatically generate release notes from merged PRs, to keep your stakeholders informed.
- **Code Modernization Context Builder**: Accelerate modernization by automatically building context files for agentic IDEs from a legacy codebase.
- **Prompt Improver**: Iteratively improve a prompt to rapidly improve results.
- **Deep Research**: Research and analyze multiple sources to produce a report.
- **Code Review**: Accelerate your workflow by automating the first round of code review feedback.
- **Increase Test Coverage**: Go beyond keeping up, and automatically boost your overall test coverage.
