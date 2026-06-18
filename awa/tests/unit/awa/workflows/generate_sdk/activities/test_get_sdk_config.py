"""Test cases for get_sdk_config activity."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from temporalio.testing import ActivityEnvironment

from awa.workflows.generate_sdk.activities.get_sdk_config import get_sdk_config_activity
from awa.workflows.generate_sdk.models.sdk_config import SdkConfig


class TestGetSdkConfigActivity:
    """Test cases for get_sdk_config_activity."""

    @pytest.mark.asyncio
    async def test_get_sdk_config_file_not_found(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test handling of missing config file."""
        # Arrange
        nonexistent_file = tmp_path / "nonexistent.yaml"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="SDK config file not found"):
            await activity_env.run(get_sdk_config_activity, str(nonexistent_file))

    @pytest.mark.asyncio
    async def test_get_sdk_config_invalid_yaml(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test handling of malformed YAML file."""
        # Arrange
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("languages:\n  invalid: [\n")  # Invalid YAML

        # Act & Assert
        with pytest.raises(yaml.YAMLError, match="Error parsing YAML file"):
            await activity_env.run(get_sdk_config_activity, str(config_file))

    @pytest.mark.asyncio
    async def test_get_sdk_config_invalid_schema(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test handling of config file with invalid schema."""
        # Arrange
        config_file = tmp_path / "invalid_schema.yaml"
        invalid_config = {
            "languages": ["invalid_structure"],  # Invalid structure
        }
        config_file.write_text(yaml.dump(invalid_config))

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid SDK configuration schema"):
            await activity_env.run(get_sdk_config_activity, str(config_file))

    @pytest.mark.asyncio
    async def test_get_sdk_config_with_default_path(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        """Test loading SDK config with default path."""
        # Arrange - create mock config data
        config_data = {
            "languages": [
                {
                    "name": "csharp",
                    "enabled": True,
                    "ext": ".cs",
                    "model_path": "Models",
                    "model_file_name": "Models",
                    "constants_file_name": "Constants",
                    "constants_path": "Constants",
                },
            ],
            "output_path": "/default/output",
        }

        # Mock FileSystemUtils.read_async to return our test config
        with (
            patch("awa.workflows.generate_sdk.activities.get_sdk_config.Path.exists", return_value=True),
            patch("awa.workflows.generate_sdk.activities.get_sdk_config.FileSystemUtils.read_async") as mock_read,
        ):
            mock_read.return_value = yaml.dump(config_data)

            # Act - call without config_path to use default
            result = await activity_env.run(get_sdk_config_activity, None)

            # Assert
            assert isinstance(result, SdkConfig)
            assert len(result.languages) == 1
            assert result.languages[0].name == "csharp"
