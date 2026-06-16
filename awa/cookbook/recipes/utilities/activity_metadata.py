"""Utility functions for extracting activity metadata."""

import importlib
import inspect
import json
from typing import Any

from cookbook.recipes.sdk.models import TemporalInfo
from cookbook.recipes.utilities.logger import LoggerComponent, get_logger
from cookbook.recipes.utilities.temporal_metadata import ParameterInfo, format_type_annotation


class ActivityInfo(TemporalInfo):
    """Information about a discovered activity.

    Inherits from TemporalInfo and adds activity-specific attributes.

    """


class ActivityMetadata:
    """Contains metadata about a discovered activity."""

    def __init__(
        self,
        name: str,
        function_name: str,
        module: str,
        parameters: list[str],
        parameter_info: list[ParameterInfo] | None = None,
    ) -> None:
        self.name = name
        self.function_name = function_name
        self.module = module
        self.parameters = parameters
        self.parameter_info = parameter_info or []


def get_activity_metadata(activities: list[Any]) -> list[ActivityMetadata]:
    """Get metadata for all discovered activities.

    Returns:
        List of ActivityMetadata objects containing activity information.

    Raises:
        Exception: If activity discovery fails.

    """
    logger = get_logger(LoggerComponent.ACTIVITIES)

    try:
        activity_metadata = []

        for activity_func in activities:
            metadata = _extract_activity_metadata(activity_func)
            activity_metadata.append(metadata)

        # Sort activities by module for consistent ordering
        activity_metadata.sort(key=lambda x: x.module)

        logger.info(f"Retrieved metadata for {len(activity_metadata)} activities")
        return activity_metadata

    except Exception:
        logger.exception("Failed to discover activities")
        raise


def _extract_activity_metadata(activity_func: Any) -> ActivityMetadata:  # noqa: ANN401
    """Extract metadata from an activity function.

    Args:
        activity_func: The activity function to extract metadata from.

    Returns:
        ActivityMetadata object with extracted information.

    """
    # Get the activity name from the function
    activity_name = activity_func.__temporal_activity_definition.name  # noqa: SLF001

    # Get the module name
    module = activity_func.__module__

    # Get the function name
    function_name = activity_func.__name__

    # Extract parameters from the function
    parameters = _extract_activity_parameters(activity_func)
    parameter_info = _extract_activity_parameter_info(activity_func)

    return ActivityMetadata(
        name=activity_name,
        function_name=function_name,
        module=module,
        parameters=parameters,
        parameter_info=parameter_info,
    )


def _extract_activity_parameters(activity_func: Any) -> list[str]:  # noqa: ANN401
    """Extract parameter names from the activity function.

    Args:
        activity_func: The activity function to inspect.

    Returns:
        List of parameter names from the function.

    """
    try:
        # Get the function signature
        signature = inspect.signature(activity_func)

        # Extract all parameter names
        parameters = list(signature.parameters.keys())

        return parameters

    except (AttributeError, TypeError, ValueError):
        # If we can't extract parameters, return empty list
        return []


def _extract_activity_parameter_info(activity_func: Any) -> list[ParameterInfo]:  # noqa: ANN401
    """Extract detailed parameter information from the activity function.

    Args:
        activity_func: The activity function to inspect.

    Returns:
        List of ParameterInfo objects with type information.

    """
    try:
        # Get the function signature
        signature = inspect.signature(activity_func)

        # Extract parameter info
        parameter_info = []
        for param_name, param in signature.parameters.items():
            param_info = ParameterInfo(name=param_name)

            # Extract type annotation if available
            if param.annotation != inspect.Parameter.empty:
                param_info.type_str = format_type_annotation(param.annotation)

            parameter_info.append(param_info)

        return parameter_info

    except (AttributeError, TypeError, ValueError):
        # If we can't extract parameters, return empty list
        return []


def format_activity_parameters(metadata: ActivityMetadata) -> dict:
    """Format activity parameters as JSON schema with fallback to basic names.

    Args:
        metadata: ActivityMetadata object containing parameter information.

    Returns:
        Dictionary representing JSON schema for parameters.

    """
    formatted_parameters = {
        "type": "object",
        "properties": {},
    }

    if metadata.parameter_info:
        for param_info in metadata.parameter_info:
            if param_info.type_str:
                module = importlib.import_module(metadata.module)
                if hasattr(module, param_info.type_str):
                    obj = getattr(module, param_info.type_str)
                    formatted_parameters = {
                        **formatted_parameters,
                        **json.loads(obj.schema_json()),
                    }
                else:
                    formatted_parameters["properties"] = {
                        **formatted_parameters["properties"],
                        param_info.name: {
                            "type": "string",
                        },
                    }
            else:
                formatted_parameters["properties"] = {
                    **formatted_parameters["properties"],
                    param_info.name: {
                        "type": "string",
                    },
                }
    else:
        # Fallback to basic parameter names
        formatted_parameters = metadata.parameters

    if formatted_parameters == []:
        formatted_parameters = {}

    return formatted_parameters
