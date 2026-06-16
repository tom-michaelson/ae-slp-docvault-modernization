"""Platform detection utilities for cross-platform compatibility."""

import sys
from typing import Literal

PlatformType = Literal["windows", "unix"]


class PlatformUtils:
    """Utilities for platform detection and cross-platform compatibility."""

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows."""
        return sys.platform == "win32"

    @staticmethod
    def is_unix() -> bool:
        """Check if running on Unix-like system (Linux, macOS, etc.)."""
        return not PlatformUtils.is_windows()

    @staticmethod
    def get_platform_type() -> PlatformType:
        """Get standardized platform type."""
        return "windows" if PlatformUtils.is_windows() else "unix"

    @staticmethod
    def get_platform_name() -> str:
        """Get detailed platform name for logging/debugging."""
        return sys.platform
