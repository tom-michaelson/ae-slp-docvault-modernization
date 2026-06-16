---
name: agents-index
description: Canonical catalog of AWA AI subagents with roles and usage guidance.
claude:
  include_in_index: true
  subagent: false
opencode:
  include_in_index: true
  subagent: false
---

# Agent Catalog

This directory contains the canonical source specifications for AWA AI subagents. Each agent file includes unified frontmatter for both Claude and OpenCode runtimes so that automation (e.g. `AGENTS.md` generation) can consume a single source of truth.

## Available Agents

| Agent | Purpose (Concise) |
|-------|-------------------|
| bitbucket-api-operator | Performs Bitbucket repository and PR operations |
| code-author | Implements and refactors code per an approved plan |
| code-review-agent | Reviews diffs and proposes improvements |
| code-simplifier | Simplifies and clarifies complex code blocks |
| git-operations-executor | Executes low-level git operations safely |
| implementation-plan-validator | Validates implementation plans before coding |
| jira-operator | Interfaces with Jira for issue operations |
| repo-initializer | Bootstraps or restructures repositories |
| task-researcher | Gathers technical/contextual information before execution |
| test-runner | Runs tests and reports structured results |

## Conventions

- Frontmatter fields `claude` and `opencode` must stay in sync.
- `subagent: true` indicates the file is eligible for delegated execution.
- `include_in_index: true` controls whether it is exported to aggregated docs.
- Descriptions should begin with an imperative verb and stay under ~160 chars.

## Lifecycle

1. Propose changes in a feature branch.
2. Update the specific agent file only (avoid cross-file edits unless required).
3. Run the documentation generator to refresh `AGENTS.md`.
4. Have changes reviewed with a focus on clarity, constraints, and safety.

## Adding a New Agent

1. Copy an existing agent file as a template.
2. Update `name`, `description`, and body content.
3. Ensure responsibilities, constraints, and output format are explicit.
4. Set `subagent: true` and `include_in_index: true` in both runtime blocks.
5. Regenerate artifacts and open a PR.
