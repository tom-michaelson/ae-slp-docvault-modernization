from enum import StrEnum


class UIMode(StrEnum):
    """UI mode for the CLI: none, dev, or prod."""

    NONE = "none"
    DEV = "dev"
    PROD = "prod"
