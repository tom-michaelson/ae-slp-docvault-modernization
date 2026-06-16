#!/usr/bin/env python3
"""SDK validation script for pre-commit hooks.

This script validates that all enabled SDKs are current with source changes
in the awa/sdk directory. It's designed to be run as a pre-commit hook to
prevent commits when SDKs are outdated.
"""

import asyncio
import os
import sys
from pathlib import Path

import yaml

from awa.core.logger.logger import init_logging
from awa.core.utils.file_system_utils import FileSystemUtils
from awa.core.utils.sdk_hash_utils import SdkHashUtils


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @staticmethod
    def green(text: str) -> str:
        return f"{Colors.GREEN}{text}{Colors.RESET}"

    @staticmethod
    def red(text: str) -> str:
        return f"{Colors.RED}{text}{Colors.RESET}"

    @staticmethod
    def yellow(text: str) -> str:
        return f"{Colors.YELLOW}{text}{Colors.RESET}"

    @staticmethod
    def blue(text: str) -> str:
        return f"{Colors.BLUE}{text}{Colors.RESET}"

    @staticmethod
    def bold(text: str) -> str:
        return f"{Colors.BOLD}{text}{Colors.RESET}"


async def get_enabled_languages() -> list[str]:
    """Get list of enabled languages from SDK configuration.

    Returns:
        List of enabled language names.

    Raises:
        FileNotFoundError: If SDK config file doesn't exist.
        ValueError: If SDK config is invalid.

    """
    config_path = Path("awa/sdk/sdk.config.yaml")

    if not config_path.exists():
        raise FileNotFoundError(f"SDK configuration not found: {config_path}")

    try:
        config_content = await FileSystemUtils.read_async(str(config_path))
        config = yaml.safe_load(config_content)

        languages = config.get("languages", [])
        enabled_languages = [lang["name"] for lang in languages if lang.get("enabled", False)]

        if not enabled_languages:
            print(Colors.yellow("Warning: No enabled languages found in SDK configuration"))
            return []

        return enabled_languages
    except (yaml.YAMLError, KeyError, TypeError) as e:
        raise ValueError(f"Invalid SDK configuration: {e}") from e


async def validate_sdk_current() -> bool:
    """Validate that all enabled SDKs are current with source changes.

    Returns:
        True if all SDKs are current, False if any are outdated.

    """
    try:
        print(Colors.bold("🔍 Validating SDK currency..."))

        enabled_languages = await get_enabled_languages()

        if not enabled_languages:
            print(Colors.green("✅ No enabled SDKs to validate"))
            return True

        print(f"Checking languages: {', '.join(enabled_languages)}")

        is_current = await SdkHashUtils.validate_all_sdks_current(enabled_languages)

        if is_current:
            print(Colors.green("✅ All SDKs are current"))
            return True
        return False

    except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
        print(Colors.red(f"❌ Error validating SDKs: {e}"))
        return False


async def get_outdated_sdks() -> list[str]:
    """Return list of SDK languages that are outdated.

    Returns:
        List of outdated language names.

    """
    try:
        enabled_languages = await get_enabled_languages()

        if not enabled_languages:
            return []

        return await SdkHashUtils.get_outdated_sdks(enabled_languages)

    except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
        print(Colors.red(f"❌ Error checking SDK status: {e}"))
        return []


def print_usage_help() -> None:
    """Print usage instructions for updating outdated SDKs."""
    print()
    print(Colors.bold('To update outdated SDKs, run the "awa-generate-sdk" workflow:'))
    print(Colors.blue("uv run -m awa.main run -w awa-generate-sdk"))
    print()


async def main() -> None:
    """Execute the SDK validation process."""
    # Initialize logging with minimal output for pre-commit
    # Set log level to ERROR to suppress debug/info/warning messages

    os.environ["AWA_LOG_LEVEL"] = "ERROR"
    init_logging(file_only=True)  # Only log to files, not console

    try:
        is_current = await validate_sdk_current()

        if not is_current:
            outdated = await get_outdated_sdks()

            print(Colors.red("❌ SDK validation failed"))
            if outdated:
                print(Colors.red(f"Outdated SDKs: {', '.join(outdated)}"))

            print_usage_help()
            sys.exit(1)
        else:
            print(Colors.green("✅ SDK validation passed"))
            sys.exit(0)

    except KeyboardInterrupt:
        print(Colors.yellow("\n⚠️  Validation interrupted"))
        sys.exit(1)
    except (OSError, RuntimeError) as e:
        print(Colors.red(f"❌ Unexpected error: {e}"))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
