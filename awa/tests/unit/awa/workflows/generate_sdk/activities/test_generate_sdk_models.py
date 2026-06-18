"""Test cases for generate_sdk_models activity."""

from pathlib import Path

import pytest
from temporalio.testing import ActivityEnvironment

from awa.sdk.models.exceptions.invalid_input_error import InvalidInputApplicationError
from awa.workflows.generate_sdk.activities.generate_sdk_models import (
    _discover_schema_files,
    generate_sdk_models_activity,
)
from awa.workflows.generate_sdk.models.generate_sdk_models_input import GenerateSdkModelsInput
from awa.workflows.generate_sdk.models.sdk_config import SdkLanguageConfig


class TestGenerateSdkModelsActivity:
    """Test cases for generate_sdk_models_activity."""

    @pytest.mark.asyncio
    async def test_generate_sdk_models_invalid_schemas_path(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test failure when schemas path doesn't exist."""
        # Arrange
        nonexistent_path = tmp_path / "nonexistent"

        language_config = SdkLanguageConfig(
            name="csharp",
            enabled=True,
            ext=".cs",
            model_path="Models",
            model_file_name="Models",
            constants_file_name="Constants",
            constants_path="Constants",
        )

        workflow_input = GenerateSdkModelsInput(
            json_schemas_path=str(nonexistent_path),
            language_config=language_config,
            output_path=str(tmp_path / "output"),
        )

        # Act & Assert
        with pytest.raises(InvalidInputApplicationError, match="JSON schemas directory not found"):
            await activity_env.run(generate_sdk_models_activity, workflow_input)

    @pytest.mark.asyncio
    async def test_generate_sdk_models_no_schema_files(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test handling of empty schemas directory."""
        # Arrange
        schemas_path = tmp_path / "empty_schemas"
        schemas_path.mkdir()

        language_config = SdkLanguageConfig(
            name="csharp",
            enabled=True,
            ext=".cs",
            model_path="Models",
            model_file_name="Models",
            constants_file_name="Constants",
            constants_path="Constants",
        )

        workflow_input = GenerateSdkModelsInput(
            json_schemas_path=str(schemas_path),
            language_config=language_config,
            output_path=str(tmp_path / "output"),
        )

        # Act
        result = await activity_env.run(generate_sdk_models_activity, workflow_input)

        # Assert
        assert result == []  # No files generated


class TestDiscoverSchemaFiles:
    """Test cases for _discover_schema_files function."""

    def test_discover_schema_files_success(self, tmp_path: Path) -> None:
        """Test discovering schema files in directory."""
        # Arrange
        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        # Create test files
        schema1 = schemas_dir / "User.json"
        schema2 = schemas_dir / "Product.json"
        non_schema = schemas_dir / "readme.txt"

        schema1.write_text('{"type": "object"}')
        schema2.write_text('{"type": "object"}')
        non_schema.write_text("This is not a schema")

        # Act
        result = _discover_schema_files(schemas_dir)

        # Assert
        assert len(result) == 2
        schema_names = [f.name for f in result]
        assert "User.json" in schema_names
        assert "Product.json" in schema_names
        assert "readme.txt" not in schema_names

    def test_discover_schema_files_empty_directory(self, tmp_path: Path) -> None:
        """Test discovering schema files in empty directory."""
        # Arrange
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Act
        result = _discover_schema_files(empty_dir)

        # Assert
        assert result == []
