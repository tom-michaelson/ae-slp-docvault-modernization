# AI Documentation Generator

The AI Documentation Generator is a core component of the AWA toolkit that automates the creation of context-specific documentation and rules for multiple AI development tools.

## Purpose

This component solves the problem of maintaining AI tool configurations across different platforms while preserving granular, context-specific targeting. Instead of creating massive monolithic files that lose context specificity, it generates targeted rule files that maintain the precision of manual curation while eliminating duplication.

## Architecture

### Core Components

- **Source Rules**: Modular markdown files with embedded YAML configuration and VitePress includes
- **VitePress Include Processor**: Intelligent system that processes `<!--@include: -->` directives to pull content from existing files
- **Multi-Tool Generator**: Creates optimized files for Cursor, GitHub Copilot, and Claude
- **Dynamic Discovery**: Automatically discovers source files in the `docs/ai/` directory

### Design Philosophy

1. **Embedded Configuration**: Each source rule has YAML frontmatter that defines how it should be adapted for each AI tool
2. **VitePress Integration**: Uses VitePress include syntax to reference existing documentation instead of duplicating content
3. **Context Preservation**: Maintains semantic meaning and application scope through intelligent targeting
4. **Single Source Management**: All AI tools work from the same source files with tool-specific adaptations

## Source File Structure

### Source Rules (`.md` files in `docs/ai/`)

Each source rule file contains embedded YAML configuration and VitePress includes:

````markdown
# BAML Development Guide

## Configuration

```yaml
cursor:
  description: "BAML development patterns, best practices, and Python integration"
  globs: "**/*.baml, **/baml_src/**/*.py"
  include_in_index: true

copilot:
  output_type: "instructions"
  description: "BAML development guidelines and integration patterns"
  applyTo: '**/*.baml, **/baml_src/**/*.py'
  include_in_index: true

claude:
  command_name: "baml-development"
  description: "BAML development guide with best practices and Python integration"
  include_in_index: true
```
````

This file provides guidance to Claude Code when working with code in this repository.

## What is AWA?

<!--@include: ../ai/includes/projectoverview.md -->

## Essential Development Commands

<!--@include: ../ai/includes/developmentcommands.md -->

```

### Include Files (`docs/ai/includes/`)

Reusable content blocks that can be included across multiple source files:

```

docs/ai/includes/
├── projectoverview.md # Project description and purpose
├── developmentcommands.md # Make commands and usage
└── ... # Other reusable content blocks

````

## Generated Output Structure

### Global Files (Base Rules)

Files marked with `base_rule: true` generate global instruction files:

- **`CLAUDE.md`** - Global Claude Code instructions (project root)
- **`.github/copilot-instructions.md`** - Global GitHub Copilot instructions
- **`.cursor/rules/core-instructions.mdc`** - Global Cursor rules with YAML frontmatter

### Context-Specific Files

Files with targeting configuration generate context-specific rules:

- **`.cursor/rules/*.mdc`** - Cursor rules with YAML frontmatter and `globs` targeting
- **`.github/instructions/*.md`** - GitHub Copilot instructions with YAML frontmatter and `applyTo` field
- **`.claude/commands/*.md`** - Claude command-specific files

#### Example Generated GitHub Copilot Instruction File

```yaml
---
description: 'TypeScript patterns for Azure Functions'
applyTo:
- '**/*.ts'
- '**/*.js'
- '**/*.json'
---

## Guidance for Code Generation
- Generate modern TypeScript code for Node.js
- Use `async/await` for asynchronous code
...
```

## VitePress Include System

The generator processes VitePress-style include directives:

```markdown
# Include entire file
<!--@include: ../includes/projectoverview.md -->

# Include with comment
<!--@include: ../includes/commands.md --> <!-- Development commands -->
````

**Important**: Include file paths cannot contain hyphens due to regex limitations in the processor. Use camelCase or underscores instead.

### Path Resolution

Include paths are resolved relative to the project root:

- `../ai/includes/file.md` resolves to `docs/ai/includes/file.md`
- `../introduction/file.md` resolves to `docs/introduction/file.md`

## Usage

### Command Line Interface

```bash
# Generate all AI tool files
python scripts/ai-documentation-generator/tools/generate_multi_rules.py generate

# Generate for specific tool
python scripts/ai-documentation-generator/tools/generate_multi_rules.py generate --agent cursor

# Validate source files and metadata
python scripts/ai-documentation-generator/tools/generate_multi_rules.py validate

# Clean generated files
python scripts/ai-documentation-generator/tools/generate_multi_rules.py clean

# List available source files
python scripts/ai-documentation-generator/tools/generate_multi_rules.py list
```

### AWA Integration Commands

```bash
# Clean all generated AI rule files
make clean                 # Clean all project files (includes AI rules)
make ai-rules-clean        # Clean only AI rule files

# Generate AI rule files (typically done automatically)
pnpm run ai-rules:generate # Generate all AI rule files manually
```

**Typical Workflow**: AI rules are automatically generated during standard development commands:
- `make install` (full project setup)
- `make docs-prep` (documentation preparation)
- `pnpm run docs:build` (documentation build)

**Manual Generation**: You typically don't need to run generation commands manually since they're included in the standard workflow. However, if you need to regenerate rules after editing source files in `docs/ai/`, you can run `pnpm run ai-rules:generate`.

## Configuration Reference

### YAML Configuration Options

Each source file supports the following configuration:

#### Cursor Configuration

```yaml
cursor:
  description: "Description for Cursor rules"
  globs: ["**/*.py", "**/*.ts"] # File patterns to target (string or array)
  alwaysApply: true # Optional: Apply to all files regardless of globs
  include_in_index: true # Include in Cursor-specific rule index
```

#### Copilot Configuration

```yaml
copilot:
  base_rule: true # Optional: Generate global copilot-instructions.md
  description: "Description for Copilot instructions or prompts"
  applyTo: '**/*.py' # File patterns for instructions (ONLY used with output_type: "instructions")
  output_type: "instructions" # "instructions" or "prompts"
  include_in_index: true # Include in Copilot-specific rule index
```

**Copilot Output Types:**

- **Instructions** (`output_type: "instructions"`): Include both `description` and `applyTo` in YAML frontmatter
  ```yaml
  ---
  description: "Python development standards and Temporal patterns"
  applyTo: '**/*.py'
  ---
  ```

- **Prompts** (`output_type: "prompts"`): Include only `description` in YAML frontmatter (no `applyTo`)
  ```yaml
  ---
  description: "Specification writing for JIRA tickets and development planning"
  ---
  ```

#### Claude Configuration

```yaml
claude:
  base_rule: true # Optional: Generate global CLAUDE.md
  command_name: "command-name" # Name for command files (required for slash commands)
  description: "Description for Claude command"
  output_location: ".claude/commands/" # Optional: Custom output directory
  include_in_index: true # Include in Claude-specific rule index (slash commands)
```

### Key Features

#### Agent-Specific Configuration Separation

Each AI agent (Cursor, Copilot, Claude) maintains completely independent configurations. No cross-contamination occurs - Claude settings never influence Copilot output, and vice versa. Each agent respects only its own configuration section.

#### Dynamic Agent-Specific Rule Indexes

Files with `include_in_index: true` automatically appear in agent-specific rule indexes:

- **Claude**: Shows slash commands (e.g., `/baml-development: BAML development guide`)
- **Cursor**: Shows rule descriptions for context-aware development
- **Copilot**: Shows instruction descriptions for code generation guidance

#### Intelligent Content Deduplication

The VitePress include processor automatically removes duplicate headers and content when including files, preventing content duplication in generated outputs. This ensures clean, professional documentation without redundant sections.

#### Base Rule Validation

The generator validates that only one rule file has `base_rule: true` per agent, preventing configuration conflicts and overwrites. This ensures clean base rule generation.

#### Enhanced Integration

Automatic generation during `make install`, `make docs-prep`, and `pnpm run docs:build` ensures AI rules are always up-to-date.

## File Naming Conventions

- **Source files**: Use kebab-case (e.g., `core-instructions.md`, `baml-development.md`)
- **Include files**: Use camelCase or underscores (no hyphens due to regex limitations)
- **Generated files**: Follow tool-specific conventions

## Workflow

1. **Create/Edit Source Files**: Add or modify `.md` files in `docs/ai/`
2. **Add Include Files**: Create reusable content in `docs/ai/includes/`
3. **Configure Tools**: Set up YAML configuration for each AI tool
4. **Update VitePress Sidebar**: Add the new rule to `docs/.vitepress/config.mts` in the "AI Rules" section
   - Navigate to the "AI Rules" sidebar configuration (around line 372)
   - Add a new entry: `{ text: "Rule Display Name", link: "/ai/rule-filename" }`
   - The link should match the filename without the `.md` extension
5. **Generate Files**: Run the generation script to create tool-specific files
6. **Commit Changes**: Generated files are committed to version control

### Example: Adding a New AI Rule

When creating a new AI rule file like `docs/ai/my-new-rule.md`:

1. Create the rule file with appropriate YAML configuration
2. Edit `docs/.vitepress/config.mts`:
   ```typescript
   {
     text: "AI Rules",
     collapsed: true,
     items: [
       // ... existing items ...
       { text: "My New Rule", link: "/ai/my-new-rule" },
     ],
   }
   ```
3. Run generation: `make` or `pnpm run ai-rules:generate`
4. The rule will now appear in the VitePress documentation sidebar

## Benefits

1. **Single Source of Truth**: All AI tools work from the same source rules with agent-specific adaptations
2. **Perfect Agent Separation**: Each AI agent maintains completely independent configurations with no cross-contamination
3. **VitePress Integration**: Leverages existing VitePress include system for intelligent content reuse
4. **Intelligent Deduplication**: Automatically removes duplicate headers and content from included files
5. **Embedded Configuration**: No separate metadata files to maintain - everything in one place
6. **Context Awareness**: Each tool gets optimized, targeted documentation specific to its capabilities
7. **Automatic Discovery**: Discovers source files dynamically from `docs/ai/` directory
8. **Agent-Specific Rule Indexes**: Self-maintaining directory of available rules tailored to each agent type
9. **Configuration Validation**: Prevents conflicts with base rule validation and ensures clean generation
10. **Build Integration**: Automatic generation during development workflows ensures consistency
11. **Professional Output**: Clean, non-duplicated generated content suitable for production use

## Integration with AWA

This component extends the AWA project's philosophy of "Easy. Compatible. Useful." by:

- **Easy**: Simple file-based configuration with embedded YAML
- **Compatible**: Works with existing VitePress documentation system
- **Useful**: Provides immediate value through automated consistency and intelligent content inclusion

## Troubleshooting

### Common Issues

1. **Includes not processing**: Check that include file paths don't contain hyphens
2. **Files not discovered**: Ensure source files are in `docs/ai/` directory
3. **YAML parsing errors**: Validate YAML syntax in configuration blocks
4. **Path resolution errors**: Verify include paths are correct relative to project root
5. **Content duplication**: This should no longer occur due to intelligent deduplication, but if seen, check VitePress include syntax
6. **Missing from rule index**: Ensure `include_in_index: true` is set for the specific agent you want to include the rule for
7. **Cross-agent contamination**: Each agent section is independent - make sure you're configuring the right agent section

### Debug Tips

- Use the `list` command to see discovered source files and their agent configurations
- Use the `validate` command to check configuration syntax and base rule conflicts
- Check that include files exist at the resolved paths
- Ensure proper spacing in VitePress include syntax: `<!--@include: path -->`
- Generate for a specific agent to isolate configuration issues: `--agent cursor`
- Check generated rule indexes to verify `include_in_index` settings are working correctly
- Compare base rule files (.cursor/rules/core-instructions.mdc, .github/copilot-instructions.md, CLAUDE.md) to see agent-specific differences

This represents a sophisticated approach to AI tool documentation that maintains the benefits of manual curation while providing the automation and consistency of generated content.
