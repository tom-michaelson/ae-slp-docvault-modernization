"""Test cases for recipes configuration flag."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from awa.core.models.config.app_config import AppConfig
from awa.core.utils.config_loader import ConfigLoader


class TestRecipesConfigLoading:
    """Test cases for loading recipes configuration from YAML files."""

    def setup_method(self) -> None:
        """Reset ConfigLoader state before each test."""
        ConfigLoader._config = None

    def teardown_method(self) -> None:
        """Clean up ConfigLoader state after each test."""
        ConfigLoader._config = None

    def test_config_with_recipes_true(self) -> None:
        """Test config loads correctly with recipes: true."""
        # Arrange
        config_path = Path(__file__).parent.parent.parent / "fixtures" / "config-with-recipes.yaml"

        # Act
        ConfigLoader.load_config(config_path)
        config = ConfigLoader.get_config()

        # Assert
        assert config is not None
        assert config.recipes is True
        assert config.llm is not None
        assert config.llm.default_model == "test-model"

    def test_config_with_recipes_false(self) -> None:
        """Test config loads correctly with recipes: false."""
        # Arrange
        config_path = Path(__file__).parent.parent.parent / "fixtures" / "config-without-recipes.yaml"

        # Act
        ConfigLoader.load_config(config_path)
        config = ConfigLoader.get_config()

        # Assert
        assert config is not None
        assert config.recipes is False
        assert config.llm is not None
        assert config.llm.default_model == "test-model"

    def test_config_without_recipes_field(self) -> None:
        """Test config defaults to recipes: false when field omitted."""
        # Arrange
        config_path = Path(__file__).parent.parent.parent / "fixtures" / "config-recipes-omitted.yaml"

        # Act
        ConfigLoader.load_config(config_path)
        config = ConfigLoader.get_config()

        # Assert
        assert config is not None
        assert config.recipes is True  # Should default to True
        assert config.llm is not None
        assert config.llm.default_model == "test-model"

    def test_config_with_invalid_recipes_value(self) -> None:
        """Test config validation fails with invalid recipes value."""
        # Arrange
        invalid_config_data = {
            "llm": {
                "default_model": "test-model",
                "models": [{"name": "test-model", "provider": "openai", "model": "gpt-4"}],
            },
            "recipes": "not-a-boolean",  # Invalid: should be boolean
        }

        # Act & Assert
        with pytest.raises((ValidationError, ValueError)):
            AppConfig(**invalid_config_data)


class TestRecipesPydanticModel:
    """Test cases for recipes field in AppConfig Pydantic model."""

    def test_pydantic_model_defaults(self) -> None:
        """Test AppConfig Pydantic model has correct defaults."""
        # Arrange
        minimal_config_data = {
            "llm": {
                "default_model": "test-model",
                "models": [{"name": "test-model", "provider": "openai", "model": "gpt-4"}],
            },
        }

        # Act
        config = AppConfig(**minimal_config_data)

        # Assert
        assert config.recipes is True  # Default value
        assert config.llm is not None
        assert config.llm.default_model == "test-model"

    def test_pydantic_model_with_recipes_true(self) -> None:
        """Test AppConfig Pydantic model accepts recipes: true."""
        # Arrange
        config_data = {
            "llm": {
                "default_model": "test-model",
                "models": [{"name": "test-model", "provider": "openai", "model": "gpt-4"}],
            },
            "recipes": True,
        }

        # Act
        config = AppConfig(**config_data)

        # Assert
        assert config.recipes is True

    def test_pydantic_model_with_recipes_false(self) -> None:
        """Test AppConfig Pydantic model accepts recipes: false."""
        # Arrange
        config_data = {
            "llm": {
                "default_model": "test-model",
                "models": [{"name": "test-model", "provider": "openai", "model": "gpt-4"}],
            },
            "recipes": False,
        }

        # Act
        config = AppConfig(**config_data)

        # Assert
        assert config.recipes is False

    def test_pydantic_model_type_validation(self) -> None:
        """Test AppConfig validates recipes field type."""
        # Arrange
        invalid_config_data = {
            "llm": {
                "default_model": "test-model",
                "models": [{"name": "test-model", "provider": "openai", "model": "gpt-4"}],
            },
            "recipes": 123,  # Invalid: should be boolean
        }

        # Act & Assert
        with pytest.raises((ValidationError, ValueError)):
            AppConfig(**invalid_config_data)

    def test_pydantic_model_field_description(self) -> None:
        """Test recipes field has proper description in model."""
        # Act
        field_info = AppConfig.model_fields["recipes"]

        # Assert
        assert field_info.default is True
        assert "Enable recipe workflows and activities registration" in field_info.description
        assert "recipe workflows will be discovered and registered" in field_info.description


class TestRecipesConfigIntegration:
    """Integration tests for recipes configuration."""

    def setup_method(self) -> None:
        """Reset ConfigLoader state before each test."""
        ConfigLoader._config = None

    def teardown_method(self) -> None:
        """Clean up ConfigLoader state after each test."""
        ConfigLoader._config = None

    def test_recipes_field_is_optional(self) -> None:
        """Test that recipes field is optional and not required."""
        # Arrange
        minimal_config_data = {
            "llm": {
                "default_model": "test-model",
                "models": [{"name": "test-model", "provider": "openai", "model": "gpt-4"}],
            },
        }

        # Act - should not raise any exceptions
        config = AppConfig(**minimal_config_data)

        # Assert
        assert config.recipes is True  # Should use default

    def test_recipes_works_with_other_optional_fields(self) -> None:
        """Test recipes field works alongside other optional fields."""
        # Arrange
        config_data = {
            "llm": {
                "default_model": "test-model",
                "models": [{"name": "test-model", "provider": "openai", "model": "gpt-4"}],
            },
            "recipes": True,
            "jira": {"url": "https://example.atlassian.net", "api_user": "test@example.com"},
        }

        # Act
        config = AppConfig(**config_data)

        # Assert
        assert config.recipes is True
        assert config.jira is not None
        assert config.jira.url == "https://example.atlassian.net"

    def test_recipes_serialization(self) -> None:
        """Test that recipes field is properly serialized."""
        # Arrange
        config_data = {
            "llm": {
                "default_model": "test-model",
                "models": [{"name": "test-model", "provider": "openai", "model": "gpt-4"}],
            },
            "recipes": True,
        }

        # Act
        config = AppConfig(**config_data)
        serialized = config.model_dump()

        # Assert
        assert "recipes" in serialized
        assert serialized["recipes"] is True
