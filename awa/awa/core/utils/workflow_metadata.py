"""Utility functions for extracting workflow metadata."""

import importlib
import inspect
from typing import Any, get_args, get_origin

from awa.core.api.registry.storage import get_registry_storage
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.temporal_discovery import TemporalDiscovery


class ParameterInfo:
    """Contains information about a workflow parameter."""

    def __init__(
        self,
        name: str,
        type_str: str | None = None,
    ) -> None:
        self.name = name
        self.type_str = type_str


class WorkflowMetadata:
    """Contains metadata about a discovered workflow."""

    def __init__(
        self,
        name: str,
        class_name: str,
        module: str,
        parameters: list[str],
        parameter_info: list[ParameterInfo] | None = None,
        exposed: bool = False,
        description: str | None = None,
    ) -> None:
        self.name = name
        self.class_name = class_name
        self.module = module
        self.parameters = parameters
        self.parameter_info = parameter_info or []
        self.exposed = exposed
        self.description = description


def get_workflow_metadata(include_recipes: bool = False) -> list[WorkflowMetadata]:
    """Get metadata for all discovered workflows.

    Returns:
        List of WorkflowMetadata objects containing workflow information.

    Raises:
        Exception: If workflow discovery fails.

    """
    logger = get_logger(LoggerComponent.API)

    try:
        discovery = TemporalDiscovery(include_recipes=include_recipes)
        workflows = discovery.discover_workflows_only()

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

    # Extract MCP exposure information
    exposed = getattr(workflow_class, "__exposed__", False)
    description = getattr(workflow_class, "__description__", None)

    return WorkflowMetadata(
        name=name,
        class_name=class_name,
        module=module,
        parameters=parameters,
        parameter_info=parameter_info,
        exposed=exposed,
        description=description,
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
                param_info.type_str = _format_type_annotation(param.annotation)

            parameter_info.append(param_info)

        return parameter_info

    except (AttributeError, TypeError, ValueError):
        # If we can't extract parameters, return empty list
        return []


def _format_type_annotation(annotation: Any) -> str:  # noqa: ANN401
    """Format a type annotation as a string.

    Args:
        annotation: The type annotation to format.

    Returns:
        String representation of the type annotation.

    """
    # Handle None type
    if annotation is type(None):
        return "None"

    # Handle generic types (e.g., list[str], dict[str, Any], List[str], Dict[str, Any])
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        if args:
            formatted_args = ", ".join(_format_type_annotation(arg) for arg in args)
            origin_name = getattr(origin, "__name__", str(origin))
            return f"{origin_name}[{formatted_args}]"
        return getattr(origin, "__name__", str(origin))

    # Handle basic types with __name__
    if hasattr(annotation, "__name__"):
        return annotation.__name__

    # Handle union types (e.g., str | None)
    if hasattr(annotation, "__class__") and "UnionType" in annotation.__class__.__name__:
        return str(annotation)

    # Default: convert to string
    return str(annotation)


def format_workflow_parameters(metadata: WorkflowMetadata) -> dict:
    """Format workflow parameters as 'name: type' strings with fallback to basic names.

    For nullable parameters (those with | None or | SkipJsonSchema[None]),
    adds 'x-nullable-input' property to schema to enable optional input UI.

    Args:
        metadata: WorkflowMetadata object containing parameter information.

    Returns:
        Dict with JSON Schema structure and x-nullable-input flag if applicable.

    """
    formatted_parameters = {
        "type": "object",
        "properties": {},
    }

    is_nullable = False  # Track if any parameter is nullable

    if metadata.parameter_info:
        for param_info in metadata.parameter_info:
            if param_info.type_str:
                module = importlib.import_module(metadata.module)
                type_str = param_info.type_str

                # Detect nullability - check for multiple patterns:
                # 1. "Type | None" (modern union syntax)
                # 2. "Union[Type, None]" (typing.Union)
                # 3. "Optional[Type]" (typing.Optional)
                # 4. "SkipJsonSchema[None]" or "Annotated[None, SkipJsonSchema()]"
                nullable_patterns = [
                    " | None",
                    ", None]",  # Union[Type, None]
                    "Optional[",
                    "SkipJsonSchema",
                    "Annotated[None",
                ]

                if any(pattern in type_str for pattern in nullable_patterns):
                    is_nullable = True

                    # Extract the actual type from Union/Optional/Annotated patterns
                    if type_str.startswith("Union["):
                        # Union[Type, None] or Union[Type, Annotated[None, ...]]
                        # Extract the first non-None type
                        import re

                        match = re.match(r"Union\[([^,\[\]]+).*\]", type_str)
                        if match:
                            type_str = match.group(1).strip()
                    elif type_str.startswith("Optional["):
                        # Optional[Type] -> Type
                        type_str = type_str[9:-1]  # Remove "Optional[" and "]"
                    elif " | " in type_str:
                        # Type | None or Type | SkipJsonSchema[None]
                        parts = type_str.split(" | ")
                        # Get the first part that's not None or SkipJsonSchema
                        for part in parts:
                            if part != "None" and "SkipJsonSchema" not in part:
                                type_str = part
                                break

                imports = vars(module)
                if type_str in imports:
                    object = imports[type_str]  # noqa: A001
                    # Use model_json_schema() for richer metadata instead of schema_json()
                    schema = object.model_json_schema()

                    # Merge the schema, preserving field metadata
                    formatted_parameters = {
                        **formatted_parameters,
                        **schema,
                    }

                    # Ensure we have the correct structure
                    if "properties" not in formatted_parameters:
                        formatted_parameters["properties"] = {}
                else:
                    formatted_parameters["properties"] = {
                        **formatted_parameters["properties"],
                        param_info.name: {
                            "type": "string",
                            "description": f"Parameter {param_info.name}",
                        },
                    }
            else:
                formatted_parameters["properties"] = {
                    **formatted_parameters["properties"],
                    param_info.name: {
                        "type": "string",
                        "description": f"Parameter {param_info.name}",
                    },
                }
    # Fallback to basic parameter names - convert list to dict format
    elif isinstance(metadata.parameters, list) and metadata.parameters:
        formatted_parameters = {
            "type": "object",
            "properties": {param: {"type": "string"} for param in metadata.parameters},
        }
    elif metadata.parameters == []:
        formatted_parameters = {}
    else:
        formatted_parameters = metadata.parameters

    # Add custom property to indicate nullable input
    if is_nullable:
        formatted_parameters["x-nullable-input"] = True

    return formatted_parameters


async def get_workflow_queue(workflow_name: str) -> str | None:
    """Get the task queue for a specific workflow by name.

    Reads registry files to find the workflow and its associated task queue.
    No discovery or complex logic - just reads existing registry files.

    Args:
        workflow_name: The name of the workflow to look up

    Returns:
        str: The task queue for the workflow, or None if not found

    """
    logger = get_logger(LoggerComponent.CLIENT)

    try:
        # Read all worker registrations from registry files
        storage = get_registry_storage()
        active_workers = await storage.list_active_workers()

        # Look for the workflow in all registered workers
        for worker in active_workers:
            for workflow_def in worker.workflows:
                if workflow_def.name == workflow_name:
                    logger.debug(
                        f"Found workflow '{workflow_name}' from {worker.worker_name} "
                        f"using queue '{workflow_def.task_queue}'",
                    )
                    return workflow_def.task_queue

        logger.debug(f"Workflow '{workflow_name}' not found in any registry files")
        return None

    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to read registry files for workflow '{workflow_name}': {e}")
        return None
