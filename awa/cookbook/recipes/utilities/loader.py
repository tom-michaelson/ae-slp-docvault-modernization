"""Dynamic loader for Temporal workflows and activities.

This module provides utilities to automatically discover and load workflow and activity
definitions from the recipes directory structure.
"""

import importlib
import inspect
import os
from pathlib import Path
from typing import Any

from cookbook.recipes.utilities.logger import LoggerComponent, get_logger

logger = get_logger(LoggerComponent.LOADER)


def is_workflow_class(obj: Any) -> bool:  # noqa: ANN401
    """Check if an object is a workflow class with the @workflow.defn decorator."""
    return (
        inspect.isclass(obj)
        and hasattr(obj, "__temporal_workflow_definition")
        and obj.__temporal_workflow_definition is not None  # noqa: SLF001
    )


def is_activity_function(obj: Any) -> bool:  # noqa: ANN401
    """Check if an object is an activity function with the @activity.defn decorator."""
    return (
        (inspect.isfunction(obj) or inspect.ismethod(obj))
        and hasattr(obj, "__temporal_activity_definition")
        and obj.__temporal_activity_definition is not None  # noqa: SLF001
    )


def discover_modules_in_package(package_path: str, package_name: str) -> list[str]:
    """Discover all Python modules in a package directory."""
    modules = []
    package_dir = Path(package_path)

    if not package_dir.exists():
        logger.warning(f"Package directory does not exist: {package_path}")
        return modules

    # Recursively find all Python files, excluding __pycache__, __init__.py, output dirs, and node_modules
    for py_file in package_dir.rglob("*.py"):
        parts = py_file.parts
        # Skip __init__.py files, files in __pycache__ directories, and files in output/node_modules/.pnpm directories
        if (
            py_file.name == "__init__.py"
            or "__pycache__" in parts
            or "output" in parts
            or "node_modules" in parts
            or ".pnpm" in parts
        ):
            continue

        # Get relative path from package root
        rel_path = py_file.relative_to(package_dir)
        # Convert file path to module name
        module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")
        full_module_name = f"{package_name}.{module_path}"
        modules.append(full_module_name)
        logger.debug(f"Discovered module: {full_module_name}")

    return modules


def load_workflows_from_package(package_path: str, package_name: str) -> list[type]:
    """Dynamically load all workflow classes from a package."""
    workflows = []
    modules = discover_modules_in_package(package_path, package_name)

    for module_name in modules:
        try:
            logger.debug(f"Importing module: {module_name}")
            module = importlib.import_module(module_name)

            # Inspect all objects in the module
            for name, obj in inspect.getmembers(module):
                if is_workflow_class(obj):
                    logger.debug(f"Found workflow: {name} in {module_name}")
                    workflows.append(obj)

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to import module {module_name}: {e}")
            continue

    # De-duplicate workflows by converting to set and back to list
    return list(set(workflows))


def load_activities_from_package(package_path: str, package_name: str) -> list[Any]:
    """Dynamically load all activity functions from a package."""
    activities = []
    modules = discover_modules_in_package(package_path, package_name)

    for module_name in modules:
        try:
            logger.debug(f"Importing module: {module_name}")
            module = importlib.import_module(module_name)

            # Inspect all objects in the module
            for name, obj in inspect.getmembers(module):
                if is_activity_function(obj):
                    logger.debug(f"Found activity: {name} in {module_name}")
                    activities.append(obj)

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to import module {module_name}: {e}")
            continue

    # De-duplicate activities by converting to set and back to list
    return list(set(activities))


def discover_workflows_and_activities(recipes_dir: str | None = None) -> tuple[list[type], list[Any]]:
    """Discover and load all workflows and activities from the recipes directory.

    Args:
        recipes_dir: Path to the recipes directory. If None, uses the current directory.

    Returns:
        Tuple of (workflows, activities) lists

    """
    if recipes_dir is None:
        recipes_dir = Path(__file__).parent.parent

    recipes_path = Path(recipes_dir)
    workflows_path = recipes_path / "workflows"
    activities_path = recipes_path / "activities"

    # Load workflows
    workflows = load_workflows_from_package(str(workflows_path), "workflows")

    # Load activities from both the activities directory and workflows directory
    activities = []

    # Search in the top-level activities directory
    if activities_path.exists():
        activities.extend(load_activities_from_package(str(activities_path), "activities"))

    # Search in the workflows directory for activities co-located with workflows
    if workflows_path.exists():
        activities.extend(load_activities_from_package(str(workflows_path), "workflows"))

    # De-duplicate the final combined activities list
    activities = list(set(activities))

    return workflows, activities
