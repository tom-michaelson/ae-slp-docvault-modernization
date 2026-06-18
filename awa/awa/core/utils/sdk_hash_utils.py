"""Enhanced SDK source hash tracking and validation with granular hash management.

This module provides utilities for calculating and managing hashes of individual SDK
components (constants, models, and utility functions) to enable fine-grained change
detection and validation for SDK generation.
"""

from pathlib import Path

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.cache_utils import CacheUtils
from awa.core.utils.file_system_utils import FileSystemUtils

logger = get_logger(LoggerComponent.ACTIVITY)


class SdkHashUtils:
    """Enhanced utilities for granular SDK source hash tracking and validation."""

    # Base path for storing hash files
    HASH_BASE_PATH = Path("sdk_dist/.hash")

    # Hash file names
    CONSTANTS_HASH_FILE = "constants.hash"
    MODELS_HASH_FILE = "models.hash"
    WORKFLOW_UTILS_DIR = "workflow_utils"
    ACTIVITY_UTILS_DIR = "activity_utils"
    GENERAL_UTILS_DIR = "general_utils"

    @staticmethod
    async def ensure_hash_directories() -> None:
        """Ensure all hash directories exist."""
        dirs = [
            SdkHashUtils.HASH_BASE_PATH,
            SdkHashUtils.HASH_BASE_PATH / SdkHashUtils.WORKFLOW_UTILS_DIR,
            SdkHashUtils.HASH_BASE_PATH / SdkHashUtils.ACTIVITY_UTILS_DIR,
            SdkHashUtils.HASH_BASE_PATH / SdkHashUtils.GENERAL_UTILS_DIR,
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    async def calculate_constants_hash() -> str:
        """Calculate hash of constants.py file.

        Returns:
            A SHA-256 hash string representing the current state of constants.py.

        Raises:
            FileNotFoundError: If the constants.py file doesn't exist.

        """
        constants_path = Path("awa/sdk/constants.py")

        if not constants_path.exists():
            raise FileNotFoundError(f"Constants file not found: {constants_path}")

        logger.info(f"Calculating hash for constants file: {constants_path}")

        content = await FileSystemUtils.read_async(str(constants_path), default="")
        hash_value = CacheUtils.hash(content)

        logger.info(f"Constants hash calculated: {hash_value[:8]}...")
        return hash_value

    @staticmethod
    async def calculate_models_hash() -> str:
        """Calculate hash of all model files in awa/sdk/models directory.

        Returns:
            A SHA-256 hash string representing the current state of all models.

        Raises:
            FileNotFoundError: If the models directory doesn't exist.

        """
        models_path = Path("awa/sdk/models")

        if not models_path.exists():
            raise FileNotFoundError(f"Models directory not found: {models_path}")

        logger.info(f"Calculating hash for models directory: {models_path}")

        # Read all model files and create structured data for hashing
        models_data: dict[str, str] = {}

        for py_file in models_path.rglob("*.py"):
            if py_file.name != "__init__.py":
                relative_path = str(py_file.relative_to(models_path))
                models_data[relative_path] = await FileSystemUtils.read_async(str(py_file), default="")

        hash_value = CacheUtils.hash(models_data)
        logger.info(f"Models hash calculated: {hash_value[:8]}...")
        return hash_value

    @staticmethod
    async def calculate_utility_function_hash(util_type: str, function_name: str) -> str:
        """Calculate hash of a specific utility function file.

        Args:
            util_type: Type of utility ("workflow", "activity", or "general")
            function_name: Name of the function (e.g., "read_file")

        Returns:
            A SHA-256 hash string representing the current state of the utility function.

        Raises:
            FileNotFoundError: If the utility function file doesn't exist.
            ValueError: If util_type is invalid.

        """
        if util_type not in ["workflow", "activity", "general"]:
            raise ValueError(f"Invalid util_type: {util_type}. Must be 'workflow', 'activity', or 'general'.")

        util_path = Path("awa/sdk/utils") / util_type / f"{function_name}.py"

        if not util_path.exists():
            raise FileNotFoundError(f"Utility function file not found: {util_path}")

        logger.debug(f"Calculating hash for utility function: {util_path}")

        content = await FileSystemUtils.read_async(str(util_path), default="")
        hash_value = CacheUtils.hash(content)

        logger.debug(f"Utility function {function_name} hash: {hash_value[:8]}...")
        return hash_value

    @staticmethod
    async def get_all_utility_functions() -> dict[str, list[str]]:
        """Discover all utility functions by scanning the utils directory.

        Returns:
            Dictionary with keys "workflow", "activity", and "general", each containing a list
            of function names.

        """
        utils_path = Path("awa/sdk/utils")
        functions = {"workflow": [], "activity": [], "general": []}

        for util_type in ["workflow", "activity", "general"]:
            type_path = utils_path / util_type
            if type_path.exists():
                for py_file in type_path.glob("*.py"):
                    if py_file.name != "__init__.py":
                        function_name = py_file.stem
                        functions[util_type].append(function_name)

        logger.info(
            f"Discovered utility functions - "
            f"workflow: {len(functions['workflow'])}, "
            f"activity: {len(functions['activity'])}, "
            f"general: {len(functions['general'])}",
        )
        return functions

    @staticmethod
    async def calculate_all_hashes() -> dict[str, str]:
        """Calculate hashes for all SDK components.

        Returns:
            Dictionary mapping component paths to their hashes:
            - "constants": hash of constants.py
            - "models": hash of all models
            - "workflow_utils/<name>": hash of each workflow utility function
            - "activity_utils/<name>": hash of each activity utility function
            - "general_utils/<name>": hash of each general utility function

        """
        await SdkHashUtils.ensure_hash_directories()

        hashes = {}

        # Calculate constants hash
        try:
            hashes["constants"] = await SdkHashUtils.calculate_constants_hash()
        except FileNotFoundError:
            logger.warning("Constants file not found, skipping")

        # Calculate models hash
        try:
            hashes["models"] = await SdkHashUtils.calculate_models_hash()
        except FileNotFoundError:
            logger.warning("Models directory not found, skipping")

        # Calculate utility function hashes
        functions = await SdkHashUtils.get_all_utility_functions()

        for util_type, function_names in functions.items():
            for function_name in function_names:
                try:
                    hash_key = f"{util_type}_utils/{function_name}"
                    hashes[hash_key] = await SdkHashUtils.calculate_utility_function_hash(
                        util_type,
                        function_name,
                    )
                except FileNotFoundError:
                    logger.warning(f"Utility function {util_type}/{function_name} not found, skipping")

        logger.info(f"Calculated {len(hashes)} component hashes")
        return hashes

    @staticmethod
    async def load_stored_hashes() -> dict[str, str]:
        """Load all previously stored hashes.

        Returns:
            Dictionary mapping component paths to their stored hashes.

        """
        await SdkHashUtils.ensure_hash_directories()

        stored_hashes = {}

        # Load constants hash
        constants_hash_path = SdkHashUtils.HASH_BASE_PATH / SdkHashUtils.CONSTANTS_HASH_FILE
        if constants_hash_path.exists():
            try:
                content = await FileSystemUtils.read_async(str(constants_hash_path))
                stored_hashes["constants"] = content.strip()
            except OSError:
                logger.warning("Failed to read constants hash")

        # Load models hash
        models_hash_path = SdkHashUtils.HASH_BASE_PATH / SdkHashUtils.MODELS_HASH_FILE
        if models_hash_path.exists():
            try:
                content = await FileSystemUtils.read_async(str(models_hash_path))
                stored_hashes["models"] = content.strip()
            except OSError:
                logger.warning("Failed to read models hash")

        # Load utility function hashes
        for util_type in ["workflow", "activity", "general"]:
            util_dir = SdkHashUtils.HASH_BASE_PATH / f"{util_type}_utils"
            if util_dir.exists():
                for hash_file in util_dir.glob("*.hash"):
                    function_name = hash_file.stem
                    try:
                        content = await FileSystemUtils.read_async(str(hash_file))
                        hash_key = f"{util_type}_utils/{function_name}"
                        stored_hashes[hash_key] = content.strip()
                    except OSError:
                        logger.warning(f"Failed to read hash for {util_type}/{function_name}")

        logger.info(f"Loaded {len(stored_hashes)} stored hashes")
        return stored_hashes

    @staticmethod
    async def store_hashes(hashes: dict[str, str]) -> None:
        """Store hashes for all SDK components.

        Args:
            hashes: Dictionary mapping component paths to their hashes.

        """
        await SdkHashUtils.ensure_hash_directories()

        for component_path, hash_value in hashes.items():
            if component_path == "constants":
                hash_file_path = SdkHashUtils.HASH_BASE_PATH / SdkHashUtils.CONSTANTS_HASH_FILE
            elif component_path == "models":
                hash_file_path = SdkHashUtils.HASH_BASE_PATH / SdkHashUtils.MODELS_HASH_FILE
            elif "/" in component_path:
                # Utility function
                util_type, function_name = component_path.split("/")
                util_type = util_type.replace("_utils", "")
                hash_file_path = SdkHashUtils.HASH_BASE_PATH / f"{util_type}_utils" / f"{function_name}.hash"
            else:
                logger.warning(f"Unknown component path format: {component_path}")
                continue

            try:
                await FileSystemUtils.write_async(str(hash_file_path), hash_value)
                logger.debug(f"Stored hash for {component_path}: {hash_value[:8]}...")
            except OSError:
                logger.exception(f"Failed to store hash for {component_path}")

    @staticmethod
    async def get_changed_components() -> dict[str, str]:
        """Get components that have changed since last hash storage.

        Returns:
            Dictionary mapping changed component paths to their new hashes.

        """
        current_hashes = await SdkHashUtils.calculate_all_hashes()
        stored_hashes = await SdkHashUtils.load_stored_hashes()

        changed = {}

        for component_path, current_hash in current_hashes.items():
            stored_hash = stored_hashes.get(component_path)
            if stored_hash is None or stored_hash != current_hash:
                changed[component_path] = current_hash
                if stored_hash is None:
                    logger.info(f"New component: {component_path}")
                else:
                    logger.info(
                        f"Changed component: {component_path} (old: {stored_hash[:8]}..., new: {current_hash[:8]}...)",
                    )

        # Check for deleted components
        for component_path in stored_hashes:
            if component_path not in current_hashes:
                logger.info(f"Deleted component: {component_path}")

        return changed

    @staticmethod
    async def has_any_changes() -> bool:
        """Check if any SDK components have changed.

        Returns:
            True if any components have changed, False otherwise.

        """
        changed = await SdkHashUtils.get_changed_components()
        return len(changed) > 0
