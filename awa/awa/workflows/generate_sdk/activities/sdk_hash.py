"""SDK hash calculation and storage activities for workflow operations."""

from temporalio import activity

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.sdk_hash_utils import SdkHashUtils
from awa.workflows.generate_sdk import constants

logger = get_logger(LoggerComponent.ACTIVITY)

# New granular hash activities


@activity.defn(name=constants.ACTIVITY_CALCULATE_ALL_COMPONENT_HASHES)
async def calculate_all_component_hashes_activity() -> dict[str, str]:
    """Calculate hashes for all SDK components using granular tracking.

    Returns:
        Dictionary mapping component paths to their hashes.

    """
    logger.info("Calculating all SDK component hashes")
    return await SdkHashUtils.calculate_all_hashes()


@activity.defn(name=constants.ACTIVITY_GET_CHANGED_COMPONENTS)
async def get_changed_components_activity() -> dict[str, str]:
    """Get SDK components that have changed since last generation.

    Returns:
        Dictionary mapping changed component paths to their new hashes.

    """
    logger.info("Checking for changed SDK components")
    return await SdkHashUtils.get_changed_components()


@activity.defn(name=constants.ACTIVITY_STORE_COMPONENT_HASHES)
async def store_component_hashes_activity(hashes: dict[str, str]) -> None:
    """Store hashes for SDK components.

    Args:
        hashes: Dictionary mapping component paths to their hashes.

    """
    logger.info(f"Storing {len(hashes)} component hashes")
    await SdkHashUtils.store_hashes(hashes)
