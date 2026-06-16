# Python Utility Function Conventions

## Overview
This document defines the Python conventions for generating utility functions in the AWA SDK. These conventions ensure consistency with the existing Python SDK models and follow Python best practices.

## Naming Conventions

### Classes
- **Convention**: PascalCase for class names
- **Example**: `MyUtil`, `DataProcessor`, `ValidationHelper`
- **Rationale**: Consistent with generated SDK model classes

### Methods
- **Convention**: snake_case for method names
- **Example**: `my_util_function`, `process_data`, `validate_input`
- **Rationale**: Follows Python PEP 8 style guidelines

### Variables and Parameters
- **Convention**: snake_case for all variables and parameters
- **Example**: `input_model`, `output_data`, `is_valid`
- **Rationale**: Consistent with Python conventions and SDK model properties

### Properties
- **Convention**: snake_case for properties (consistent with generated models)
- **Example**: `prop_a`, `prop_b`, `prop_c`
- **Rationale**: Matches existing SDK model property naming

## Class Structure

### Utility Classes
```python
class MyUtil:
    @staticmethod
    def my_util_function(input_model: MyInputModel) -> MyOutputModel:
        # Implementation
        pass
```

### Key Patterns:
- Use static methods for utility functions
- No instance variables or constructors needed
- Group related utility functions in the same class

## Method Signatures

### Static Methods
```python
@staticmethod
def method_name(parameter_name: ParameterType) -> ReturnType:
    # Implementation
    pass
```

### Type Annotations
- **Required**: All parameters and return types must have type annotations
- **Import Style**: Use direct imports from SDK models
- **Optional Types**: Use `Optional[Type]` for nullable parameters
- **Union Types**: Use `Union[Type1, Type2]` for multiple possible types

## Import Conventions

### SDK Model Imports
```python
from awa.client.models.Models import MyInputModel, MyOutputModel, MyChildOutputModel
```

### Standard Library Imports
```python
from typing import Optional, Union, List, Dict, Any
```

### Import Order
1. Standard library imports
2. Third-party imports
3. Local/SDK imports

## Model Instantiation Patterns

### Creating New Models
```python
# Simple model creation
output_model = MyOutputModel(
    prop_c=MyChildOutputModel(prop_e=input_model.prop_a),
    prop_d=True
)

# With optional parameters
output_model = MyOutputModel(
    prop_c=child_model if condition else None,
    prop_d=some_boolean_value
)
```

### Accessing Model Properties
```python
# Direct property access
value = input_model.prop_a
optional_value = input_model.prop_b  # May be None

# Safe access with defaults
value = input_model.prop_b or 0
```

## Error Handling Patterns

### Basic Validation
```python
@staticmethod
def validate_and_process(input_model: MyInputModel) -> MyOutputModel:
    if not input_model.prop_a:
        raise ValueError("prop_a is required")

    # Process the input
    return MyOutputModel(
        prop_c=MyChildOutputModel(prop_e=input_model.prop_a),
        prop_d=True
    )
```

### Exception Types
- Use `ValueError` for invalid input data
- Use `TypeError` for incorrect types
- Use `AttributeError` for missing properties

## Documentation Patterns

### Method Documentation
```python
@staticmethod
def my_util_function(input_model: MyInputModel) -> MyOutputModel:
    """
    Process input model and return transformed output.

    Args:
        input_model: The input data to process

    Returns:
        MyOutputModel: The processed output data

    Raises:
        ValueError: If input_model is invalid
    """
    # Implementation
    pass
```

### Class Documentation
```python
class MyUtil:
    """
    Utility functions for processing AWA SDK models.

    This class provides static methods for common data transformations
    and processing operations on SDK models.
    """
```

## File Organization

### Directory Structure
```
awa/
├── client/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   └── Models.py
│   └── utils/
│       ├── __init__.py
│       ├── activity/
│       │   ├── __init__.py
│       │   └── MyActivityUtil.py
│       ├── workflow/
│       │   ├── __init__.py
│       │   └── MyWorkflowUtil.py
│       └── general/
│           ├── __init__.py
│           └── MyGeneralUtil.py
```

### Utility Organization
- **Convention**: Utilities are organized into three subdirectories
- **activity/**: Contains utility functions that interact with Temporal activities
- **workflow/**: Contains utility functions that work within Temporal workflows
- **general/**: Contains general-purpose utility functions used by both activities and workflows

### File Naming
- **Convention**: PascalCase for utility class files
- **Example**: `MyUtil.py`, `DataProcessor.py`
- **Rationale**: Matches class name for clarity

## Testing Patterns

### Unit Test Structure
```python
import unittest
from awa.client.models.Models import MyInputModel, MyOutputModel
from awa.client.utils.activity.MyActivityUtil import MyActivityUtil
from awa.client.utils.workflow.MyWorkflowUtil import MyWorkflowUtil
from awa.client.utils.general.MyGeneralUtil import MyGeneralUtil

class TestMyUtil(unittest.TestCase):
    def test_my_util_function(self):
        # Arrange
        input_model = MyInputModel(prop_a="test", prop_b=42)

        # Act
        result = MyWorkflowUtil.my_util_function(input_model)

        # Assert
        self.assertIsInstance(result, MyOutputModel)
        self.assertEqual(result.prop_c.prop_e, "test")
        self.assertTrue(result.prop_d)
```

## Code Style Guidelines

### Formatting
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black formatter standard)
- Use trailing commas in multi-line structures

### Comments
- Use `#` for inline comments
- Use `"""` for docstrings
- Comment complex logic and business rules

### Blank Lines
- Two blank lines between classes
- One blank line between methods
- One blank line between logical sections within methods
