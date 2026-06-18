"""Clear worker registry files from the global AWA configuration directory.

This script removes all worker registration JSON files from the registry/workers
directory in the global AWA config directory. It is typically run during the
install process to ensure a clean state.
"""

import logging

from awa.core.utils.config_paths import ConfigPaths

logger = logging.getLogger(__name__)


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


def clear_registry() -> None:
    """Clear all worker registry JSON files from the global config directory."""
    logger.info(Colors.bold("=" * 60))
    logger.info(Colors.bold("Worker Registry Cleanup"))
    logger.info(Colors.bold("=" * 60))

    # Get the registry directory path
    global_dir = ConfigPaths.get_global_config_dir()
    registry_dir = global_dir / "registry" / "workers"

    logger.info(f"Registry directory: {registry_dir}")

    # Check if directory exists
    if not registry_dir.exists():
        logger.info(Colors.yellow("Registry directory does not exist. Nothing to clean."))
        return

    # Find all JSON files in the registry directory
    json_files = list(registry_dir.glob("*.json"))

    if not json_files:
        logger.info(Colors.yellow("No registry files found. Registry is already clean."))
        return

    # Delete each JSON file
    deleted_count = 0
    errors = []

    for json_file in json_files:
        try:
            json_file.unlink()
            logger.info(Colors.green(f"Deleted: {json_file.name}"))
            deleted_count += 1
        except OSError as e:
            error_msg = f"Failed to delete {json_file.name}: {e}"
            errors.append(error_msg)
            logger.exception(Colors.red(error_msg))

    # Print summary
    logger.info(Colors.bold("=" * 60))
    logger.info(Colors.bold("SUMMARY"))
    logger.info(Colors.bold("=" * 60))
    logger.info(Colors.green(f"Successfully deleted {deleted_count} registry file(s)"))

    if errors:
        logger.warning(Colors.yellow(f"Encountered {len(errors)} error(s) during cleanup"))
    else:
        logger.info(Colors.green("Registry cleanup complete!"))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    clear_registry()
