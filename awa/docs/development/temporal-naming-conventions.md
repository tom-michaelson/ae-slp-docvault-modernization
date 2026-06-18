# Temporal Naming Conventions

AWA uses the following naming conventions for Temporal workflows and activities.

## General

- Use explicit names (never rely on the auto-generated name derived from code symbols)
- Use kabob case to cleanly match naming conventions across languages (don't use C#'s PascalCase or Python's snake_case)
- Prefix all AWA core workflows and activities with `awa-`
- Use verb phrases
- Don't use suffixes like `workflow` or `activity`
- Use python constants, defined in `awa.core.constants`, for workflow and activity names

## Workflows

**Format**: `awa-{verb phrase}`

**Examples**:

- `awa-build-prompt`
- `awa-transform-batch`

## Activities

**Format**: `awa-{verb phrase}`

**Examples**:

- `awa-read-file`
- `awa-invoke-mcp-tool`
