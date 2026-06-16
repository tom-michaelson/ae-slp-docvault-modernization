"""CLI utility functions for AWA."""

from pathlib import Path


def is_packaged_mode() -> bool:
    """Detect if running as installed package vs development mode.

    Returns:
        True if running from site-packages (packaged mode), False otherwise.

    """
    return "site-packages" in str(Path(__file__).resolve())
