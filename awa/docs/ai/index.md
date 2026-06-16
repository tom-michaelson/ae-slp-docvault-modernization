# AI Rules Overview

The AI Rules system provides intelligent, context-aware guidance for multiple AI development tools working with the AWA (Agentic Workflow Accelerator) codebase. This system ensures consistent development practices, project-specific knowledge, and tool-optimized instructions across different AI assistants.

## Supported AI Tools

The system generates optimized documentation for four major AI development platforms:

- **Claude Code** - Command-based AI assistant with slash commands
- **Cursor** - AI-powered code editor with context-aware rules
- **GitHub Copilot** - AI code completion and generation
- **OpenCode** - Multi-agent development environment

## Organization Structure

AI rules are organized into three main categories:

### 📁 Agents
Individual AI agent configurations and specialized capabilities for specific development tasks.

### 📁 Commands
Development workflow commands and specialized operations.

### 📁 Hooks
Automated development hooks and pre-commit validations.

## Core Instruction

The **[Core Instruction](./core-instructions.md)** provides foundational guidance for all AI tools working with AWA, covering:
- Project architecture and technology stack
- Development patterns and conventions
- Configuration management
- Testing strategies
- Deployment procedures

## How It Works

### Source Files
All AI rules start as markdown files in the `docs/ai/` directory with embedded YAML configuration:

```yaml
cursor:
  description: "Context-aware guidance for Cursor editor"
  globs: "**/*.py"
  include_in_index: true

copilot:
  description: "Code generation guidance for GitHub Copilot"
  applyTo: "**/*.py"
  include_in_index: true

claude:
  command_name: "python-development"
  description: "Python development standards"
  include_in_index: true

opencode:
  description: "Python development guide for OpenCode"
  include_in_index: true
```

### Automatic Generation
The system automatically generates tool-specific files during development workflows:
- `make install` - Full project setup including AI rules
- `make docs-prep` - Documentation preparation
- `pnpm run docs:build` - Documentation build process

### Manual Generation
For immediate updates after editing source files:
```bash
pnpm run ai-rules:generate
```

## Key Features

### 🔄 Single Source of Truth
All AI tools work from the same source files with agent-specific adaptations, ensuring consistency across platforms.

### 🎯 Context-Aware Targeting
Rules automatically apply to relevant files and contexts using glob patterns and intelligent filtering.

### 🤖 Agent-Specific Optimization
Each AI tool receives documentation optimized for its capabilities and interface patterns.

### 📚 Intelligent Content Reuse
VitePress include system prevents duplication while maintaining content freshness.

### ✅ Automatic Validation
Built-in validation prevents configuration conflicts and ensures clean rule generation.

## Managing Rules

### Adding New Rules
1. Create a new `.md` file in the appropriate subdirectory (`agents/`, `commands/`, or `hooks/`)
2. Add YAML configuration for each target AI tool
3. Include relevant content and VitePress includes
4. Update the sidebar navigation in `docs/.vitepress/config.mts`
5. Run generation to create tool-specific files

### Updating Existing Rules
1. Edit the source markdown file in `docs/ai/`
2. Modify YAML configuration as needed
3. Run `pnpm run ai-rules:generate` to update all generated files

### Rule Categories
- **Agents**: Specialized AI assistants for specific development tasks
- **Commands**: Workflow commands and development operations
- **Hooks**: Automated validation and pre-commit processes

## Integration with AWA

This system extends AWA's philosophy of "Easy. Compatible. Useful." by providing:
- **Easy**: Simple markdown-based configuration
- **Compatible**: Works with existing documentation workflows
- **Useful**: Delivers immediate value through consistent AI guidance

## Troubleshooting

### Common Issues
- **Rules not appearing**: Check `include_in_index: true` in YAML configuration
- **Content not updating**: Run `pnpm run ai-rules:generate` after source changes
- **Path resolution errors**: Verify VitePress include paths are correct
- **Agent-specific issues**: Check individual agent configuration sections

### Validation Commands
```bash
# List all discovered rules and configurations
python scripts/ai-documentation-generator/tools/generate_multi_rules.py list

# Validate configuration syntax
python scripts/ai-documentation-generator/tools/generate_multi_rules.py validate

# Generate for specific agent only
python scripts/ai-documentation-generator/tools/generate_multi_rules.py generate --agent claude
```

## File Structure

```
docs/ai/
├── index.md                 # This overview page
├── core-instructions.md     # Foundational guidance
├── agents/                  # Individual agent configurations
│   ├── bitbucket-api-operator.md
│   ├── code-author.md
│   └── ...
├── commands/                # Development commands
│   ├── baml-development.md
│   ├── python-development.md
│   └── ...
└── hooks/                   # Pre-commit hooks
    └── stop-lint.md
```

The AI Rules system ensures that all AI development tools working with AWA have access to consistent, comprehensive, and contextually relevant guidance for effective collaboration.
