#!/usr/bin/env python3
"""Manual script to generate SDK facades with namespace modules."""

import sys
from pathlib import Path

# Add the AWA source to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from awa.workflows.generate_sdk.activities.generate_facade_activity import FacadeGenerator


def main() -> None:
    """Generate SDK facades manually."""
    sdk_path = Path(__file__).parent.parent / "sdk_dist" / "python"
    sdk_root = sdk_path / "awa" / "client"

    if not sdk_root.exists():
        print(f"SDK root directory not found: {sdk_root}")
        sys.exit(1)

    print(f"Generating facades for SDK at: {sdk_root}")

    # Create and run the facade generator
    generator = FacadeGenerator(sdk_root)
    generator.discover()

    # Log discovery summary
    print("Discovered components:")
    for category, items in generator.discoveries.items():
        if items:
            print(f"  {category}: {len(items)} items")

    # Generate the facade files
    generator.generate(sdk_root)

    print("Facade generation completed successfully")
    print(f"Generated namespace modules in: {sdk_root}")


if __name__ == "__main__":
    main()
