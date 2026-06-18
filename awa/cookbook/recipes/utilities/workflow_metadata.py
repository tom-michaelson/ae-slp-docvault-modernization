"""Utility functions for extracting workflow metadata."""

import importlib
import inspect
import json
from typing import Any

from cookbook.recipes.sdk.models import TemporalInfo
from cookbook.recipes.utilities.logger import LoggerComponent, get_logger
from cookbook.recipes.utilities.temporal_metadata import ParameterInfo, format_type_annotation


class WorkflowInfo(TemporalInfo):
    """Information about a discovered workflow.

    Inherits from TemporalInfo and adds workflow-specific attributes.

    """


class WorkflowMetadata:
    """Contains metadata about a discovered workflow."""

    def __init__(
        self,
        name: str,
        class_name: str,
        module: str,
        parameters: list[str],
        parameter_info: list[ParameterInfo] | None = None,
    ) -> None:
        self.name = name
        self.class_name = class_name
        self.module = module
        self.parameters = parameters
        self.parameter_info = parameter_info or []


def get_workflow_metadata(workflows: list[Any]) -> list[WorkflowMetadata]:
    """Get metadata for all discovered workflows.

    Returns:
        List of WorkflowMetadata objects containing workflow information.

    Raises:
        Exception: If workflow discovery fails.

    """
    logger = get_logger(LoggerComponent.WORKFLOWS)

    try:
        workflow_metadata = []

        for workflow_class in workflows:
            metadata = _extract_workflow_metadata(workflow_class)
            workflow_metadata.append(metadata)

        # Sort workflows by module for consistent ordering
        workflow_metadata.sort(key=lambda x: x.module)

        logger.info(f"Retrieved metadata for {len(workflow_metadata)} workflows")
        return workflow_metadata

    except Exception:
        logger.exception("Failed to discover workflows")
        raise


def _extract_workflow_metadata(workflow_class: Any) -> WorkflowMetadata:  # noqa: ANN401
    """Extract metadata from a workflow class.

    Args:
        workflow_class: The workflow class to extract metadata from.

    Returns:
        WorkflowMetadata object with extracted information.

    """
    # Get the workflow name from the class
    class_name = workflow_class.__temporal_workflow_definition.name  # noqa: SLF001

    # Get the module name
    module = workflow_class.__module__

    # Get the workflow name (same as class name for now)
    name = class_name

    # Extract parameters from the run method
    parameters = _extract_run_method_parameters(workflow_class)
    parameter_info = _extract_run_method_parameter_info(workflow_class)

    return WorkflowMetadata(
        name=name,
        class_name=class_name,
        module=module,
        parameters=parameters,
        parameter_info=parameter_info,
    )


def _extract_run_method_parameters(workflow_class: Any) -> list[str]:  # noqa: ANN401
    """Extract parameter names from the workflow's run method.

    Args:
        workflow_class: The workflow class to inspect.

    Returns:
        List of parameter names from the run method.

    """
    try:
        # Get the run method from the workflow class
        run_method = getattr(workflow_class, "run", None)
        if run_method is None:
            return []

        # Get the method signature
        signature = inspect.signature(run_method)

        # Extract parameter names, excluding 'self'
        parameters = [param_name for param_name in signature.parameters if param_name != "self"]

        return parameters

    except (AttributeError, TypeError, ValueError):
        # If we can't extract parameters, return empty list
        return []


def _extract_run_method_parameter_info(workflow_class: Any) -> list[ParameterInfo]:  # noqa: ANN401
    """Extract detailed parameter information from the workflow's run method.

    Args:
        workflow_class: The workflow class to inspect.

    Returns:
        List of ParameterInfo objects with type information.

    """
    try:
        # Get the run method from the workflow class
        run_method = getattr(workflow_class, "run", None)
        if run_method is None:
            return []

        # Get the method signature
        signature = inspect.signature(run_method)

        # Extract parameter info, excluding 'self'
        parameter_info = []
        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            param_info = ParameterInfo(name=param_name)

            # Extract type annotation if available
            if param.annotation != inspect.Parameter.empty:
                param_info.type_str = format_type_annotation(param.annotation)

            parameter_info.append(param_info)

        return parameter_info

    except (AttributeError, TypeError, ValueError):
        # If we can't extract parameters, return empty list
        return []


def format_workflow_parameters(metadata: WorkflowMetadata) -> dict:
    """Format workflow parameters as 'name: type' strings with fallback to basic names.

    Args:
        metadata: WorkflowMetadata object containing parameter information.

    Returns:
        List of formatted parameter strings.

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
                    object = getattr(module, param_info.type_str)  # noqa: A001
                    formatted_parameters = {
                        **formatted_parameters,
                        **json.loads(object.schema_json()),
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
