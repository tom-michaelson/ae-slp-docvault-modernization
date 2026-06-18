export function getCookbookSidebar(): any[] {
  return [
    { text: "Overview", link: "/cookbook/" },
    {
      text: "Tutorials",
      collapsed: true,
      items: [
        {
          text: "AWA 101",
          collapsed: true,
          items: [
            { text: "Overview", link: "/cookbook/tutorials/awa-101/" },
            {
              text: "101: Simple Direct Transform",
              link: "/cookbook/tutorials/awa-101/awa-101-simple-direct-transform",
            },
            {
              text: "102: Advanced Direct Transform",
              link: "/cookbook/tutorials/awa-101/awa-102-advanced-direct-transform",
            },
            {
              text: "103: Transform Chain",
              link: "/cookbook/tutorials/awa-101/awa-103-transform-chain",
            },
            {
              text: "104: Transform Files in a Directory",
              link: "/cookbook/tutorials/awa-101/awa-104-transform-directory",
            },
          ],
        },
        {
          text: "AWA 201",
          collapsed: true,
          items: [
            { text: "Overview", link: "/cookbook/tutorials/awa-201/" },
          ],
        },
      ],
    },
    {
      text: "Recipes",
      collapsed: true,
      items: [
        {
          text: "Use MCP Tools",
          items: [
            {
              text: "HTTP",
              link: "/cookbook/recipes/use-mcp-tools/sample-mcp-tool-server-http-workflow",
            },
            {
              text: "stdio - Local Python",
              link: "/cookbook/recipes/use-mcp-tools/sample-mcp-tool-stdio-workflow",
            },
            {
              text: "stdio - NPX",
              link: "/cookbook/recipes/use-mcp-tools/sample-mcp-tool-npx-stdio-workflow",
            },
            {
              text: "stdio - UVX",
              link: "/cookbook/recipes/use-mcp-tools/sample-mcp-tool-uvx-stdio-workflow",
            },
          ],
        },
        {
          text: "Default Agent",
          items: [
            {
              text: "PydanticAI Agent Workflow",
              link: "/cookbook/recipes/default-agent/agent-mode-pydantic-ai-workflow",
            },
            {
              text: "Example Usage",
              link: "/cookbook/recipes/default-agent/DemoScript",
            },
          ],
        },
        {
          text: "Agent Isolation",
          items: [
            {
              text: "Sample Isolated Agent Workflow (Act Mode)",
              link: "/cookbook/recipes/agent-isolation/sample-isolated-agent-act-workflow",
            },
            {
              text: "Sample Isolated Agent Workflow (Analyze Mode)",
              link: "/cookbook/recipes/agent-isolation/sample-isolated-agent-analyze-workflow",
            },
          ],
        },
        {
          text: "OpenAI Agents SDK",
          items: [
            {
              text: "OpenAI Agents SDK Demo Workflow",
              link: "/cookbook/recipes/openai-agents-sdk-demo/openai-agents-sdk-demo-workflow",
            },
          ],
        },
        {
          text: "Test Doctor",
          items: [
            {
              text: "Test Doctor Workflow",
              link: "/cookbook/recipes/test-doctor/test-doctor-workflow",
            },
            {
              text: "Test and Lint Pipeline Workflow",
              link: "/cookbook/recipes/test-doctor/test-and-lint-pipeline-workflow",
            },
            {
              text: "Demo Script",
              link: "/cookbook/recipes/test-doctor/demo-script",
            },
          ],
        },
        {
          text: "JIRA Test Generation",
          items: [
            {
              text: "JIRA to Test Cases Workflow",
              link: "/cookbook/recipes/jira-test-generation/",
            },
          ],
        },
        {
          text: "PR Description Workflow",
          items: [
            {
              text: "PR Description Workflow",
              link: "/cookbook/recipes/pr-description/PRDescriptionWorkflow",
            },
            {
              text: "Demo Script",
              link: "/cookbook/recipes/pr-description/DemoScript",
            },
          ],
        },
        {
          text: "GitHub PR Description",
          items: [
            {
              text: "GitHub PR Description Workflow",
              link: "/cookbook/recipes/github-pr-description/",
            },
            {
              text: "GitHub Actions Integration",
              link: "/cookbook/recipes/github-pr-description/github-actions-integration",
            },
            {
              text: "Pipeline Runner",
              link: "/cookbook/recipes/github-pr-description/pipeline-runner",
            },
          ],
        },
        {
          text: "Other",
          items: [
            {
              text: "Apply File Diff",
              link: "/cookbook/recipes/other/single-file-diff",
            },
            {
              text: "Image to Story",
              link: "/cookbook/recipes/other/image-to-story-workflow",
            },
            {
              text: "Release Notes",
              link: "/cookbook/recipes/other/release-notes-workflow",
            },
            {
              text: "Remote File IO",
              link: "/cookbook/recipes/other/remote-file-io",
            },
            {
              text: "Vector Database Ingestion Workflow",
              link: "/cookbook/recipes/other/vector-database-ingestion",
            },
          ],
        },
      ],
    },
    { text: "Starter Projects", link: "/cookbook/starter-projects" },
  ]
}
