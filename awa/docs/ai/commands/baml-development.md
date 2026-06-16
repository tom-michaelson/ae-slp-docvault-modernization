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

opencode:
  command_name: "baml-development"
  description: "BAML development guide with best practices and Python integration"
  include_in_index: true
```

This guide provides comprehensive patterns and best practices for BAML development, including schema design, function patterns, prompt engineering, testing, and Python integration.

## BAML Development Patterns

<!--@include: ../development/baml-patterns.md -->

## AWA Integration

<!--@include: ../development/baml-integration.md -->
