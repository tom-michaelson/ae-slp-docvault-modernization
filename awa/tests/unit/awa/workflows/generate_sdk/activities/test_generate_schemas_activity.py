"""Tests for generate_schemas_activity."""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from awa.sdk.models.exceptions.invalid_input_error import InvalidInputApplicationError
from awa.workflows.generate_sdk.activities.generate_schemas_activity import generate_schemas_activity
from awa.workflows.generate_sdk.models.generate_sdk_schemas_input import GenerateSdkSchemasInput


@pytest.mark.asyncio
async def test_generate_schemas_activity_success() -> None:
    """Test successful schema generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        input_data = GenerateSdkSchemasInput(models_path="awa/sdk/models", output_path=temp_dir)

        # Create a mock model class
        class MockModel:
            @classmethod
            def model_json_schema(cls, mode: None = None) -> dict[str, Any]:  # noqa: ARG003
                return {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "value": {"type": "integer"},
                    },
                    "$defs": {"SomeDefinition": {"type": "string"}},
                }

        # Mock the entire activity function logic, patching the internal functions
        with (
            patch("awa.workflows.generate_sdk.activities.generate_schemas_activity._discover_models") as mock_discover,
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_discover.return_value = {"MockModel": MockModel}

            # Execute the activity
            result = await generate_schemas_activity(input_data)

            # Verify the result contains the expected schema file
            assert len(result) == 1
            assert result[0].endswith("MockModel.json")

            # Verify the schema file was created and contains expected content
            schema_file = Path(temp_dir) / "MockModel.json"
            assert schema_file.exists()

            with schema_file.open() as f:
                schema_content = json.load(f)

            # Verify the schema content
            assert schema_content["type"] == "object"
            assert "properties" in schema_content
            # $defs should be removed during processing
            assert "$defs" not in schema_content


@pytest.mark.asyncio
async def test_generate_schemas_activity_no_models_found() -> None:
    """Test when no models are found."""
    with tempfile.TemporaryDirectory() as temp_dir:
        input_data = GenerateSdkSchemasInput(models_path="awa/sdk/models", output_path=temp_dir)

        # Mock to return no models
        with (
            patch("awa.workflows.generate_sdk.activities.generate_schemas_activity._discover_models") as mock_discover,
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_discover.return_value = {}

            # Execute the activity
            result = await generate_schemas_activity(input_data)

            # Verify empty result
            assert result == []


@pytest.mark.asyncio
async def test_generate_schemas_activity_models_dir_not_found() -> None:
    """Test when models directory doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        input_data = GenerateSdkSchemasInput(models_path="awa/sdk/models", output_path=temp_dir)

        # Mock the models directory to not exist
        with (
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(InvalidInputApplicationError, match="Models directory not found"),
        ):
            await generate_schemas_activity(input_data)


@pytest.mark.asyncio
async def test_generate_schemas_activity_with_defs_removal() -> None:
    """Test schema generation with $defs removal."""
    with tempfile.TemporaryDirectory() as temp_dir:
        input_data = GenerateSdkSchemasInput(models_path="awa/sdk/models", output_path=temp_dir)

        # Create a mock model class with $defs
        class MockModelWithDefs:
            @classmethod
            def model_json_schema(cls, mode: None = None) -> dict[str, Any]:  # noqa: ARG003
                return {
                    "type": "object",
                    "properties": {
                        "reference": {"$ref": "#/$defs/SomeReference"},
                    },
                    "$defs": {
                        "SomeReference": {"type": "string", "description": "A reference type"},
                    },
                }

        with (
            patch("awa.workflows.generate_sdk.activities.generate_schemas_activity._discover_models") as mock_discover,
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_discover.return_value = {"MockModelWithDefs": MockModelWithDefs}

            # Execute the activity
            await generate_schemas_activity(input_data)

            # Verify the schema file was created
            schema_file = Path(temp_dir) / "MockModelWithDefs.json"
            assert schema_file.exists()

            with schema_file.open() as f:
                schema_content = json.load(f)

            # Verify $defs removal and reference conversion
            assert "$defs" not in schema_content
            # The internal reference should be converted to external
            assert schema_content["properties"]["reference"]["$ref"] == "./SomeReference.json"
