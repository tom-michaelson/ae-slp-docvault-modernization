"""AWA Client SDK - Clean namespace-based API."""

# Import namespace modules
from . import (
    awa_activity,
    awa_workflow,
    awa_general,
    awa_constants,
    models,
)

# Define what's exported
__all__ = [
    "awa_activity",
    "awa_workflow",
    "awa_general",
    "awa_constants",
    "models",
]
