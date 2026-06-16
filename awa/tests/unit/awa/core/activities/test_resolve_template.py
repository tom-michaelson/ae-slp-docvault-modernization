from unittest.mock import Mock, patch

import pytest
from jinja2 import TemplateError
from temporalio.testing import ActivityEnvironment

from awa.core.activities.resolve_template import resolve_template_activity
from awa.core.utils.config_loader import AppConfig, ConfigLoader


class TestResolveTemplateActivity:
    @pytest.mark.asyncio
    @patch("awa.core.activities.resolve_template.EnvConfig.get_env_config")
    async def test_resolve_template_activity_returns_correct_response(
        self,
        mock_get_env_config: Mock,
        activity_env: ActivityEnvironment,
    ) -> None:
        # Arrange
        mock_get_env_config().test = "env value"
        mock_config = Mock(spec=AppConfig)
        mock_config.llm = "config value"
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.get_config.return_value(mock_config)

        template_str = """
        Env Variable: {{ "test" | env }}
        Config Variable: {{ awa.config.llm }}
        """

        # Act
        with (
            patch("awa.core.activities.resolve_template.ConfigLoader.get_config", return_value=mock_config),
        ):
            result = await activity_env.run(resolve_template_activity, template_str)

        # Assert
        assert "Env Variable: env value" in result
        assert "Config Variable: config value" in result

    @pytest.mark.asyncio
    @patch("awa.core.activities.resolve_template.EnvConfig.get_env_config")
    async def test_resolve_template_activity_returns_dict_config_value(
        self,
        mock_get_env_config: Mock,
        activity_env: ActivityEnvironment,
    ) -> None:
        # Arrange
        mock_get_env_config().test = "env value"
        mock_config = Mock(spec=AppConfig)
        mock_config = {
            "llm": {
                "default_model": "gpt-4.1",
            },
        }
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.get_config.return_value(mock_config)

        template_str = """
        Config Variable: {{ awa.config.llm }}
        """

        # Act
        with (
            patch("awa.core.activities.resolve_template.ConfigLoader.get_config", return_value=mock_config),
        ):
            result = await activity_env.run(resolve_template_activity, template_str)

        # Assert
        assert "Config Variable: {&#39;default_model&#39;: &#39;gpt-4.1&#39;}" in result

    @pytest.mark.asyncio
    @patch("awa.core.activities.resolve_template.EnvConfig.get_env_config")
    async def test_resolve_template_activity_returns_nested_config_value(
        self,
        mock_get_env_config: Mock,
        activity_env: ActivityEnvironment,
    ) -> None:
        # Arrange
        mock_get_env_config().test = "env value"
        mock_config = Mock(spec=AppConfig)
        mock_config = {
            "llm": {
                "default_model": "gpt-4.1",
            },
        }
        mock_loader = Mock(spec=ConfigLoader)
        mock_loader.get_config.return_value(mock_config)

        template_str = """
        Config Variable: {{ awa.config.llm.default_model }}
        """

        # Act
        with (
            patch("awa.core.activities.resolve_template.ConfigLoader.get_config", return_value=mock_config),
        ):
            result = await activity_env.run(resolve_template_activity, template_str)

        # Assert
        assert "Config Variable: gpt-4.1" in result

    @pytest.mark.asyncio
    @patch("awa.core.activities.resolve_template.EnvConfig.get_env_config")
    @patch("awa.core.activities.resolve_template.ConfigLoader.get_config")
    async def test_resolve_template_activity_throws_missing_env_var_error(
        self,
        mock_get_config: Mock,
        mock_get_env_config: Mock,
        activity_env: ActivityEnvironment,
    ) -> None:
        # Arrange
        mock_get_config().test = "config value"
        mock_get_env_config().test = "env value"

        template_str = """
        Env Variable: {{ "MISSING" | env }}
        """

        # Act
        with pytest.raises(TemplateError) as error:
            await activity_env.run(resolve_template_activity, template_str)

        # Assert
        assert str(error.value) == "env variable not found: MISSING"
