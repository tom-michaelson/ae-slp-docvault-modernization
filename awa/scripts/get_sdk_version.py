#!/usr/bin/env python
"""Get the current SDK version from the version files."""

import sys
from pathlib import Path


def get_current_sdk_version() -> str | None:
    """Get the current SDK version from the latest version file.

    Returns:
        The current SDK version string, or None if no version file exists.

    """
    # Look for version files in sdk_dist/.hash/
    version_dir = Path("sdk_dist/.hash")

    if not version_dir.exists():
        return None

    # Find all version files (*.version)
    version_files = list(version_dir.glob("*.version"))

    if not version_files:
        return None

    # Sort version files by semantic version (not string sorting)
    def version_sort_key(filepath: Path) -> tuple[int, ...]:
        """Convert version string to tuple of ints for proper sorting."""
        version_str = filepath.stem
        try:
            # Split version into parts and convert to integers
            parts = [int(x) for x in version_str.split(".")]
            # Pad with zeros to ensure consistent comparison
            min_parts = 4
            while len(parts) < min_parts:
                parts.append(0)
            return tuple(parts)
        except (ValueError, AttributeError):
            # If parsing fails, return a tuple that sorts to the beginning
            return (0, 0, 0, 0)

    # Sort by semantic version and get the highest
    version_files.sort(key=version_sort_key)
    latest_version_file = version_files[-1]

    # Extract version from filename (e.g., "1.0.1.version" -> "1.0.1")
    version = latest_version_file.stem

    return version


def main() -> None:
    """Execute the main entry point for the script."""
    version = get_current_sdk_version()

    if version:
        print(version)
    else:
        print("No SDK version found. Run 'uv run python -m awa workflows generate-sdk' first.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
