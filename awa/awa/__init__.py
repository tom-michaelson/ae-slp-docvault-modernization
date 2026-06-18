"""AWA Package - Main entry point.

This package acts as a namespace package that allows both the core AWA code
and the SDK distribution client to coexist.
"""

# Extend the __path__ to include the SDK distribution
from pathlib import Path

_sdk_dist_path = Path(__file__).parent.parent / "sdk_dist" / "python" / "awa"
if _sdk_dist_path.exists():
    __path__.append(str(_sdk_dist_path))  # type: ignore[name-defined]
