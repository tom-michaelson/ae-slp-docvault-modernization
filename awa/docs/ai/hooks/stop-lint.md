# Stop Lint Hook

This hook automatically runs linting after Claude Code finishes responding to ensure code quality.

## Configuration

```yaml
claude:
  hook: true
  output_location: ".claude/hooks/"
  filename: "stop-lint.sh"
```

## Hook Content

```bash
#!/bin/bash

# Claude Code Stop hook - runs make lint-fix when Claude finishes responding
# Exit code 2 indicates a blocking error that should be shown to Claude

echo "Running linter..."

# Change to project root directory
cd "$CLAUDE_PROJECT_DIR" || exit 2

# Run the lint-fix command
make lint-fix

# Capture the exit code
LINT_EXIT_CODE=$?

# If linting failed, return exit code 2 to block and show error to Claude
if [ $LINT_EXIT_CODE -ne 0 ]; then
    echo "Linting failed with exit code $LINT_EXIT_CODE" >&2
    exit 2
fi

echo "Linting completed successfully"
exit 0
```</content>
<parameter name="filePath">docs/ai/hooks/stop-lint.md
