# ruff: noqa: ANN401
# Import the functions from the script
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

# Calculate project root correctly from tests/unit/scripts/test_generate_api_reference_docs.py
test_file_path = Path(__file__).resolve()
# Go up 3 levels: tests/unit/scripts/test_generate_api_reference_docs.py -> project_root
project_root = test_file_path.parents[3]

# Import the script as a module
script_path = project_root / "scripts" / "generate_api_reference_docs.py"
spec = importlib.util.spec_from_file_location(
    "generate_api_reference_docs",
    script_path,
)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for {script_path}")
generate_api_reference_docs_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_api_reference_docs_module)

# Import the functions we need to test
format_parameter = generate_api_reference_docs_module.format_parameter
extract_field_descriptions = generate_api_reference_docs_module.extract_field_descriptions
format_schema = generate_api_reference_docs_module.format_schema
get_type_string = generate_api_reference_docs_module.get_type_string
format_response = generate_api_reference_docs_module.format_response
get_method_badge = generate_api_reference_docs_module.get_method_badge
generate_endpoint_doc = generate_api_reference_docs_module.generate_endpoint_doc
generate_api_reference_docs = generate_api_reference_docs_module.generate_api_reference_docs


@pytest.fixture
def test_setup() -> Any:
    """Set up test environment with temporary directory."""
    test_dir = Path(tempfile.mkdtemp())
    docs_dir = test_dir / "docs" / "reference"
    docs_dir.mkdir(parents=True)
    api_docs_path = docs_dir / "api.md"
    openapi_path = docs_dir / "openapi.json"

    yield {
        "test_dir": test_dir,
        "docs_dir": docs_dir,
        "api_docs_path": api_docs_path,
        "openapi_path": openapi_path,
    }

    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)


def test_format_parameter() -> None:
    """Test format_parameter function."""
    # Test required parameter
    param = {
        "name": "workflow_id",
        "type": "string",
        "required": True,
        "description": "The ID of the workflow",
        "in": "path",
    }
    result = format_parameter(param)
    assert "**`workflow_id`**" in result
    assert "(`string`)" in result
    assert '<Badge type="info" text="path" />' in result
    assert '<Badge type="warning" text="required" />' in result
    assert "The ID of the workflow" in result

    # Test optional parameter
    param = {
        "name": "limit",
        "type": "integer",
        "required": False,
        "in": "query",
    }
    result = format_parameter(param)
    assert '<Badge type="tip" text="optional" />' in result


def test_extract_field_descriptions() -> None:
    """Test extract_field_descriptions function."""
    description = """
    A workflow configuration model.

    Attributes:
        name: The name of the workflow
        enabled: Whether the workflow is enabled
        timeout: The timeout in seconds
        tags: List of tags for categorization
    """

    result = extract_field_descriptions(description)
    assert result == {
        "name": "The name of the workflow",
        "enabled": "Whether the workflow is enabled",
        "timeout": "The timeout in seconds",
        "tags": "List of tags for categorization",
    }

    # Test with no attributes section
    result = extract_field_descriptions("Simple description")
    assert result == {}


def test_get_type_string() -> None:
    """Test get_type_string function."""
    schemas = {}

    # Test simple type
    schema = {"type": "string"}
    assert get_type_string(schema, schemas) == "string"

    # Test array type
    schema = {"type": "array", "items": {"type": "string"}}
    assert get_type_string(schema, schemas) == "string[]"

    # Test reference
    schema = {"$ref": "#/components/schemas/WorkflowModel"}
    assert get_type_string(schema, schemas) == "WorkflowModel"

    # Test unknown type
    schema = {}
    assert get_type_string(schema, schemas) == "unknown"


def test_format_schema() -> None:
    """Test format_schema function."""
    schemas = {
        "UserModel": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
            },
        },
    }

    # Test object schema
    schema = {
        "type": "object",
        "properties": {
            "workflow_id": {"type": "string", "description": "Workflow identifier"},
            "status": {"type": "string"},
            "config": {"$ref": "#/components/schemas/UserModel"},
        },
        "required": ["workflow_id"],
    }

    result = format_schema(schema, schemas, "")
    assert "| Property | Type | Details |" in result
    assert "| `workflow_id` | `string` |" in result
    assert '<Badge type="warning" text="required" />' in result
    assert "Workflow identifier" in result
    assert "| `config` | `UserModel` |" in result

    # Test array schema
    schema = {"type": "array", "items": {"type": "integer"}}
    result = format_schema(schema, schemas, "")
    assert result == "`integer[]`"

    # Test simple type
    schema = {"type": "boolean"}
    result = format_schema(schema, schemas, "")
    assert result == "`boolean`"


def test_get_method_badge() -> None:
    """Test get_method_badge function."""
    assert get_method_badge("get") == '<Badge type="tip" text="GET" />'
    assert get_method_badge("post") == '<Badge type="info" text="POST" />'
    assert get_method_badge("put") == '<Badge type="warning" text="PUT" />'
    assert get_method_badge("delete") == '<Badge type="danger" text="DELETE" />'
    assert get_method_badge("patch") == '<Badge type="warning" text="PATCH" />'
    assert get_method_badge("options") == '<Badge type="info" text="OPTIONS" />'


def test_format_response() -> None:
    """Test format_response function."""
    schemas = {}

    # Test response with content
    response = {
        "description": "Successful response",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                    },
                },
            },
        },
    }

    result = format_response(response, schemas)
    assert "Successful response" in result
    assert "**Response Schema** (`application/json`):" in result
    assert "| `message` | `string` |" in result

    # Test response without content
    response = {"description": "No content"}
    result = format_response(response, schemas)
    assert result == "No content"


def test_generate_endpoint_doc() -> None:
    """Test generate_endpoint_doc function."""
    schemas = {}

    operation = {
        "summary": "Get workflow by ID",
        "description": "Retrieve a workflow by its unique identifier",
        "tags": ["workflows"],
        "parameters": [
            {
                "name": "workflow_id",
                "in": "path",
                "required": True,
                "type": "string",
                "description": "The workflow ID",
            },
        ],
        "responses": {
            "200": {
                "description": "Workflow found",
                "content": {
                    "application/json": {
                        "schema": {"type": "object", "properties": {"id": {"type": "string"}}},
                    },
                },
            },
            "404": {"description": "Workflow not found"},
        },
    }

    result = generate_endpoint_doc("/workflows/{workflow_id}", "get", operation, schemas)

    # Check structure - the implementation puts summary as main header, method/path as subheader
    assert "### Get workflow by ID" in result
    assert "#### GET `/workflows/{workflow_id}`" in result
    assert "Retrieve a workflow by its unique identifier" in result

    # Check parameters section
    assert "#### Parameters" in result
    assert "**`workflow_id`**" in result

    # Check responses section
    assert "#### Responses" in result
    assert '<Badge type="tip" text="200" />' in result
    assert '<Badge type="warning" text="404" />' in result


@patch.object(generate_api_reference_docs_module, "Api")
@patch.object(generate_api_reference_docs_module, "get_openapi")
@patch.object(generate_api_reference_docs_module, "init_logging")
@patch.object(generate_api_reference_docs_module, "get_logger")
def test_generate_api_reference_docs_success(
    mock_get_logger: Mock,
    mock_init_logging: Mock,
    mock_get_openapi: Mock,
    mock_api_class: Mock,
    test_setup: Any,
) -> None:
    """Test successful API reference documentation generation."""
    # Arrange
    api_docs_path = test_setup["api_docs_path"]
    openapi_path = test_setup["openapi_path"]

    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    # Mock API instance
    mock_api = Mock()
    mock_api.app.title = "Test API"
    mock_api.app.version = "1.0.0"
    mock_api.app.description = "Test API Description"
    mock_api.app.routes = []
    mock_api_class.return_value = mock_api

    # Mock OpenAPI spec
    mock_openapi_spec = {
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API Description",
        },
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {"200": {"description": "Service is healthy"}},
                },
            },
        },
        "components": {
            "schemas": {
                "HealthResponse": {
                    "type": "object",
                    "description": "Health check response",
                    "properties": {"status": {"type": "string"}},
                },
            },
        },
    }
    mock_get_openapi.return_value = mock_openapi_spec

    # Mock Path to use our test directory
    with patch.object(generate_api_reference_docs_module, "Path") as mock_path_class:

        def path_side_effect(path_str: str) -> Any:
            if "docs/reference" in str(path_str):
                return test_setup["docs_dir"]
            return Path(path_str)

        mock_path_class.side_effect = path_side_effect

        # Act
        generate_api_reference_docs()

    # Assert
    mock_init_logging.assert_called_once()
    mock_get_logger.assert_called_once()
    mock_logger.info.assert_called()

    # Check API documentation file
    assert api_docs_path.exists()
    content = api_docs_path.read_text()
    assert "# API Reference" in content
    assert "This documentation is automatically generated from the FastAPI OpenAPI specification." in content
    assert "Test API Description" in content
    assert "/health" in content
    assert "Health check" in content
    assert "## Data Models" in content
    assert "HealthResponse" in content

    # Check OpenAPI JSON file
    assert openapi_path.exists()
    openapi_content = json.loads(openapi_path.read_text())
    assert openapi_content == mock_openapi_spec


@patch.object(generate_api_reference_docs_module, "Api")
@patch.object(generate_api_reference_docs_module, "init_logging")
@patch.object(generate_api_reference_docs_module, "get_logger")
def test_generate_api_reference_docs_exception(
    mock_get_logger: Mock,
    _mock_init_logging: Mock,
    mock_api_class: Mock,
) -> None:
    """Test API reference documentation generation with exception."""
    # Arrange
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger

    # Make API creation raise an exception
    mock_api_class.side_effect = Exception("API initialization failed")

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        generate_api_reference_docs()

    assert "API initialization failed" in str(excinfo.value)
    mock_logger.exception.assert_called_with("Failed to generate API reference documentation")


def test_extract_field_descriptions_edge_cases() -> None:
    """Test extract_field_descriptions with edge cases."""
    # Test with malformed attributes
    description = """
    Attributes:
        field1: desc1
        field with spaces: should be ignored
        field2:desc2 with no space after colon
        : empty field name
        field3:
    """

    result = extract_field_descriptions(description)
    assert "field1" in result
    assert "field with spaces" not in result  # Ignored due to spaces
    assert "field2" in result
    assert "" not in result  # Empty field name ignored
    assert "field3" not in result  # No description


def test_format_schema_with_field_descriptions() -> None:
    """Test format_schema using field descriptions from parent."""
    schemas = {}

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "description": "Property description"},
        },
        "required": ["name"],
    }

    parent_description = """
    User model.

    Attributes:
        name: The user's full name
        age: Override this description
    """

    result = format_schema(schema, schemas, parent_description)

    # Should use attribute description for name
    assert "The user's full name" in result
    # Should prefer attribute description over property description
    assert "Override this description" in result
    assert "Property description" not in result


def test_generate_endpoint_doc_with_request_body() -> None:
    """Test generate_endpoint_doc with request body."""
    schemas = {}

    operation = {
        "summary": "Create workflow",
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                },
            },
        },
        "responses": {"201": {"description": "Workflow created"}},
    }

    result = generate_endpoint_doc("/workflows", "post", operation, schemas)

    assert "### Request Body" in result
    assert "::: code-group" in result
    assert "```json [Example]" in result
    assert "**Content Type:** `application/json`" in result
    assert "| `name` | `string` |" in result


def test_main_execution() -> None:
    """Test main execution when script is run directly."""
    # Import would trigger main execution when __name__ == "__main__"
    # Since we can't easily test this, we'll just verify the function exists
    assert hasattr(generate_api_reference_docs_module, "generate_api_reference_docs")
    assert callable(generate_api_reference_docs_module.generate_api_reference_docs)
