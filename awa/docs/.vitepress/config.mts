import { defineConfig } from "vitepress";
import { withMermaid } from "vitepress-plugin-mermaid";
import llmstxt from "vitepress-plugin-llms";
import { bamlTextmate, bamlJinjaTextmate } from "./baml/baml.tmLanguage.ts";
import lightbox from "vitepress-plugin-lightbox"
import { getCookbookSidebar } from "./cookbook-sidebar";

// https://vitepress.dev/reference/site-config
export default withMermaid(
  defineConfig({
    ignoreDeadLinks: [/^http?:\/\/localhost/],
    base: "/docs/",
    outDir: "./../ui/docs-content",
    title: "by Slalom",
    titleTemplate: ":title - AWA",
    description:
      "AWA is a code accelerator to aid in the development and deployment of agentic workflows and agents",
    head: [["link", { rel: "icon", href: "/docs/favicon/favicon-96x96.png" }]],
    lastUpdated: true,
    appearance: false,
    mermaid: {
      theme: "default",
      look: "handDrawn",
      layout: "ELK", // "dagre"
      elk: {
        mergeEdges: true,
        nodePlacementStrategy: "BRANDES_KOEPF",
        cycleBreakingStrategy: "GREEDY_MODEL_ORDER",
      },
    },
    srcExclude: [
      "**/.cookbook-placeholder/**",
    ],
    themeConfig: {
      logo: "/images/AWA Logo Dark.svg",
      nav: [
        { text: "Home", link: "/" },
        { text: "Quick Start", link: "/introduction/quick-start" },
        { text: "Usage", link: "/usage/" },
        { text: "Cookbook", link: "/cookbook/" },
        { text: "Reference", link: "/reference/" },
      ],
      sidebar: [
        {
          text: "Introduction",
          collapsed: true,
          items: [
            { text: "Intro", link: "/introduction/" },
            { text: "Quick Start", link: "/introduction/quick-start" },
            {
              text: "Guiding Principles",
              link: "/introduction/guiding-principles",
            },
            { text: "Use Cases", link: "/introduction/use-cases" },
            { text: "Architecture", link: "/introduction/architecture" },
            { text: "FAQs", link: "/introduction/faq" },
            {
              text: "More", collapsed: true, items: [
                { text: "History", link: "/introduction/history" },
                { text: "Alternatives", link: "/introduction/alternatives" },
                {
                  text: "Release Notes",
                  items: [
                    { text: "Latest", link: "/introduction/release-notes/latest" },
                    {
                      text: "Archive",
                      link: "/introduction/release-notes/archive",
                    },
                  ],
                },
                { text: "Roadmap", link: "/introduction/roadmap" },
                { text: "Troubleshooting", link: "/introduction/troubleshooting" },
              ]
            },
          ],
        },
        {
          text: "Basics",
          items: [
            {
              text: "Installation",
              collapsed: true,
              items: [
                { text: "Mac & Linux", link: "/installation/mac-linux" },
                { text: "Windows", link: "/installation/windows" },
                { text: "Docker", link: "/installation/docker" },
                {
                  text: "Agents",
                  collapsed: true,
                  items: [
                    { text: "Overview", link: "/installation/agents/overview" },
                    { text: "Claude", link: "/installation/agents/claude" },
                    { text: "Codex", link: "/installation/agents/codex" },
                    { text: "Gemini", link: "/installation/agents/gemini" },
                    { text: "GitHub Copilot CLI", link: "/installation/agents/github-copilot-cli" },
                    { text: "Goose", link: "/installation/agents/goose" },
                    { text: "OpenCode", link: "/installation/agents/opencode" },
                    { text: "Amazon Q", link: "/installation/agents/q" },
                  ],
                },
              ],
            },
            {
              text: "Configuration",
              collapsed: true,
              items: [
                { text: "Overview", link: "/configuration/" },
                { text: "Authentication", link: "/configuration/authentication" },
                {
                  text: "LLMs",
                  link: "/configuration/llms/",
                  items: [
                    { text: "Anthropic", link: "/configuration/llms/anthropic" },
                    {
                      text: "AWS Bedrock",
                      link: "/configuration/llms/aws-bedrock",
                    },
                    {
                      text: "Azure OpenAI",
                      link: "/configuration/llms/azure-openai",
                    },
                    { text: "GitHub Copilot", link: "/configuration/llms/github-copilot" },
                    { text: "Google Vertex AI", link: "/configuration/llms/google-vertex" },
                    { text: "LiteLLM", link: "/configuration/llms/lite-llm" },
                    { text: "OpenAI", link: "/configuration/llms/openai" },
                  ],
                },
              ],
            },
            {
              text: "Usage",
              collapsed: true,
              items: [
                { text: "Overview", link: "/usage/" },
                {
                  text: "SDK",
                  collapsed: true,
                  items: [
                    { text: "Overview", link: "/usage/sdk/" },
                    { text: "Python SDK", link: "/usage/sdk/python" },
                    { text: "C# SDK", link: "/usage/sdk/csharp" },
                  ],
                },
                { text: "CLI", link: "/usage/cli" },
                { text: "API", link: "/usage/api" },
                { text: "UI", link: "/usage/ui" },
                { text: "CI/CD", link: "/usage/cicd" },
                { text: "MCP", link: "/usage/mcp" },
                { text: "A2A", link: "/usage/a2a" },
                {
                  text: "Features",
                  items: [
                    { text: "Prompts and Templates", link: "/usage/features/prompts-and-templates" },
                    { text: "Agents", link: "/usage/features/agents" },
                    {
                      text: "OpenAI Agents SDK",
                      link: "/usage/features/openai-agents-sdk.md",
                    },
                    { text: "Agent Streaming", link: "/usage/features/agent-streaming" },
                    { text: "File System Operations", link: "/usage/features/file-system-operations" },
                    { text: "Document Parsing", link: "/usage/features/document-parsing" },
                    { text: "Document Chunking", link: "/usage/features/document-chunking" },
                    { text: "Logging", link: "/usage/features/logging" },
                    { text: "Workflow Registration", link: "/usage/features/workflow-registration" },
                  ],
                },
              ],
            },
            {
              text: "Deployment",
              collapsed: true,
              items: [
                { text: "Overview", link: "/deployment/" },
                { text: "Docker", link: "/deployment/docker" },
                { text: "AWS", link: "/deployment/aws" },
                { text: "Azure", link: "/deployment/azure" },
                { text: "GCP", link: "/deployment/gcp" },
              ],
            },
          ],
        },
        {
          text: "Development",
          collapsed: true,
          items: [
            { text: "Overview", link: "/development/" },
            { text: "Temporal", link: "/development/temporal" },
            { text: "Temporal Patterns", link: "/development/temporal-patterns" },
            { text: "BAML", link: "/development/baml" },
            { text: "BAML Integration", link: "/development/baml-integration" },
            { text: "BAML Patterns", link: "/development/baml-patterns" },
            { text: "Python Standards", link: "/development/python-standards" },
            { text: "Naming Conventions", link: "/development/temporal-naming-conventions" },
            { text: "Child Workflows", link: "/development/child-workflows" },
            { text: "LLM Cache", link: "/development/llm-cache" },
            { text: "Agent Streaming", link: "/development/agent-streaming" },
            { text: "Workflow Testing", link: "/development/workflow-testing" },
          ],
        },
        {
          text: "Cookbook",
          collapsed: true,
          items: getCookbookSidebar(),
        },
        {
          text: "Contributing",
          collapsed: true,
          items: [
            { text: "Overview", link: "/contributing/" },
            { text: "Authentication", link: "/contributing/authentication" },
            { text: "Debugging", link: "/contributing/debugging" },
            { text: "Developer Workflow", link: "/contributing/developer-workflow" },
            { text: "Cross-Platform Considerations", link: "/contributing/cross-platform-considerations" },
            { text: "Documentation", link: "/contributing/documentation" },
            { text: "Workflow Management", link: "/contributing/workflow-management" },
            { text: "Temporal Conventions", link: "/contributing/temporal-conventions" },
            { text: "Dynamic BAML", link: "/contributing/dynamic-baml" },
            { text: "SDK", collapsed: false, items: [
              { text: "Add Utility", link: "/contributing/sdk/add-utility" },
              { text: "Generate", link: "/contributing/sdk/generation" }
            ] },
            { text: "CI", link: "/contributing/ci" },
            { text: "Workflow Input", link: "/contributing/workflow-input" },
            {
              text: "Demo",
              collapsed: true,
              items: [
                { text: "Demo Script Template", link: "/contributing/demo/demo_script" },
                { text: "Video Publishing & Embedding Guide", link: "/contributing/demo/video_publishing" },
              ],
            },
          ],
        },
        {
          text: "Reference",
          collapsed: true,
          items: [
            // { text: "Glossary", link: "/reference/glossary" },
            // { text: "Resources", link: "/reference/resources" },
            {
              text: "Configuration",
              items: [
                { text: ".env", link: "/reference/configuration/environment" },
                {
                  text: "config.yaml",
                  link: "/reference/configuration/application",
                },
              ],
            },
            { text: "CLI", link: "/reference/cli" },
            { text: "API", link: "/reference/api" },
            {
              text: "Activities",
              link: "/reference/activity/",
              collapsed: true,
              items: [
                {
                  text: "agent-execute",
                  link: "/reference/activity/agent-execute",
                },
                {
                  text: "apply-diff",
                  link: "/reference/activity/apply-diff",
                },
                {
                  text: "chunk-document",
                  link: "/reference/activity/chunk-document",
                },
                {
                  text: "cleanup-worktree-activity",
                  link: "/reference/activity/cleanup-worktree-activity",
                },
                {
                  text: "copy-analyze-outputs-activity",
                  link: "/reference/activity/copy-analyze-outputs-activity",
                },
                {
                  text: "copy-directory",
                  link: "/reference/activity/copy-directory",
                },
                {
                  text: "git-clone-activity",
                  link: "/reference/activity/git-clone-activity",
                },
                {
                  text: "invoke-mcp-tool",
                  link: "/reference/activity/invoke-mcp-tool",
                },
                {
                  text: "list-directory",
                  link: "/reference/activity/list-directory",
                },
                {
                  text: "merge-worktree-changes-activity",
                  link: "/reference/activity/merge-worktree-changes-activity",
                },
                {
                  text: "read-file",
                  link: "/reference/activity/read-file",
                },
                {
                  text: "read-file-and-parse",
                  link: "/reference/activity/read-file-and-parse",
                },
                {
                  text: "read-file-or-directory",
                  link: "/reference/activity/read-file-or-directory",
                },
                {
                  text: "requirements-gathering",
                  link: "/reference/activity/requirements-gathering",
				},
				{
                  text: "resolve-config-variables-activity",
                  link: "/reference/activity/resolve-config-variables-activity",
                },
                {
                  text: "resolve-template-activity",
                  link: "/reference/activity/resolve-template-activity",
                },
                {
                  text: "sample-activity",
                  link: "/reference/activity/sample-activity",
                },
                {
                  text: "say-hello-activity",
                  link: "/reference/activity/say-hello-activity",
                },
                {
                  text: "setup-isolated-agent-activity",
                  link: "/reference/activity/setup-isolated-agent-activity",
                },
                {
                  text: "setup-worktree-activity",
                  link: "/reference/activity/setup-worktree-activity",
                },
                {
                  text: "socket",
                  link: "/reference/activity/socket",
                },
                {
                  text: "streaming-monitor-activity",
                  link: "/reference/activity/streaming-monitor-activity",
                },
                {
                  text: "transform",
                  link: "/reference/activity/transform",
                },
                {
                  text: "transform-activity",
                  link: "/reference/activity/transform-activity",
                },
                {
                  text: "write-file",
                  link: "/reference/activity/write-file",
                },
              ],
            },
            {
              text: "Workflows",
              link: "/reference/workflow/",
              collapsed: true,
              items: [
                {
                  text: "build-prompt",
                  link: "/reference/workflow/build-prompt",
                },
                {
                  text: "chunk-document",
                  link: "/reference/workflow/chunk-document",
                },
                {
                  text: "create-prototype-from-figma",
                  link: "/reference/workflow/create-prototype-from-figma",
                },
                {
                  text: "execute-agent",
                  link: "/reference/workflow/execute-agent",
                },
                {
                  text: "hello-human",
                  link: "/reference/workflow/hello-human",
                },
                {
                  text: "hello-world",
                  link: "/reference/workflow/hello-world",
                },
                {
                  text: "hitl-child",
                  link: "/reference/workflow/hello-world",
                },
                {
                  text: "isolated-agent-child-workflow",
                  link: "/reference/workflow/isolated-agent-child-workflow",
                },
                {
                  text: "openai-agent",
                  link: "/reference/workflow/openai-agent",
                },
                {
                  text: "requirements-gathering",
                  link: "/reference/workflow/requirements-gathering",
                },
                {
                  text: "resolve-template",
                  link: "/reference/workflow/resolve-template",
                },
                {
                  text: "single-file-diff",
                  link: "/reference/workflow/single-file-diff",
                },
                {
                  text: "transform",
                  link: "/reference/workflow/transform",
                },
                {
                  text: "transform-batch",
                  link: "/reference/workflow/transform-batch",
                },
                {
                  text: "transform-file",
                  link: "/reference/workflow/transform-file",
                },
              ],
            },
          ],
        },
        {
          text: "AI Rules",
          collapsed: true,
          items: [
            { text: "Overview", link: "/ai/" },
            { text: "Core Instruction", link: "/ai/core-instructions" },
            { text: "Agents", collapsed: true, items: [
              { text: "Catalog", link: "/ai/agents/" },
              { text: "bitbucket-api-operator", link: "/ai/agents/bitbucket-api-operator" },
              { text: "code-author", link: "/ai/agents/code-author" },
              { text: "code-review-agent", link: "/ai/agents/code-review-agent" },
              { text: "code-simplifier", link: "/ai/agents/code-simplifier" },
              { text: "git-operations-executor", link: "/ai/agents/git-operations-executor" },
              { text: "implementation-plan-validator", link: "/ai/agents/implementation-plan-validator" },
              { text: "jira-operator", link: "/ai/agents/jira-operator" },
              { text: "repo-initializer", link: "/ai/agents/repo-initializer" },
              { text: "task-researcher", link: "/ai/agents/task-researcher" },
              { text: "test-runner", link: "/ai/agents/test-runner" },
            ] },
            { text: "Commands", collapsed: true, items: [
              { text: "BAML Development", link: "/ai/commands/baml-development" },
              { text: "Python Development", link: "/ai/commands/python-development" },
              { text: "Documentation Generation", link: "/ai/commands/docs-generation" },
              { text: "Workflow Management", link: "/ai/commands/workflow-management" },
              { text: "Specification Writing", link: "/ai/commands/spec-writing" },
              { text: "PR Description", link: "/ai/commands/pr-description" },
              { text: "Write Bug", link: "/ai/commands/write-bug" },
            ] },
            { text: "Hooks", collapsed: true, items: [
              { text: "Stop Lint", link: "/ai/hooks/stop-lint" },
            ] },
          ],
        },
      ],

      socialLinks: [
        {
          icon: "bitbucket",
          link: "https://bitbucket.org/slalom-consulting/agentic-workflow-accelerator",
        },
        {
          icon: "slack",
          link: "https://grid-slalom.enterprise.slack.com/archives/C094ZRQC6P6",
        },
      ],

      search: {
        provider: "local",
      },

      footer: {
        message: "",
        copyright: "© Slalom, Inc. All rights reserved.",
      },

      externalLinkIcon: true,

      outline: {
        level: "deep",
        label: "Contents",
      },
    },
    markdown: {
      languages: [bamlTextmate, bamlJinjaTextmate], // @ts-ignore
      lineNumbers: true,
      config(md) {
        const defaultCodeInline = md.renderer.rules.code_inline!;
        md.renderer.rules.code_inline = (tokens, idx, options, env, self) => {
          tokens[idx].attrSet("v-pre", "");
          return defaultCodeInline(tokens, idx, options, env, self);
        };
        md.use(lightbox, {});
      },
    },
    vite: {
      plugins: [
        llmstxt({
          ignoreFiles: [],
        }),
      ],
    },
  })
);
