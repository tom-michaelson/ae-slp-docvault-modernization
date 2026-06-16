import asyncio
from datetime import datetime
from pathlib import Path

from fsspec.implementations.local import LocalFileSystem
from temporalio import activity

from awa.core.utils.baml_utils import generate_baml_client_for_dir
from awa.core.utils.cache_utils import CacheUtils
from awa.core.utils.file_system_utils import FileSystemUtils
from awa.sdk import constants as sdk_constants

# Module-level lock to ensure thread-safe BAML client generation
_baml_client_generation_lock = asyncio.Lock()

# Prefix for timestamped directories
TIMESTAMP_PREFIX = "awa_ts_"
TIMESTAMP_FORMAT = "%Y%m%d%H%M%S%f"
TIMESTAMP_VALIDATION_FORMAT = "%Y%m%d%H%M%S"  # For validating the 17-character timestamp

# Constants for timestamp validation
TIMESTAMP_LENGTH = 17
MILLISECONDS_MAX = 999


def _is_valid_timestamp(timestamp_str: str) -> bool:
    """Validate if a string is a valid timestamp in our expected format.

    Args:
        timestamp_str: The timestamp string to validate.

    Returns:
        True if the timestamp is valid, False otherwise.

    """
    try:
        # The timestamp should be 17 characters (YYYYMMDDHHMMSSMMM)
        if len(timestamp_str) != TIMESTAMP_LENGTH:
            return False

        # Split into date/time part (14 chars) and milliseconds (3 chars)
        datetime_part = timestamp_str[:14]
        milliseconds_part = timestamp_str[14:]

        # Validate the datetime part
        datetime.strptime(datetime_part, TIMESTAMP_VALIDATION_FORMAT)  # noqa: DTZ007

        # Validate that the milliseconds part is numeric
        if not milliseconds_part.isdigit():
            return False

        # Validate that milliseconds are within valid range (0-999)
        return 0 <= int(milliseconds_part) <= MILLISECONDS_MAX
    except ValueError:
        return False


def _find_latest_timestamped_directory(base_dir: Path) -> Path | None:
    """Find the latest timestamped directory in the base directory.

    Args:
        base_dir: The base directory to search for timestamped directories.

    Returns:
        The path to the latest timestamped directory, or None if no timestamped directories exist.

    """
    if not base_dir.exists():
        return None

    timestamped_dirs = []
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith(TIMESTAMP_PREFIX):
            # Extract the timestamp suffix
            timestamp_suffix = item.name[len(TIMESTAMP_PREFIX) :]

            # Validate that the suffix is a valid timestamp
            if _is_valid_timestamp(timestamp_suffix):
                timestamped_dirs.append(item)

    if not timestamped_dirs:
        return None

    # Sort by timestamp string (which will sort chronologically)
    timestamped_dirs.sort(key=lambda d: d.name[len(TIMESTAMP_PREFIX) :])
    return timestamped_dirs[-1]


@activity.defn(name=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT)
async def generate_baml_client_activity(
    baml_function_name: str,
    baml_content: str,
    workflow_task_queue: str,
) -> str:
    """Generate a BAML client for the given function name and content.

    This activity creates a unique BAML client per queue + function combination.
    It writes the BAML content to a file and generates the corresponding client
    if the content is new or different from existing content.

    Args:
        baml_function_name: The name of the BAML function to generate a client for.
        baml_content: The content of the BAML function to generate a client for.
        workflow_task_queue: The task queue of the workflow.

    Returns:
        The path to the BAML source directory.

    """
    async with _baml_client_generation_lock:
        return await _generate_baml_client_impl(baml_function_name, baml_content, workflow_task_queue)


async def _generate_baml_client_impl(baml_function_name: str, baml_content: str, workflow_task_queue: str) -> str:
    """If new, write the baml_content to a file in awa/baml_dynamic and generate a BAML client.

    This function is used to generate a BAML client for a given BAML function name and content.
    It will create a unique BAML client per queue + function.

    Args:
        baml_function_name: The name of the BAML function to generate a client for.
        baml_content: The content of the BAML function to generate a client for.
        workflow_task_queue: The task queue of the workflow.

    Returns:
        The path to the BAML client directory.

    """
    dynamic_filename = f"{baml_function_name}.baml"
    project_root = Path(__file__).parent.parent.parent.parent

    # Find the latest timestamped directory for this function
    function_base_dir = project_root / "awa" / "baml_dynamic" / workflow_task_queue / baml_function_name
    latest_timestamped_dir = _find_latest_timestamped_directory(function_base_dir)

    # Check if the file already exists in the latest timestamped directory and compare content hashes
    fs = LocalFileSystem(auto_mkdir=True)
    file_needs_writing = True
    baml_src_dir = None

    if latest_timestamped_dir:
        latest_baml_src_dir = latest_timestamped_dir / "baml_src"
        latest_dynamic_file_path = latest_baml_src_dir / dynamic_filename

        if latest_dynamic_file_path.exists():
            existing_content = FileSystemUtils.read(fs, str(latest_dynamic_file_path))
            existing_hash = CacheUtils.hash(existing_content)
            new_hash = CacheUtils.hash(baml_content)

            if existing_hash == new_hash:
                file_needs_writing = False
                baml_src_dir = latest_baml_src_dir

    # Only create a new timestamped directory if content is different (or no existing content)
    if file_needs_writing:
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)[:-3]  # noqa: DTZ005
        timestamped_dir_name = f"{TIMESTAMP_PREFIX}{timestamp}"
        baml_src_dir = function_base_dir / timestamped_dir_name / "baml_src"
        baml_src_dir.mkdir(parents=True, exist_ok=True)
        dynamic_file_path = baml_src_dir / dynamic_filename

        FileSystemUtils.write(
            fs,
            str(dynamic_file_path),
            baml_content,
        )

    # Generate client if we wrote a new file or if client doesn't exist
    baml_client_dir = baml_src_dir.parent / "baml_client"
    baml_client_exists = baml_client_dir.exists()

    if not baml_client_exists or file_needs_writing:
        # Copy shared BAML files to the dynamic BAML directory
        await FileSystemUtils.copy_directory_async(
            project_root / "awa" / "core" / "baml_src" / "shared",
            baml_src_dir / "shared",
        )

        generate_baml_client_for_dir(baml_src_dir, activity.logger)

    return str(baml_src_dir)
