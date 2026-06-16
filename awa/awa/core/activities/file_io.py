from temporalio import activity

from awa.core import constants
from awa.core.utils.file_system_utils import FileSystemUtils
from awa.sdk import constants as sdk_constants
from awa.sdk.models.folder_info import FolderInfo
from awa.sdk.models.input_params import InputParams


@activity.defn(name=sdk_constants.ACTIVITY_IS_DIRECTORY)
async def is_directory_activity(path: str) -> bool:
    """Check if a path is a directory.

    This function uses `fsspec` to check if a path is a directory.
    """
    return FileSystemUtils.is_directory(path)


@activity.defn(name=sdk_constants.ACTIVITY_READ_FILE)
async def read_file_activity(path: str, default: str | None = None) -> str:
    """Read the entire content of a file from a specified path.

    This function uses `fsspec` to open and read a file, which allows it to
    handle various file systems like local, S3, GCS, etc., based on the path's
    protocol prefix.

    Args:
        path: A string representing the file path or URI.
        default: A string to return if the file does not exist.

    Returns:
        A string containing the entire content of the file.

    """
    return await FileSystemUtils.read_async(path, default)


@activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_BYTES)
async def read_file_bytes_activity(path: str, default: bytes | None = None) -> bytes:
    """Read the entire content of a file from a specified path (in raw bytes).

    This function uses `fsspec` to open and read a file, which allows it to
    handle various file systems like local, S3, GCS, etc., based on the path's
    protocol prefix.

    Args:
        path: A string representing the file path or URI.
        default: A bytes to return if the file does not exist.

    Returns:
        A bytes containing the entire content of the file.

    """
    return await FileSystemUtils.read_bytes_async(path, default)


@activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
async def read_file_or_directory_activity(input_params: InputParams) -> str:
    r"""Read content from either a file or directory based on the path type.

    This function dynamically determines whether the given path is a file or
    directory and reads accordingly. For directories, it reads all files
    recursively and returns their combined content using customizable join
    templates. For files, it reads the individual file content.

    Args:
        input_params: An InputParams object containing:
            - name: A descriptive name for the input (not used in processing)
            - path: The file or directory path to read from
            - ignore_file_path: Optional path to .gitignore-style file for
              directories (ignored for single files)
            - default: Default content to return if file doesn't exist
              (only used for single files)
            - directory_join_str: String used to join multiple file contents
              when reading directories (defaults to "\n")
            - directory_join_template_str: Template string for formatting
              each file's content when reading directories (defaults to
              '<file name="{file}">\n{content}\n</file>')

    Returns:
        A string containing the file content or combined directory content.

    """
    if FileSystemUtils.is_directory(input_params.path):
        directory_result = await FileSystemUtils.read_directory_async(input_params.path, input_params.ignore_file_path)
        directory_join_str = input_params.directory_join_str or constants.DEFAULT_DIRECTORY_JOIN_STR
        directory_join_template_str = (
            input_params.directory_join_template_str or constants.DEFAULT_DIRECTORY_JOIN_TEMPLATE_STR
        )
        directory_content_str = directory_join_str.join(
            str.format(directory_join_template_str, file=result["file"], content=result["content"])
            for result in directory_result
        )
        return directory_content_str
    return await FileSystemUtils.read_async(input_params.path, input_params.default)


@activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
async def write_file_activity(path: str, content: str) -> None:
    """Write string content to a file at a specified path.

    This function uses `fsspec` to open and write to a file, which allows it to
    handle various file systems. If the file already exists, its content will
    be overwritten. If the file does not exist, it will be created.

    Args:
        path: A string representing the file path or URI.
        content: The string content to be written to the file.

    """
    await FileSystemUtils.write_async(path, content)


@activity.defn(name=sdk_constants.ACTIVITY_COPY_DIRECTORY)
async def copy_directory_activity(
    source_path: str,
    destination_path: str,
    ignore_file_path: str | None = None,
) -> list[str]:
    """Recursively copies a directory from a source to a destination.

    This function uses `fsspec` to copy a directory. It determines the
    filesystem (e.g., local, S3, GCS) from the protocol prefix of the
    source path. The copy operation is performed within this single
    filesystem. Cross-filesystem copies are not supported by this activity.

    If an ignore file is provided, it will be parsed using .gitignore patterns.
    Files matching these patterns will not be copied.

    Returns:
        A list of full paths to files that were copied.

    Args:
        source_path: The path or URI of the source directory. Must include a
                     protocol prefix (e.g., 's3://') for remote filesystems.
        destination_path: The path or URI for the destination, which must be
                          on the same filesystem as the source.
        ignore_file_path: Optional path to a file containing .gitignore-style
                          patterns for files to ignore during the copy.

    """
    return await FileSystemUtils.copy_directory_async(source_path, destination_path, ignore_file_path)


@activity.defn(name=sdk_constants.ACTIVITY_LIST_DIRECTORY)
async def list_directory_activity(
    source_path: str,
    ignore_file_path: str | None = None,
) -> list[str]:
    """List all files in a directory, optionally ignoring based on .gitignore.

    This function recursively finds all files in the given source path.
    If an ignore file is provided, it filters the file list based on
    .gitignore-style patterns. It returns a flat list of full file paths.

    The returned paths are suitable for use with other file activities like
    `read_file` or `write_file`.

    Args:
        source_path: The path or URI of the source directory.
        ignore_file_path: Optional path to a file with .gitignore patterns.

    Returns:
        A list of full paths to files in the directory.

    """
    return await FileSystemUtils.list_directory_async(source_path, ignore_file_path)


@activity.defn(name=sdk_constants.ACTIVITY_READ_DIRECTORY)
async def read_directory_activity(
    source_path: str,
    ignore_file_path: str | None = None,
) -> list[dict[str, str]]:
    """Read all files in a directory recursively, optionally ignoring based on .gitignore.

    This function recursively finds and reads all files in the given source path.
    If an ignore file is provided, it filters the file list based on
    .gitignore-style patterns. It returns a list of dictionaries containing
    file paths and their content.

    File reads are performed in parallel for optimal performance.

    Args:
        source_path: The path or URI of the source directory.
        ignore_file_path: Optional path to a file with .gitignore patterns.

    Returns:
        A list of dictionaries with 'file' and 'content' keys for each file.

    """
    return await FileSystemUtils.read_directory_async(source_path, ignore_file_path)


@activity.defn(name=sdk_constants.ACTIVITY_DELETE_DIRECTORY)
async def remove_directory_activity(path: str) -> None:
    """Delete a directory and all its contents.

    This function uses `fsspec` to delete a directory recursively, which allows it to
    handle various file systems like local, S3, GCS, etc., based on the path's
    protocol prefix. The directory and all files and subdirectories within it
    will be permanently removed.

    Args:
        path: A string representing the directory path or URI to delete.

    """
    await FileSystemUtils.remove_directory_async(path)


@activity.defn(name=sdk_constants.ACTIVITY_COPY_FILE)
async def copy_file_activity(source_path: str, destination_path: str) -> None:
    """Copy a file from source to destination.

    This function uses `fsspec` to copy a file. It determines the
    filesystem (e.g., local, S3, GCS) from the protocol prefix of the
    source path. The copy operation is performed within this single
    filesystem. Cross-filesystem copies are not supported by this activity.

    Args:
        source_path: The path or URI of the source file. Must include a
                     protocol prefix (e.g., 's3://') for remote filesystems.
        destination_path: The path or URI for the destination, which must be
                          on the same filesystem as the source.

    """
    await FileSystemUtils.copy_file_async(source_path, destination_path)


@activity.defn(name=sdk_constants.ACTIVITY_LIST_ALL_DIRECTORIES_RECURSIVE)
async def list_all_directories_recursive(source_dir: str) -> list[str]:
    """Recursively list all directories under the source directory.

    This function uses the FileSystemUtils to recursively find all directories
    under the given source directory path. It returns a sorted list of full
    directory paths.

    Args:
        source_dir: The root directory to search from.

    Returns:
        A list of directory paths as strings.

    """
    return await FileSystemUtils.list_all_directories_recursive_async(source_dir)


@activity.defn(name=sdk_constants.ACTIVITY_GET_DIRECTORY_INFO)
async def get_directory_info(directory_path: str) -> FolderInfo:
    """Get information about a single directory including its immediate files and subdirectories.

    This function examines a single directory and returns information about its
    immediate contents without recursing into subdirectories. It provides lists
    of file names and subdirectory names found directly in the specified directory.

    Args:
        directory_path: The path to the directory to analyze.

    Returns:
        A DirectoryInfo object containing:
            - path: The directory path
            - files: List of file names (not full paths)
            - subdirectories: List of subdirectory names (not full paths)

    """
    return await FileSystemUtils.get_directory_info_async(directory_path)
