import logging
import shutil
from pathlib import Path

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


def _print_header() -> None:
    """Print the script header."""
    logger.info(Colors.bold("=" * 60))
    logger.info(Colors.bold("AWA Configuration Setup"))
    logger.info(Colors.bold("=" * 60))


def _print_summary(actions: list[tuple[str, str]]) -> None:
    """Print a summary of the actions taken."""
    logger.info(Colors.bold("=" * 60))
    logger.info(Colors.bold("SUMMARY"))
    logger.info(Colors.bold("=" * 60))

    for message, status in actions:
        if status == "created":
            logger.info(Colors.green(f" + {message}"))
        elif status == "existed":
            logger.info(f" - {message}")

    logger.info(Colors.green("\nConfiguration setup complete!"))


def setup_config_files() -> None:
    """Check for essential configuration files like 'config.yaml' and '.env'.

    If they don't exist, it creates them by copying their respective '.example'
    files. This ensures the application has the necessary configuration to run.
    """
    _print_header()
    actions = []

    # Get the directory of the script to find the project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[0]
    logger.info(f"Project root: {project_root}")

    config_mapping = {
        "config.example.yaml": "config.yaml",
        ".env.example": ".env",
        "goose.config.example.yaml": "goose.config.yaml",
        ".mcp.example.json": ".mcp.json",
        "litellm_config.example.yaml": "litellm_config.yaml",
    }

    for example_file, target_file in config_mapping.items():
        example_path = project_root / example_file
        target_path = project_root / target_file

        if not target_path.exists():
            if example_path.exists():
                try:
                    shutil.copy(example_path, target_path)
                    actions.append(
                        (
                            f"Created '{target_file}' from '{example_file}'.",
                            "created",
                        ),
                    )
                except OSError:
                    logger.exception(
                        Colors.red(f"Error copying '{example_file}' to '{target_file}'"),
                    )
            # We can create an empty .env file if the example doesn't exist
            elif target_file == ".env":
                target_path.touch()
                actions.append(
                    (
                        f"Created an empty '{target_file}' as '{example_file}' was not found.",
                        "created",
                    ),
                )
            else:
                logger.warning(
                    Colors.yellow(
                        f"'{example_file}' not found. Skipping creation of '{target_file}'.",
                    ),
                )
        else:
            actions.append((f"'{target_file}' already exists.", "existed"))

    _print_summary(actions)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    setup_config_files()
