---
outline: 2
---

# Pydantic Models for Workflow Input

When defining input schema for workflows, Pydantic Basemodels are leveraged to convert the schema to JSON, and rendered on the frontend with **jsonforms**. It's important to ensure that the models are correctly formatted for JSON conversion. This will help avoid issues with how fields are displayed in the frontend, and ensure valid inputs are used to initiate workflows.

## Key Guidelines

### Using Pipe Operators

When defining fields in Pydantic models, if you are using pipe operators to define secondary types (i.e., `str | None`), it is important to wrap the secondary type portion in `SkipJsonSchema`. This is cruical for ensuring that the fields display correctly on the frontend, and do not appear as `AnyOf` field.

#### Example

Instead of defining a field like this:

```python
from pydantic import BaseModel

class WorkflowInput(BaseModel):
    my_field: str | None
```

You should define it as follows:

```python
from pydantic import BaseModel
from pydantic.json_schema import SkipJsonSchema

class WorkflowInput(BaseModel):
    my_field: str | SkipJsonSchema[None]
```

When in doubt, input renderers can be validated within the Execute Workflow modal in the ui `/runs` page.

## JSON Input Format Requirements

All workflows initiated via the UI, API, or CLI must accept either:
- **No input** (empty input field)
- **A JSON object as input** (provided as a string)

This standardization ensures consistent error handling and validation across all workflow execution methods.

### Valid Input Examples

**No Input:**
```json
{
  "name": "my-workflow",
  "input": ""
}
```

**JSON Object Input:**
```json
{
  "name": "my-workflow",
  "input": "{\"field1\": \"value1\", \"field2\": 123}"
}
```

### Invalid Input Examples

**Primitive values (not supported):**
```json
{
  "name": "my-workflow",
  "input": "just a string"
}
```

**Malformed JSON:**
```json
{
  "name": "my-workflow",
  "input": "{invalid json"
}
```

### API Error Handling

When invalid JSON is provided in the input field, the API will return:
- **Status Code:** 400 Bad Request
- **Error Message:** "Invalid JSON format in input field"

This helps clients understand and correct their requests quickly.

### Workflow Design Guidelines

When creating new workflows, ensure they follow this pattern:
- Accept a single Pydantic model as input (which represents a JSON object)
- Or accept no input parameters
- Avoid workflows that require primitive types (strings, numbers) as direct input
