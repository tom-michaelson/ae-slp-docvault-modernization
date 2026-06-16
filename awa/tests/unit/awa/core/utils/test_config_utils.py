"""Test cases for ConfigUtils class."""

import pytest

from awa.core.models.config.app_config import AppConfig
from awa.core.models.config.llm_behavior_config import LlmBehaviorConfig
from awa.core.models.config.llm_config import LLMConfig
from awa.core.models.config.llm_providers_config import LlmProviderEnum, LlmProvidersConfig, OpenAiLlmProvider
from awa.core.models.config.model_config import ModelConfig
from awa.core.utils.config_utils import ConfigUtils
from awa.sdk.models.exceptions.fatal_application_error import FatalApplicationError


@pytest.fixture
def sample_model_config() -> ModelConfig:
    """Provide a sample model config for testing."""
    return ModelConfig(
        name="test_model",
        provider=LlmProviderEnum.OPEN_AI,
        model="gpt-4",
        use_cache=True,
        max_tokens=1000,
    )


@pytest.fixture
def sample_app_config(sample_model_config: ModelConfig) -> AppConfig:
    """Provide a sample app config for testing."""
    llm_behavior = LlmBehaviorConfig(use_cache=False)
    llm_providers = LlmProvidersConfig(openai=OpenAiLlmProvider())
    llm_config = LLMConfig(
        default_model="test_model",
        providers=llm_providers,
        models=[sample_model_config],
        behavior=llm_behavior,
    )
    return AppConfig(llm=llm_config)


class TestConfigUtils:
    """Test cases for ConfigUtils class."""

    def test_get_model_config_with_model_name(self, sample_app_config: AppConfig) -> None:
        """Test getting model config with specified model name."""
        # Act
        result = ConfigUtils.get_model_config(sample_app_config, "test_model")

        # Assert
        assert result.name == "test_model"
        assert result.provider == LlmProviderEnum.OPEN_AI
        assert result.model == "gpt-4"

    def test_get_model_config_without_model_name_uses_default(self, sample_app_config: AppConfig) -> None:
        """Test getting model config without model name uses default."""
        # Act
        result = ConfigUtils.get_model_config(sample_app_config)

        # Assert
        assert result.name == "test_model"
        assert result.provider == LlmProviderEnum.OPEN_AI

    def test_get_model_config_with_none_model_name_uses_default(self, sample_app_config: AppConfig) -> None:
        """Test getting model config with None model name uses default."""
        # Act
        result = ConfigUtils.get_model_config(sample_app_config, None)

        # Assert
        assert result.name == "test_model"

    def test_get_model_config_raises_error_when_no_default_model(self) -> None:
        """Test getting model config raises error when no default model is set."""
        # Arrange
        llm_behavior = LlmBehaviorConfig(use_cache=False)
        llm_providers = LlmProvidersConfig(openai=OpenAiLlmProvider())
        llm_config = LLMConfig(
            default_model="",  # Empty string to simulate no default model
            providers=llm_providers,
            models=[],
            behavior=llm_behavior,
        )
        config = AppConfig(llm=llm_config)

        # Act & Assert
        with pytest.raises(FatalApplicationError, match="No model name provided"):
            ConfigUtils.get_model_config(config)

    def test_get_model_config_raises_error_when_model_not_found(self, sample_app_config: AppConfig) -> None:
        """Test getting model config raises error when model is not found."""
        # Act & Assert
        with pytest.raises(FatalApplicationError, match="Model config not found for model name: nonexistent_model"):
            ConfigUtils.get_model_config(sample_app_config, "nonexistent_model")

    def test_get_model_config_inherits_use_cache_from_behavior_when_none(self) -> None:
        """Test that model config inherits use_cache from behavior when it's None."""
        # Arrange
        model_config = ModelConfig(
            name="test_model",
            provider=LlmProviderEnum.OPEN_AI,
            model="gpt-4",
            use_cache=None,  # This should inherit from behavior
        )
        llm_behavior = LlmBehaviorConfig(use_cache=True)
        llm_providers = LlmProvidersConfig(openai=OpenAiLlmProvider())
        llm_config = LLMConfig(
            default_model="test_model",
            providers=llm_providers,
            models=[model_config],
            behavior=llm_behavior,
        )
        config = AppConfig(llm=llm_config)

        # Act
        result = ConfigUtils.get_model_config(config, "test_model")

        # Assert
        assert result.use_cache is True

    def test_get_model_config_preserves_existing_use_cache(self, sample_app_config: AppConfig) -> None:
        """Test that model config preserves existing use_cache value."""
        # The sample config has use_cache=True for the model
        # Act
        result = ConfigUtils.get_model_config(sample_app_config, "test_model")

        # Assert
        assert result.use_cache is True
