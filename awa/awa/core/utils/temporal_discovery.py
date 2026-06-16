import importlib
import inspect
import pkgutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.cli_utils import is_packaged_mode


class TemporalDiscovery:
    """Utility class for dynamically discovering Temporal workflows and activities."""

    def __init__(self, base_path: str | None = None, include_recipes: bool = False) -> None:
        if base_path is None:
            # Auto-detect the correct base path
            if is_packaged_mode():
                # In packaged mode, use the actual package path
                import awa

                self.base_path = Path(awa.__file__).parent
            else:
                # In development mode, use relative path
                self.base_path = Path("awa")
        else:
            # Allow explicit override
            self.base_path = Path(base_path)
        self.include_recipes = include_recipes
        self.logger = get_logger(LoggerComponent.CLI)

        # Add the awa directory to Python path if not already present
        awa_path = str(self.base_path.absolute())
        if awa_path not in sys.path:
            sys.path.insert(0, awa_path)

        # Determine the repository root for cookbook access
        if self.include_recipes:
            # Repository root is the parent of the awa directory
            self.repo_root = self.base_path.parent if self.base_path.name == "awa" else self.base_path.parent.parent

            # Add repository root to sys.path so cookbook can be imported
            repo_root_str = str(self.repo_root.absolute())
            if repo_root_str not in sys.path:
                sys.path.insert(0, repo_root_str)
                self.logger.debug(f"Added repository root to sys.path: {repo_root_str}")

    def discover_workflows_and_activities(self, dependencies: list[Any] | None = None) -> tuple[list[Any], list[Any]]:
        """Discover all workflows and activities in the codebase.

        Returns:
            A tuple of (workflows, activities) lists

        """
        if not dependencies:
            dependencies = []

        workflows = []
        activities = []

        # Log recipe configuration status
        if self.include_recipes:
            self.logger.info("Recipe workflows and activities are ENABLED")
        else:
            self.logger.info("Recipe workflows and activities are DISABLED")

        # Define potential workflow and activity directories
        activity_paths = [
            self.base_path / "activities",
            self.base_path / "core" / "activities",
        ]
        workflow_paths = [
            self.base_path / "workflows",
            self.base_path / "core" / "workflows",
        ]

        # Conditionally add recipe paths
        if self.include_recipes:
            activity_paths.append(self.repo_root / "cookbook" / "recipes" / "activities")
            workflow_paths.append(self.repo_root / "cookbook" / "recipes" / "workflows")
            self.logger.debug("Added cookbook recipe directories to discovery paths")

        # Scan all activity directories
        for activities_path in activity_paths:
            if activities_path.exists():
                # Determine the module prefix based on the path
                if "cookbook" in activities_path.parts and "recipes" in activities_path.parts:
                    module_prefix = "cookbook.recipes.activities"
                elif "core" in activities_path.parts:
                    module_prefix = "core.activities"
                else:
                    module_prefix = "activities"
                activities.extend(self._scan_activities(activities_path, module_prefix, dependencies))

        # Scan all workflow directories
        # Make this recursive as we have sub-folders in the workflows and activities directories
        for workflows_path in workflow_paths:
            if workflows_path.exists():
                # Determine the module prefix based on the path
                if "cookbook" in workflows_path.parts and "recipes" in workflows_path.parts:
                    module_prefix = "cookbook.recipes.workflows"
                elif "core" in workflows_path.parts:
                    module_prefix = "core.workflows"
                else:
                    module_prefix = "workflows"
                workflows.extend(self._scan_workflows(workflows_path, module_prefix))

                # Also scan for activities within workflow directories
                # Many workflow directories contain nested activities subdirectories
                activities.extend(self._scan_activities(workflows_path, module_prefix, dependencies))

        self.logger.info(f"Discovered {len(workflows)} workflows and {len(activities)} activities")

        # Deduplicate workflows and activities more robustly
        deduplicated_workflows = self._deduplicate_callables(workflows)
        deduplicated_activities = self._deduplicate_callables(activities)

        self.logger.info(
            f"After deduplication: {len(deduplicated_workflows)} workflows and "
            f"{len(deduplicated_activities)} activities",
        )
        return deduplicated_workflows, deduplicated_activities

    def _deduplicate_callables(self, callables: list[Any]) -> list[Any]:
        """Deduplicate callables (functions/methods) by their name and module.

        Args:
            callables: List of callable objects (functions, methods, classes)

        Returns:
            Deduplicated list of callables

        """
        seen = set()
        deduplicated = []

        for callable_obj in callables:
            # Create a unique identifier for this callable
            if hasattr(callable_obj, "__name__") and hasattr(callable_obj, "__module__"):
                # For functions and classes
                module_name = self._normalize_module_name(callable_obj.__module__)
                identifier = f"{module_name}.{callable_obj.__name__}"
            elif hasattr(callable_obj, "__func__") and hasattr(callable_obj.__func__, "__name__"):
                # For bound methods, use the function name and the class name
                func_name = callable_obj.__func__.__name__
                class_name = (
                    callable_obj.__self__.__class__.__name__ if hasattr(callable_obj, "__self__") else "unknown"
                )
                module_name = self._normalize_module_name(getattr(callable_obj.__func__, "__module__", "unknown"))
                identifier = f"{module_name}.{class_name}.{func_name}"
            elif hasattr(callable_obj, "__name__"):
                # Fallback for other callable objects
                identifier = callable_obj.__name__
            else:
                # Final fallback - use object id (shouldn't happen for Temporal objects)
                identifier = str(id(callable_obj))

            if identifier not in seen:
                seen.add(identifier)
                deduplicated.append(callable_obj)
            else:
                # Try to get a more readable name for logging
                display_name = identifier
                if self._is_workflow_class(callable_obj):
                    display_name = self._get_workflow_name(callable_obj)
                elif self._is_activity_function(callable_obj):
                    display_name = self._get_activity_name(callable_obj)
                self.logger.debug(f"Skipping duplicate callable: {display_name} (internal: {identifier})")

        return deduplicated

    def _normalize_module_name(self, module_name: str) -> str:
        """Normalize module names to handle variations like 'core.activities' vs 'awa.core.activities'.

        Args:
            module_name: Original module name

        Returns:
            Normalized module name

        """
        if not module_name or module_name == "unknown":
            return module_name

        # Handle cases where module name starts with 'awa.' - remove it for normalization
        if module_name.startswith("awa."):
            return module_name[4:]  # Remove 'awa.' prefix

        return module_name

    def discover_workflows_only(self) -> list[Any]:
        """Discover only workflows, skipping activity discovery to avoid dependency warnings.

        This method is useful for scenarios like listing workflows where activities
        are not needed and dependency injection warnings should be avoided.

        Returns:
            List of discovered workflow classes.

        """
        workflows = []

        # Log recipe configuration status
        if self.include_recipes:
            self.logger.info("Recipe workflows are ENABLED")
        else:
            self.logger.info("Recipe workflows are DISABLED")

        # Define potential workflow directories
        workflow_paths = [
            self.base_path / "workflows",
            self.base_path / "core" / "workflows",
        ]

        # Conditionally add recipe workflow paths
        if self.include_recipes:
            workflow_paths.append(self.repo_root / "cookbook" / "recipes" / "workflows")
            self.logger.debug("Added cookbook recipe workflow directory to discovery paths")

        # Scan all workflow directories
        for workflows_path in workflow_paths:
            if workflows_path.exists():
                # Determine the module prefix based on the path
                if "cookbook" in workflows_path.parts and "recipes" in workflows_path.parts:
                    module_prefix = "cookbook.recipes.workflows"
                elif "core" in workflows_path.parts:
                    module_prefix = "core.workflows"
                else:
                    module_prefix = "workflows"
                workflows.extend(self._scan_workflows(workflows_path, module_prefix))

        self.logger.info(f"Discovered {len(workflows)} workflows")

        # Use proper deduplication instead of simple set()
        deduplicated_workflows = self._deduplicate_callables(workflows)
        self.logger.info(f"After deduplication: {len(deduplicated_workflows)} workflows")

        return deduplicated_workflows

    def _scan_directory(
        self,
        path: Path,
        module_prefix: str,
        discovery_predicate: Callable[[Any], bool],
        member_predicate: Callable[[Any], bool],
    ) -> list[Any]:
        """Recursively scan for decorated objects in a given path."""
        items = []
        for module_info in pkgutil.walk_packages([str(path)], prefix=f"{module_prefix}."):
            if module_info.name.split(".")[-1].startswith("__"):
                continue

            try:
                module_name = module_info.name
                module = importlib.import_module(module_name)

                for _, obj in inspect.getmembers(module, member_predicate):
                    if discovery_predicate(obj):
                        items.append(obj)

            except Exception:
                self.logger.exception(f"Failed to import module {module_name}")

        return items

    def _scan_workflows(self, workflows_path: Path, module_prefix: str) -> list[Any]:
        """Scan for workflow classes decorated with @workflow.defn."""
        return self._scan_directory(
            workflows_path,
            module_prefix,
            self._is_workflow_class,
            inspect.isclass,
        )

    def _scan_activities(self, activities_path: Path, module_prefix: str, dependencies: list[Any]) -> list[Any]:
        """Scan for activity functions and class-based activities decorated with @activity.defn."""
        activities = []

        # First, scan for function-based activities (existing behavior)
        function_activities = self._scan_directory(
            activities_path,
            module_prefix,
            self._is_activity_function,
            inspect.isfunction,
        )
        activities.extend(function_activities)

        # Then, scan for class-based activities
        class_activities = self._scan_directory(
            activities_path,
            module_prefix,
            self._has_activity_methods,
            inspect.isclass,
        )

        # Process class-based activities with dependency injection
        for activity_class in class_activities:
            try:
                activity_methods = self._instantiate_activity_class(activity_class, dependencies)
                activities.extend(activity_methods)
            except Exception:
                self.logger.exception(f"Failed to instantiate activity class {activity_class.__name__}")

        return activities

    def _has_activity_methods(self, cls: Any) -> bool:  # noqa: ANN401
        """Check if a class has methods decorated with @activity.defn."""
        try:
            return any(self._is_activity_function(method) for _, method in inspect.getmembers(cls, inspect.isfunction))
        except Exception:  # noqa: BLE001
            return False

    def _instantiate_activity_class(self, activity_class: Any, dependencies: list[Any]) -> list[Any]:  # noqa: ANN401
        """Instantiate an activity class with dependency injection and return its activity methods."""
        # Get the constructor signature
        try:
            constructor_signature = inspect.signature(activity_class.__init__)
        except (ValueError, TypeError):
            self.logger.warning(f"Could not get constructor signature for {activity_class.__name__}")
            return []

        # Build dependency mapping by type
        dependency_map = {}
        for dep in dependencies:
            dep_type = type(dep)
            dependency_map[dep_type] = dep

            # Also handle mock objects that have a _spec_class attribute (for testing)
            if hasattr(dep, "_spec_class"):
                dependency_map[dep._spec_class] = dep  # noqa: SLF001

        # Match constructor parameters with dependencies
        constructor_args = []
        for param_name, param in constructor_signature.parameters.items():
            if param_name == "self":
                continue

            # Get the parameter type annotation
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                self.logger.warning(
                    f"Parameter '{param_name}' in {activity_class.__name__}.__init__ has no type annotation",
                )
                continue

            # Find matching dependency by type
            matching_dependency = None
            for dep_type, dep in dependency_map.items():
                # Direct type match
                if dep_type == param_type or (not hasattr(dep, "_spec_class") and isinstance(dep, param_type)):
                    matching_dependency = dep
                    break
                # For mock objects, check if the spec matches
                if hasattr(dep, "_spec_class") and dep._spec_class == param_type:  # noqa: SLF001
                    matching_dependency = dep
                    break

            if matching_dependency is None:
                self.logger.warning(
                    f"No dependency found for parameter '{param_name}' of type {param_type} "
                    f"in {activity_class.__name__}.__init__",
                )
                return []

            constructor_args.append(matching_dependency)

        # Instantiate the class with dependencies
        try:
            instance = activity_class(*constructor_args)
        except Exception:
            self.logger.exception(f"Failed to instantiate {activity_class.__name__} with dependencies")
            return []

        # Extract activity methods from the instance
        activity_methods = []
        for _, method in inspect.getmembers(instance, inspect.ismethod):
            if self._is_activity_function(method):
                activity_methods.append(method)

        self.logger.debug(
            f"Instantiated {activity_class.__name__} with {len(constructor_args)} dependencies, "
            f"found {len(activity_methods)} activity methods",
        )

        return activity_methods

    def _is_workflow_class(self, cls: Any) -> bool:  # noqa: ANN401
        """Check if a class is decorated with @workflow.defn."""
        try:
            # Use getattr to avoid name mangling issues with double underscore
            return getattr(cls, "__temporal_workflow_definition", None) is not None
        except Exception:  # noqa: BLE001
            return False

    def _is_activity_function(self, func: Any) -> bool:  # noqa: ANN401
        """Check if a function is decorated with @activity.defn."""
        try:
            # Use getattr to avoid name mangling issues with double underscore
            return getattr(func, "__temporal_activity_definition", None) is not None
        except Exception:  # noqa: BLE001
            return False

    def _get_workflow_name(self, workflow_cls: Any) -> str:  # noqa: ANN401
        """Get the decorator-defined name for a workflow class."""
        try:
            # Use getattr to avoid name mangling issues with double underscore
            defn = getattr(workflow_cls, "__temporal_workflow_definition", None)
            if defn and hasattr(defn, "name") and defn.name:
                return defn.name
        except Exception:  # noqa: BLE001, S110
            pass
        # Fallback to class name if decorator name is not available
        return getattr(workflow_cls, "__name__", str(workflow_cls))

    def _get_activity_name(self, activity_func: Any) -> str:  # noqa: ANN401
        """Get the decorator-defined name for an activity function."""
        try:
            # Use getattr to avoid name mangling issues with double underscore
            defn = getattr(activity_func, "__temporal_activity_definition", None)
            if defn and hasattr(defn, "name") and defn.name:
                return defn.name
        except Exception:  # noqa: BLE001, S110
            pass
        # Fallback to function name if decorator name is not available
        return getattr(activity_func, "__name__", str(activity_func))
