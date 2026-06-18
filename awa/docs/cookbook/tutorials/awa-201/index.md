# AWA 201 - Automated Documentation Generator

The `awa-201-generate-documentation-site` workflow is an advanced AWA workflow that automatically generates a comprehensive documentation site from source code. It analyzes your codebase, creates technical documentation, and builds a complete VitePress documentation site with intelligent organization and cross-references.

## Overview

This workflow takes a target directory containing source code and produces a fully functional documentation website. It intelligently analyzes your codebase's structure, technology stack, and individual files to create organized, searchable documentation that includes:

- **Technology Stack Analysis**: Identifies and documents the technologies, frameworks, and dependencies used
- **File Classification**: Categorizes files by type (source code, configuration, documentation, etc.)
- **Code Documentation**: Generates detailed descriptions of source files and their functionality
- **Directory Structure**: Documents the project organization and architecture
- **Cross-References**: Creates links between related components and files, and reviews each documentation page against source code files to ensure accuracy
- **Interactive Site**: Builds a VitePress documentation site with search and navigation

## Run It

<!--@include: /../../../.shared/recipe-setup-pre.md -->

4. From the AWA repo root directory, run the AWA 201 workflow:

   ```bash
   # /agentic-workflow-accelerator/
   uv run -m awa.main run -w "awa-201-generate-documentation-site"
   ```

<!--@include: /../../../.shared/recipe-setup-post.md -->

## How It Works

The workflow executes 13 sequential steps to transform source code into documentation:

### Phase 1: Analysis and Setup

1. **Define Paths**: Establishes working directories and file paths
2. **Copy Source Files**: Creates a working copy of the target codebase
3. **Classify Files**: Categorizes each file by type and purpose
4. **Describe Files**: Generates detailed descriptions of source files

### Phase 2: Technical Documentation

5. **Describe Tech Stack**: Analyzes dependencies and creates technology overview
6. **Describe Directories**: Documents the project structure and organization
7. **Create Application Summary**: Generates high-level application overview

### Phase 3: Site Generation

8. **Copy Starter Docs**: Sets up the VitePress documentation framework
9. **Copy Source Files**: Integrates source code into the documentation site
10. **Create Site Outline**: Generates the documentation structure and navigation
11. **Create Documentation Pages**: Builds individual documentation pages
12. **Validate Documentation**: Ensures documentation quality and completeness
13. **Build Documentation Site**: Compiles the final VitePress site

## Usage

### Input Parameters

| Parameter        | Type          | Description                                        | Default    |
| ---------------- | ------------- | -------------------------------------------------- | ---------- |
| `target_dir`     | `str \| Path` | Path to the source code directory to document      | Required   |
| `agent_provider` | `str`         | AI provider for analysis ("claude", "codex", etc.) | `"claude"` |

### Output

The workflow generates a complete documentation site in the output directory containing:

- **VitePress Site**: A fully functional documentation website
- **Source Analysis**: Detailed file and directory descriptions
- **Technology Documentation**: Tech stack overview and explanations

## Configuration

### Environment Variables

| Variable                    | Description                       | Default                        |
| --------------------------- | --------------------------------- | ------------------------------ |
| `TEMPORAL_TASK_QUEUE`       | Task queue for workflow execution | `"recipes-default-task-queue"` |
| `MAX_CONCURRENT_TRANSFORMS` | Maximum parallel BAML transforms  | `10`                           |
| `MAX_CONCURRENT_AGENTS`     | Maximum parallel agent operations | `5`                            |

## Output Structure

The generated documentation site includes:

```
output/
├── docs-site/          # VitePress documentation site
│   ├── docs/           # Generated documentation pages
│   ├── source/         # Source code for reference
│   └── package.json    # VitePress configuration
├── descriptions/       # Detailed file descriptions
├── short_descriptions/ # Summary file descriptions
├── directory_descriptions/ # Directory structure docs
├── tech_stack.md      # Technology stack overview
└── application_summary.md # High-level application summary
```
