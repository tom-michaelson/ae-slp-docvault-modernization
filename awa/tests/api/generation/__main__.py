"""CLI entry point for API test generation.

This allows running the generation module directly:
    python -m tests.api.generation
"""

from __future__ import annotations

import sys


def main() -> None:
    """Provide the main entry point for the generation module."""
    if len(sys.argv) > 1 and sys.argv[1] == "data":
        # Run test data generation only
        from tests.api.generation.generate_test_data import main as data_main

        data_main()
    else:
        # Run full API test generation (default)
        from tests.api.generation.generate_api_tests import main as api_main

        api_main()


if __name__ == "__main__":
    main()
