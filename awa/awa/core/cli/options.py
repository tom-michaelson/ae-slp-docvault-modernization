from pathlib import Path
from typing import Annotated

import typer

from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.config_loader import ConfigLoader


def options_callback(
    env: Annotated[
        str | None,
        typer.Option("--env", "-e", help="Optional .env path, overwriting any defaults or values from local"),
    ] = None,
    config: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Optional config.yaml path, overwriting any defaults or values from local"),
    ] = None,
) -> None:
    # Setup creation of global cli options
    handle_options(env, config)


def handle_options(env: str | None, config: str | None) -> None:
    # Load cli options to custom override .env and config.yaml
    if env is not None and file_exists(env):
        EnvConfig.update_env_config(env)

    if config is not None and file_exists(config):
        ConfigLoader.load_config(config)


def file_exists(file_path: str) -> bool:
    path = Path(file_path)
    return path.is_file()
