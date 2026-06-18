# Python Development Guide

## Configuration

```yaml
cursor:
  description: "Python development standards, Temporal patterns, and AWA conventions"
  globs: "**/*.py"
  include_in_index: true

copilot:
  output_type: "instructions"
  description: "Python development standards and Temporal patterns"
  applyTo: '**/*.py'
  include_in_index: true

claude:
  command_name: "python-development"
  description: "Python development standards and Temporal integration patterns"
  include_in_index: true

opencode:
  command_name: "python-development"
  description: "Python development standards and Temporal integration patterns"
  include_in_index: true
```

This guide provides comprehensive Python development standards and Temporal patterns for AWA development, covering code style, error handling, logging, workflow patterns, and activities.

## Python Development Standards

<!--@include: ../development/python-standards.md -->

## Temporal Workflow and Activity Patterns

<!--@include: ../development/temporal-patterns.md -->

## Project Integration

When working with Python in AWA projects:

1. **Code Organization**: Follow AWA's module structure with clear separation between workflows and activities
2. **Dependencies**: Use `uv` for dependency management and virtual environments
3. **Testing**: Write unit tests for activities and integration tests for workflows
4. **Configuration**: Use AWA's configuration patterns with Pydantic models

## Development Workflow

1. **Setup**: Use `make install` to set up development environment
2. **Linting**: Run `make lint` and `make format` before committing
3. **Testing**: Use `make test` for unit tests, `make test-workflow` for integration tests
4. **Type Checking**: Ensure all code passes mypy type checking

## Performance Considerations

- Use async/await patterns consistently throughout the codebase
- Leverage Temporal's built-in retry mechanisms for resilience
- Implement proper resource cleanup in activities
- Monitor workflow execution times and optimize where needed
