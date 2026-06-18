"""Main CLI entry point for AWA package."""

import os
import platform

from dotenv import load_dotenv

from awa.core import cli
from awa.core.logger.logger import init_logging
from awa.core.utils.cli_utils import is_packaged_mode
from awa.core.utils.command_utils import CommandUtils


def setup_development_environment() -> None:
    """Set up development-specific environment."""
    os.environ["PYTHONPYCACHEPREFIX"] = "./.cache/pycache"
    # Set Windows-specific environment variables for better Unicode support
    if platform.system() == "Windows":
        # Force UTF-8 encoding for Python I/O
        os.environ["PYTHONIOENCODING"] = "utf-8"
        # Set console code page to UTF-8
        os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"

    load_dotenv(override=True)


def setup_packaged_environment() -> None:
    """Set up packaged environment with global config."""
    # Global config will be handled by the updated EnvConfig class


def main() -> None:
    """Serve as main CLI entry point that works in both dev and packaged modes."""
    if is_packaged_mode():
        setup_packaged_environment()
    else:
        setup_development_environment()

    CommandUtils.set_event_loop_policy()
    init_logging()
    cli.app()


if __name__ == "__main__":
    main()
