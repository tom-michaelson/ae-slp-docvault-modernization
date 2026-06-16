# Prompts and Templates

AWA provides powerful capabilities for working with prompts and templates, enabling flexible content generation, transformation, and templating workflows. These features make it easy to integrate Large Language Models (LLMs) and template engines into your applications.

## Overview

AWA offers three core capabilities for prompts and templates:

- **`awa-transform`**: Execute BAML-powered LLM prompts to transform text content
- **`awa-transform-batch`**: Process multiple transformations in parallel for efficient batch operations
- **`awa-resolve-template`**: Render Jinja2 templates with dynamic variables

These features work together to provide a comprehensive solution for content generation, data transformation, and templating needs.

## Transform Workflows

Transform workflows leverage [BAML (Boundary ML)](https://docs.boundaryml.com/home) to execute LLM-powered transformations on your content. BAML provides structured prompt definition, type-safe inputs/outputs, and multi-provider LLM support.

### Single Transform

The `awa-transform` workflow executes a single BAML function with provided input, making it perfect for straightforward content transformations.

**Common use cases:**
- Text summarization and analysis
- Code generation and refactoring
- Content translation and formatting
- Data extraction and parsing
- Creative writing assistance

See the workflow reference documentation for [`awa-transform`](/reference/workflow/transform.md).

### Batch Transform

The `awa-transform-batch` workflow orchestrates multiple transform operations in parallel, enabling efficient processing of large datasets or multiple related transformations.

**Common use cases:**
- Processing multiple documents simultaneously
- Running different analyses on the same content (e.g., summary + translation + sentiment)
- Parallel code generation for multiple components
- Batch content creation with different parameters
- Multi-model comparisons (running the same prompt against different LLMs)

See the workflow reference documentation for [`awa-transform-batch`](/reference/workflow/transform-batch.md).

## Template Resolution

The `awa-resolve-template` workflow renders Jinja2 templates with provided variables, making it easy to generate dynamic content from templates.

**Common use cases:**
- Configuration file generation
- Report and document generation
- Email and notification templates
- Code scaffolding and boilerplate generation
- Dynamic content creation for web applications

See the workflow reference documentation for [`awa-resolve-template`](/reference/workflow/resolve-template.md).

## BAML Integration

AWA's transform capabilities are built on [BAML (Boundary ML)](https://docs.boundaryml.com/home), which provides:

- **Structured Prompts**: Define prompts with clear inputs and outputs using BAML's type system
- **Multi-Provider Support**: Use different LLM providers (OpenAI, Anthropic, Azure OpenAI, etc.) with the same prompt definitions
- **Prompt Playground**: Test and iterate on prompts using BAML's VS Code extension
- **Type Safety**: Ensure correct data types for inputs and outputs with compile-time validation

For more information on working with BAML in AWA, see the [BAML development guide](/development/baml.md).

## How It Works

### Transform Processing Flow

1. **Input**: Provide text content and transformation instructions
2. **BAML Execution**: AWA generates a BAML client for your function and executes it
3. **LLM Processing**: The prompt is sent to your configured LLM provider
4. **Result**: Structured output is returned according to your BAML function definition

### Template Processing Flow

1. **Template Loading**: Read the Jinja2 template file from the specified path
2. **Variable Substitution**: Apply provided variables to template placeholders
3. **Rendering**: Generate the final content with resolved variables
4. **Output**: Write the rendered content to the specified output file

## Getting Started

To start using prompts and templates in your workflows:

1. **Set up LLM Configuration**: Configure your preferred LLM providers in `config.yaml`
2. **Define BAML Functions**: Create `.baml` files with your prompt definitions (for transforms)
3. **Create Templates**: Write Jinja2 templates for dynamic content generation
4. **Execute Workflows**: Use the transform and template workflows in your applications

For hands-on examples, explore the [AWA 101 tutorials](/cookbook/tutorials/awa-101/) which demonstrate these capabilities in action.
