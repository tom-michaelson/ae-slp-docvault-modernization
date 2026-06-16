# Documentation Generation Guide

## Configuration

```yaml
cursor:
  description: "Documentation generation patterns for workflows and activities"
  globs: "**/*_workflow.py, **/*_activity.py, **/docs/**"
  include_in_index: true

copilot:
  output_type: "instructions"
  description: "Automated documentation generation guidelines"
  applyTo: '**/*_workflow.py, **/*_activity.py'
  include_in_index: true

claude:
  command_name: "docs-generation"
  description: "Documentation generation patterns and automation"
  include_in_index: true

opencode:
  command_name: "docs-generation"
  description: "Documentation generation patterns and automation"
  include_in_index: true
```

This guide provides patterns for generating comprehensive SDK-style reference documentation for AWA workflows and activities, including multi-language usage examples.

<!--@include: ../contributing/docs-generation.md -->
