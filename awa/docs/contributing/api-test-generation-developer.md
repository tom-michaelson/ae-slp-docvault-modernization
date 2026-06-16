# API Test Generation - Developer Guide

This document provides implementation details for developers working on or extending the API test generation system.

## Overview

The API test generation system is a comprehensive framework that automatically creates tests and test data from OpenAPI specifications. This guide focuses on the internal architecture and extension points.

## Architecture

### Directory Structure

```
tests/api/generation/
├── generate_api_tests.py      # Main API test generator
├── generate_test_data.py      # Main test data generator
├── __main__.py                # CLI entry point
├── core/                      # Core generation components
│   ├── constants.py           # Shared constants
│   ├── validation.py          # Validation utilities
│   ├── schema_parser.py       # OpenAPI schema parsing
│   ├── data_writer.py         # File writing operations
│   ├── data_manager.py        # Test data loading and management
│   ├── field_generators.py    # Field value generation strategies
│   └── workflow_templates.py  # Workflow-specific templates
└── README.md                  # This file
```

### Core Components

#### **SchemaParser**

- Parses OpenAPI specifications
- Extracts schema definitions and endpoint information
- Validates schema structure

#### **FieldGeneratorRegistry**

- Strategy pattern for field value generation
- Specific generators for workflow fields (name, version, task_queue)
- Type-based generators for primitives (string, int, boolean)
- Extensible with custom generators

#### **DataWriter**

- Handles all file writing operations
- Generates basic, variant, and invalid payload files
- Manages output directory structure

#### **WorkflowTemplateRegistry**

- Provides workflow-specific test data templates
- Supports curated examples for complex workflows
- Extensible with custom workflow providers

#### **DataManager**

- Loads existing test data files
- Manages both manual and generated test data
- Provides schema-to-file mapping

## Usage Examples

### Basic Usage

```python
from tests.api.generation import TestDataGenerator
from awa.core.api.api import Api

# Create API instance and generate OpenAPI spec
api = Api()
openapi_spec = get_openapi(
    title="AWA API",
    version="1.0.0",
    routes=api.app.routes,
)

# Generate test data
generator = TestDataGenerator(openapi_spec)
generated_data = generator.generate_all_endpoint_data()
```

### Custom Field Generator

```python
from tests.api.generation.core.field_generators import BaseFieldGenerator

class CustomFieldGenerator(BaseFieldGenerator):
    def can_generate(self, field_name: str, field_schema: dict) -> bool:
        return field_name == "custom_field"

    def generate_value(self, field_name: str, field_schema: dict, variant: str):
        return f"custom-{variant}-value"

# Register the custom generator
generator.register_custom_field_generator(CustomFieldGenerator())
```

### Custom Workflow Provider

```python
from tests.api.generation.core.workflow_templates import WorkflowTemplateProvider, WorkflowTemplate

class CustomWorkflowProvider(WorkflowTemplateProvider):
    def get_templates(self) -> list[WorkflowTemplate]:
        return [
            WorkflowTemplate(
                description="Custom workflow example",
                workflow_name="my-custom-workflow",
                input_data='{"custom": "data"}'
            )
        ]

    def get_supported_workflows(self) -> list[str]:
        return ["my-custom-workflow"]

# Register the custom provider
generator.register_custom_workflow_provider(CustomWorkflowProvider())
```

## Test Data Types

### Generated Files

- **`*_basic.json`**: Simple, valid payloads for basic testing
- **`*_variants.json`**: Multiple payload variants including workflow-specific examples
- **`*_invalid.json`**: Invalid payloads for error handling tests

### File Organization

```
tests/api/test-data/
├── generated/                    # Auto-generated files (in .gitignore)
│   ├── workflow_run_payload_basic.json
│   ├── workflow_run_payload_variants.json
│   ├── workflow_run_payload_invalid.json
│   ├── worker_registration_basic.json
│   ├── worker_registration_variants.json
│   └── worker_registration_invalid.json
├── hello_human_inputs.json      # Manual test data
├── hello_world_inputs.json      # Manual test data
├── transform_inputs.json        # Manual test data
└── README.md
```

## Configuration

### Constants

Key configuration options in `core/constants.py`:

- `MAX_INVALID_CASES`: Maximum number of invalid test cases (default: 10)
- `MAX_OPTIONAL_FIELDS`: Maximum optional fields in variants (default: 2)
- `MAX_ARRAY_ITEMS`: Maximum array items in generated data (default: 2)

### Supported Workflows

The system includes templates for:

- `awa-hello-human`
- `awa-hello-world`
- `awa-transform`
- `awa-build-prompt`
- `awa-execute-agent`

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Run from project root
python -m tests.api.generation.generate_test_data
```

#### Missing Test Data

Check that OpenAPI specification is valid and contains POST/PUT endpoints with request bodies.

#### Invalid Generated Data

Verify schema definitions in the OpenAPI spec and ensure required fields are properly marked.

### Debug Mode

Enable debug logging for detailed generation information:

```python
import logging
logging.getLogger("AWA").setLevel(logging.DEBUG)
```

## Contributing

### Adding New Field Generators

1. Create a new generator class inheriting from `BaseFieldGenerator`
2. Implement `can_generate()` and `generate_value()` methods
3. Add to `FieldGeneratorRegistry._setup_default_generators()`

### Adding New Workflow Templates

1. Create a new provider class inheriting from `WorkflowTemplateProvider`
2. Implement `get_templates()` and `get_supported_workflows()` methods
3. Add to `WorkflowTemplateRegistry._setup_default_providers()`

### Testing Changes

```bash
make lint                     # Check code quality
make test-api                # Test generated API tests
python -m tests.api.generation.generate_test_data  # Test data generation
```

## Related Documentation

- **[API Test Documentation](./api-testing.md)** - Main API test documentation and user guide
- **[Main Project Documentation](/introduction/)** - AWA project documentation
