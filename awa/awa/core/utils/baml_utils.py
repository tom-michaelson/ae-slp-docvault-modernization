import shutil
from pathlib import Path

from loguru._logger import Logger

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.command_utils import CommandUtils

logger = get_logger(LoggerComponent.SCRIPT)


def generate_baml_client() -> None:
    """Generate BAML client for the main AWA project."""
    root_dir = Path(__file__).parents[3]
    logger.info(f"Root dir: {root_dir}")
    global_awa_dir = (root_dir / "awa").resolve()
    logger.info(f"Global awa dir: {global_awa_dir}")

    # Copy all project-level BAML files to the global BAML directory
    logger.info("Copying all BAML files to the global BAML directory...")

    # Find all "baml_src" directories under "awa" (except for /awa/baml_src)
    # and copy all files into /awa/baml_src in a subdirectory structure mimicking the original structure
    _copy_baml_files_to_global_directory(global_awa_dir)

    # Regenerate BAML client
    generate_baml_client_for_dir(global_awa_dir / "baml_src")


def generate_baml_client_for_dir(baml_src_dir: str | Path, activity_logger: Logger | None = None) -> None:
    """Generate BAML client for a specific directory.

    Args:
        baml_src_dir: Path to the baml_src directory
        activity_logger: Optional logger to use (typically activity.logger when called from an activity)

    """
    working_dir = Path(baml_src_dir).parent
    # Use provided logger or fall back to default logger
    current_logger = activity_logger if activity_logger is not None else logger
    current_logger.info(f"Regenerating BAML client for {working_dir!s} ...")
    try:
        max_tries = 5
        attempt = 0
        baml_client_dir = Path(baml_src_dir).parent / "baml_client"
        init_file = baml_client_dir / "__init__.py"

        while attempt < max_tries:
            attempt += 1
            logger.info(f"Generating BAML client (attempt {attempt}/{max_tries})...")

            generate_status, generate_result = CommandUtils.run_command(
                command="uv run baml-cli generate",
                working_dir=str(working_dir),
            )
            if not generate_status:
                logger.warning(f"Failed to generate BAML on attempt {attempt}: {generate_result}")
                if attempt == max_tries:
                    raise RuntimeError(f"Failed to generate BAML after {max_tries} attempts: {generate_result}")  # noqa: TRY301
                continue

            if init_file.exists():
                logger.info("BAML client regenerated successfully.")
                break

            logger.warning(f"__init__.py not found in {baml_client_dir} after generation attempt {attempt}")
            if attempt == max_tries:
                raise RuntimeError(  # noqa: TRY301
                    f"Failed to generate valid BAML client after {max_tries} attempts. "
                    f"__init__.py not found in {baml_client_dir}",
                )
    except Exception:
        current_logger.exception(f"Failed to generate BAML client for {working_dir!s}")
        raise


def _is_path_under_directory(path: Path, directory: Path) -> bool:
    """Check if a path is under a specific directory."""
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    else:
        return True


def _copy_baml_files_to_global_directory(global_awa_dir: Path) -> None:
    """Copy all baml_src files from all subdirectories.

    Find all 'baml_src' directories under 'awa' (except for /awa/baml_src)
    and copy all files into /awa/baml_src maintaining the original directory structure.
    """
    global_baml_dir = global_awa_dir / "baml_src"

    # Create the global baml_src directory if it doesn't exist
    global_baml_dir.mkdir(exist_ok=True)

    # Find all baml_src directories except the global one and those in baml_dynamic
    awa_dir = global_awa_dir
    baml_dynamic_dir = awa_dir / "baml_dynamic"
    baml_src_dirs: list[Path] = [
        p
        for p in awa_dir.rglob("baml_src")
        if p.resolve() != global_baml_dir.resolve() and not _is_path_under_directory(p, baml_dynamic_dir)
    ]

    if not baml_src_dirs:
        return

    for baml_src_path in baml_src_dirs:
        # Calculate the relative path from src to this baml_src directory
        # This will be used to create the same structure in the global baml_src
        try:
            relative_path = baml_src_path.parent.relative_to(awa_dir)
        except ValueError:
            # If we can't get relative path, skip this directory
            logger.warning(f"Could not determine relative path for {baml_src_path}")
            continue

        # Create the destination directory structure
        dest_dir: Path = global_baml_dir / "_copied" / relative_path
        dest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Copying BAML files from {baml_src_path} to {dest_dir}")

        # Copy all files from the source baml_src to the destination
        for file_path in baml_src_path.rglob("*"):
            if file_path.is_file():
                # Get the relative path of the file within its baml_src directory
                file_relative_path = file_path.relative_to(baml_src_path)
                dest_file_path: Path = dest_dir / file_relative_path

                # Create parent directories if needed
                dest_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy the file
                shutil.copy2(file_path, dest_file_path)
