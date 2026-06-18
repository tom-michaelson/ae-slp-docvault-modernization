from awa.core.models.config.app_config import AppConfig
from awa.core.models.config.model_config import ModelConfig
from awa.sdk.models.exceptions.fatal_application_error import FatalApplicationError


class ConfigUtils:
    @staticmethod
    def get_model_config(config: AppConfig, model_name: str | None = None) -> ModelConfig:
        if not model_name:
            model_name = config.llm.default_model

        if not model_name:
            raise FatalApplicationError("No model name provided, and default model is not set")

        model_config: ModelConfig | None = next(
            (model for model in config.llm.models if model.name == model_name),
            None,
        )

        if not model_config:
            raise FatalApplicationError(f"Model config not found for model name: {model_name}")

        if model_config.use_cache is None:
            model_config.use_cache = config.llm.behavior.use_cache

        return model_config
