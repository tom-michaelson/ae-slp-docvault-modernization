from typing import Any

from jinja2 import BaseLoader, Environment, TemplateError
from temporalio import activity

from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.config_loader import ConfigLoader
from awa.sdk import constants as sdk_constants


@activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
async def resolve_template_activity(
    template_str: str,
    variables: dict[str, Any] | None = None,
) -> str:
    """Resolve a Jinja2 template string with application context.

    This activity renders a given Jinja2 template string. It provides the application
    configuration under the `awa.config` object in the template context. It also
    adds a custom `env` filter to resolve environment variables, e.g., `{{ 'MY_VAR' | env }}`.

    Args:
        template_str: The Jinja2 template string to resolve.
        variables: A dictionary of variables to pass to the template.

    Returns:
        The resolved string.

    """
    app_config = ConfigLoader.get_config()
    env_config = EnvConfig.get_env_config()
    env = Environment(loader=BaseLoader(), autoescape=True)

    if not variables:
        variables = {}

    def env_override(key: str) -> str:
        try:
            return env_config.__getattribute__(key)
        except AttributeError:
            raise TemplateError(f"env variable not found: {key}") from AttributeError

    env.filters["env"] = env_override

    if "awa" in variables:
        raise TemplateError("The 'awa' key is reserved and cannot be used in variables")

    variables["awa"] = {
        "config": app_config,
    }

    return env.from_string(template_str).render(**variables)
