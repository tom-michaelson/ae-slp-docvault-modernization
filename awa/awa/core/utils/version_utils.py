"""Utilities for reading version information from project configuration."""

import tomllib
from pathlib import Path
from typing import Any

from awa.core.logger.logger import LoggerComponent, get_logger

logger = get_logger(LoggerComponent.API)


def _raise_key_error(msg: str) -> None:
    """Raise KeyError with logging.

    Args:
        msg: Error message to log and raise.

    Raises:
        KeyError: Always raises with the provided message.

    """
    logger.error(msg)
    raise KeyError(msg)


def get_project_version() -> str:
    """Read the project version from pyproject.toml.

    Returns:
        The version string from pyproject.toml.

    Raises:
        FileNotFoundError: If pyproject.toml cannot be found.
        KeyError: If version is not found in pyproject.toml.
        Exception: If there's an error parsing the TOML file.

    """
    # Find pyproject.toml starting from this file's directory and walking up
    current_path = Path(__file__).resolve()
    project_root = None

    # Walk up the directory tree to find pyproject.toml
    for parent in current_path.parents:
        pyproject_path = parent / "pyproject.toml"
        if pyproject_path.exists():
            project_root = parent
            break

    if project_root is None:
        msg = "Could not find pyproject.toml in any parent directory"
        logger.error(msg)
        raise FileNotFoundError(msg)

    pyproject_path = project_root / "pyproject.toml"

    try:
        with pyproject_path.open("rb") as f:
            pyproject_data: dict[str, Any] = tomllib.load(f)

        if "project" not in pyproject_data:
            _raise_key_error("No [project] section found in pyproject.toml")

        project_section = pyproject_data["project"]
        if "version" not in project_section:
            _raise_key_error("No version found in [project] section of pyproject.toml")

        version = project_section["version"]
        logger.debug(f"Successfully read version '{version}' from {pyproject_path}")
        return version

    except Exception:
        logger.exception(f"Error reading version from {pyproject_path}")
        raise
