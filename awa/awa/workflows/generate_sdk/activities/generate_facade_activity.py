"""Activity for generating facade pattern files for Python SDK."""

import ast
import re
from pathlib import Path

from temporalio import activity

from awa.workflows.generate_sdk import constants as generate_sdk_constants


class FacadeGenerator:
    """Generates facade pattern for the AWA SDK."""

    def __init__(self, package_root: Path) -> None:
        """Initialize the facade generator.

        Args:
            package_root: Root path of the SDK package (e.g., sdk_dist/python/awa/client)

        """
        self.package_root = package_root
        # Store as (display_name, module, actual_name, function_type)
        self.discoveries: dict[str, list[tuple[str, str, str, str]]] = {
            "workflow": [],
            "activity": [],
            "general": [],
            "models": [],
            "constants": [],
        }
        # Store function signatures for stub generation
        # Maps function_name -> (params, return_type)
        self.function_signatures: dict[str, tuple[str, str]] = {}

    def discover(self) -> None:
        """Discover all SDK components."""
        # Discover utilities
        utils_path = self.package_root / "utils"
        if utils_path.exists():
            for util_type in ["workflow", "activity", "general"]:
                type_path = utils_path / util_type
                if type_path.exists():
                    self._discover_module_functions(type_path, util_type, f"awa.client.utils.{util_type}")

        # Discover models
        models_path = self.package_root / "models"
        if models_path.exists():
            self._discover_models(models_path, "awa.client.models")

        # Discover constants
        constants_path = self.package_root / "constants.py"
        if constants_path.exists():
            self._discover_constants(constants_path)

    def _collect_external_types(self, type_str: str) -> dict[str, str]:
        """Collect external types (not in our models) and their import sources.

        Args:
            type_str: The type string to process

        Returns:
            Dict mapping type names to their import sources

        """
        external_types = {}

        # Known external types and their import sources
        external_type_mappings = {
            "RetryPolicy": "temporalio.common",
        }

        # Find all potential type references in the string
        pattern = r"\b([A-Z][a-zA-Z0-9_]*)\b"
        for match in re.finditer(pattern, type_str):
            potential_type = match.group(1)
            if potential_type in external_type_mappings:
                external_types[potential_type] = external_type_mappings[potential_type]

        return external_types

    def _extract_function_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, str]:
        """Extract function signature from AST node.

        Args:
            node: The function definition AST node

        Returns:
            Tuple of (parameters_string, return_type_string)

        """
        params = []

        for arg in node.args.args:
            param_name = arg.arg
            if param_name == "self":
                continue

            # Get type annotation if available
            if arg.annotation:
                param_type = ast.unparse(arg.annotation)
                # Handle union types properly for stub files
                param_type = param_type.replace("'", "")  # Remove quotes from type strings
            else:
                param_type = "Any"

            # Check for default value
            default_idx = len(node.args.args) - len(node.args.defaults)
            arg_idx = node.args.args.index(arg)

            if arg_idx >= default_idx and node.args.defaults:
                default_value_idx = arg_idx - default_idx
                if default_value_idx < len(node.args.defaults):
                    default = node.args.defaults[default_value_idx]
                    if isinstance(default, ast.Constant):
                        if default.value is None:
                            default_str = " = None"
                        elif isinstance(default.value, str):
                            default_str = f' = "{default.value}"'
                        else:
                            default_str = f" = {default.value}"
                    else:
                        default_str = " = ..."
                    params.append(f"{param_name}: {param_type}{default_str}")
                else:
                    params.append(f"{param_name}: {param_type}")
            else:
                params.append(f"{param_name}: {param_type}")

        # Handle *args
        if node.args.vararg:
            vararg_type = ast.unparse(node.args.vararg.annotation) if node.args.vararg.annotation else "Any"
            params.append(f"*{node.args.vararg.arg}: {vararg_type}")

        # Handle **kwargs
        if node.args.kwarg:
            kwarg_type = ast.unparse(node.args.kwarg.annotation) if node.args.kwarg.annotation else "Any"
            params.append(f"**{node.args.kwarg.arg}: {kwarg_type}")

        params_str = ", ".join(params) if params else ""

        # Get return type
        if node.returns:
            return_type = ast.unparse(node.returns)
            # Remove quotes from type strings
            return_type = return_type.replace("'", "")
        else:
            return_type = "Any"

        return params_str, return_type

    def _discover_module_functions(self, path: Path, category: str, import_path: str) -> None:
        """Discover functions in utility module directories.

        Args:
            path: Directory path containing utility files
            category: Category of utilities ('workflow', 'activity', 'general')
            import_path: Import path prefix for the module

        """
        for py_file in path.glob("*.py"):
            if py_file.name.startswith("_") or py_file.name == "__init__.py":
                continue

            module_name = py_file.stem
            full_import = f"{import_path}.{module_name}"

            try:
                with Path.open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    # Look for both async and regular functions
                    if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                        # Skip private functions
                        if node.name.startswith("_"):
                            continue

                        # For workflow/activity categories, prefer functions that match the module name
                        # For general category, include all public functions
                        if category == "general" or node.name == module_name:
                            # Strip suffixes for cleaner API
                            display_name = module_name
                            if module_name.endswith("_activity"):
                                display_name = module_name[:-9]  # Remove '_activity'
                            elif module_name.endswith("_workflow"):
                                display_name = module_name[:-9]  # Remove '_workflow'

                            function_type = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
                            self.discoveries[category].append(
                                (display_name, full_import, node.name, function_type),
                            )

                            # Store function signature for stub generation
                            params_str, return_type = self._extract_function_signature(node)
                            self.function_signatures[f"{category}.{display_name}"] = (params_str, return_type)

                            # For workflow/activity, stop after finding the main function
                            # For general, continue to find all public functions
                            if category != "general":
                                break
            except Exception as e:  # noqa: BLE001
                activity.logger.warning(f"Failed to parse {py_file}: {e}")

    def _discover_models(self, path: Path, import_prefix: str) -> None:
        """Discover model classes.

        Args:
            path: Models directory path
            import_prefix: Import path prefix for models

        """
        for py_file in path.rglob("*.py"):
            if py_file.name.startswith("_") or py_file.name == "__init__.py":
                continue

            # Build import path
            relative_path = py_file.relative_to(path).with_suffix("")
            module_path = str(relative_path).replace("/", ".")
            full_import = f"{import_prefix}.{module_path}"

            try:
                with Path.open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    # Only export public classes
                    if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                        self.discoveries["models"].append(
                            (node.name, full_import, node.name, "class"),
                        )
            except Exception as e:  # noqa: BLE001
                activity.logger.warning(f"Failed to parse {py_file}: {e}")

    def _discover_constants(self, path: Path) -> None:
        """Discover constants from constants.py.

        Args:
            path: Path to constants.py file

        """
        try:
            with Path.open(path) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        # Only export uppercase constants (convention)
                        if isinstance(target, ast.Name) and (
                            target.id.isupper()
                            or target.id.startswith("WORKFLOW_")
                            or target.id.startswith("ACTIVITY_")
                        ):
                            self.discoveries["constants"].append(
                                (target.id, "awa.client.constants", target.id, "constant"),
                            )
        except Exception as e:  # noqa: BLE001
            activity.logger.warning(f"Failed to parse constants: {e}")

    def _generate_namespace_module(self, namespace_type: str, prefix: str) -> str:  # noqa: ARG002
        """Generate a namespace module file.

        Args:
            namespace_type: Type of namespace (e.g., 'workflow', 'activity', 'general')
            prefix: Module prefix (e.g., 'awa_activity', 'awa_workflow')

        Returns:
            Content for the namespace module file

        """
        lines = [
            f'"""AWA {namespace_type.capitalize()} utilities namespace.',
            "",
            "This file is automatically generated. Do not edit manually.",
            '"""',
            "",
        ]

        # Add imports - use relative imports within the SDK
        imports = []
        exports = []

        for display_name, module, actual_name, _ in sorted(
            self.discoveries.get(namespace_type, []),
            key=lambda x: x[0],
        ):
            # Convert absolute import to relative import
            # awa.client.utils.activity -> .utils.activity
            relative_module = module.replace("awa.client.", ".")
            imports.append(f"from {relative_module} import {actual_name} as {display_name}")
            exports.append(display_name)

        if imports:
            lines.extend(imports)
            lines.append("")
            lines.append("__all__ = [")
            for i, export in enumerate(exports):
                comma = "," if i < len(exports) - 1 else ""
                lines.append(f'    "{export}"{comma}')
            lines.append("]")
        else:
            lines.append("__all__ = []")

        return "\n".join(lines) + "\n"

    def _extract_model_types_from_signature(self, signature: str) -> set[str]:
        """Extract model type names from a function signature.

        Args:
            signature: The function signature string containing types

        Returns:
            Set of model type names found in the signature

        """
        # Get all discovered model names for reference
        all_models = {name for name, _, _, _ in self.discoveries.get("models", [])}

        found_models = set()

        # Use regex to find potential type references
        # This pattern matches word boundaries followed by capitalized names
        # which is the convention for class/type names in Python
        pattern = r"\b([A-Z][a-zA-Z0-9_]*)\b"

        for match in re.finditer(pattern, signature):
            potential_type = match.group(1)
            # Check if this is one of our discovered models
            if potential_type in all_models:
                found_models.add(potential_type)

        return found_models

    def _generate_namespace_stub(self, namespace_type: str, prefix: str) -> str:  # noqa: ARG002
        """Generate a namespace module stub file.

        Args:
            namespace_type: Type of namespace (e.g., 'workflow', 'activity', 'general')
            prefix: Module prefix (e.g., 'awa_activity', 'awa_workflow')

        Returns:
            Content for the namespace module stub file

        """
        lines = [
            f'"""Type stubs for AWA {namespace_type.capitalize()} utilities.',
            "",
            "This file is automatically generated. Do not edit manually.",
            '"""',
            "",
            "from typing import Any, Optional, Dict, List, Union, Callable",
            "from pathlib import Path",
            "",
        ]

        # Collect specific model types and external types used in function signatures
        used_models = set()
        external_imports = {}  # Maps module -> set of types to import

        for display_name, _, _, _ in self.discoveries.get(namespace_type, []):
            signature_key = f"{namespace_type}.{display_name}"
            if signature_key in self.function_signatures:
                params_str, return_type = self.function_signatures[signature_key]
                # Extract model names from both parameters and return type
                used_models.update(self._extract_model_types_from_signature(params_str))
                used_models.update(self._extract_model_types_from_signature(return_type))

                # Collect external types
                for external_type, module in self._collect_external_types(params_str).items():
                    if module not in external_imports:
                        external_imports[module] = set()
                    external_imports[module].add(external_type)

                for external_type, module in self._collect_external_types(return_type).items():
                    if module not in external_imports:
                        external_imports[module] = set()
                    external_imports[module].add(external_type)

        # Add external imports
        if external_imports:
            lines.append("# Import external types")
            for module, types in sorted(external_imports.items()):
                if len(types) == 1:
                    lines.append(f"from {module} import {', '.join(sorted(types))}")
                else:
                    lines.append(f"from {module} import {', '.join(sorted(types))}")
            lines.append("")

        # Import only the specific models needed for type hints
        if used_models:
            lines.append("# Import only models used in function signatures")
            lines.append("from .models import (")
            lines.extend(f"    {model}," for model in sorted(used_models))
            lines.append(")")
        lines.append("")

        # Add function signatures based on the actual functions
        for display_name, _module, _actual_name, func_type in sorted(
            self.discoveries.get(namespace_type, []),
            key=lambda x: x[0],
        ):
            # Get the stored signature
            signature_key = f"{namespace_type}.{display_name}"
            if signature_key in self.function_signatures:
                params_str, return_type = self.function_signatures[signature_key]
            else:
                # Fallback to generic signature
                params_str = "*args: Any, **kwargs: Any"
                return_type = "Any"

            if func_type == "async_function":
                lines.append(f"async def {display_name}({params_str}) -> {return_type}: ...")
            else:
                lines.append(f"def {display_name}({params_str}) -> {return_type}: ...")

        return "\n".join(lines) + "\n"

    def _generate_constants_namespace(self, output_dir: Path) -> None:
        """Generate the constants namespace module.

        Args:
            output_dir: SDK client directory

        """
        # Generate awa_constants.py
        lines = [
            '"""AWA Constants namespace.',
            "",
            "This file is automatically generated. Do not edit manually.",
            '"""',
            "",
            "from .constants import (",
        ]

        constants = [name for name, _, _, _ in sorted(self.discoveries.get("constants", []))]
        for i, const_name in enumerate(constants):
            comma = "," if i < len(constants) - 1 else ""
            lines.append(f"    {const_name}{comma}")

        lines.append(")")
        lines.append("")
        lines.append("__all__ = [")
        for i, const_name in enumerate(constants):
            comma = "," if i < len(constants) - 1 else ""
            lines.append(f'    "{const_name}"{comma}')
        lines.append("]")

        content = "\n".join(lines) + "\n"
        file_path = output_dir / "awa_constants.py"
        with Path.open(file_path, "w") as f:
            f.write(content)
        activity.logger.info(f"Generated: {file_path}")

        # Generate awa_constants.pyi stub
        stub_lines = [
            '"""Type stubs for AWA Constants.',
            "",
            "This file is automatically generated. Do not edit manually.",
            '"""',
            "",
        ]

        for const_name, _, _, _ in sorted(self.discoveries.get("constants", [])):
            # Constants are typically strings or numbers
            stub_lines.append(f"{const_name}: str")

        stub_content = "\n".join(stub_lines) + "\n"
        stub_path = output_dir / "awa_constants.pyi"
        with Path.open(stub_path, "w") as f:
            f.write(stub_content)
        activity.logger.info(f"Generated: {stub_path}")

    def _generate_namespace_modules(self, output_dir: Path) -> None:
        """Generate all namespace module files.

        Args:
            output_dir: SDK client directory

        """
        # Generate namespace modules for activity, workflow, and general
        for namespace_type, prefix in [
            ("activity", "awa_activity"),
            ("workflow", "awa_workflow"),
            ("general", "awa_general"),
        ]:
            # Generate .py file
            content = self._generate_namespace_module(namespace_type, prefix)
            file_path = output_dir / f"{prefix}.py"
            with Path.open(file_path, "w") as f:
                f.write(content)
            activity.logger.info(f"Generated: {file_path}")

            # Generate .pyi stub
            stub_content = self._generate_namespace_stub(namespace_type, prefix)
            stub_path = output_dir / f"{prefix}.pyi"
            with Path.open(stub_path, "w") as f:
                f.write(stub_content)
            activity.logger.info(f"Generated: {stub_path}")

        # Generate constants namespace
        self._generate_constants_namespace(output_dir)

    def _generate_facade_implementation(self) -> str:  # noqa: PLR0915
        """Generate the facade implementation file content.

        Returns:
            The content of _facade.py

        """
        lines = [
            '"""Auto-generated facade for AWA SDK with direct imports.',
            "",
            "This file is automatically generated. Do not edit manually.",
            '"""',
            "",
            "from __future__ import annotations",
            "",
            "from typing import ClassVar",
            "",
        ]

        # Add all direct imports at the top
        lines.append("# Direct imports for all SDK components")
        imports_added = set()

        # Sort imports by module path for consistency
        all_imports = []
        for items in self.discoveries.values():
            for _, module, actual_name, _ in items:
                import_key = f"{module}.{actual_name}"
                if import_key not in imports_added:
                    all_imports.append((module, actual_name))
                    imports_added.add(import_key)

        # Group imports by category for better organization
        activity_imports = []
        workflow_imports = []
        model_imports = []
        general_imports = []
        constant_imports = []

        for module, actual_name in sorted(all_imports):
            import_line = f"from {module} import {actual_name}"
            if "utils.activity" in module:
                activity_imports.append(import_line)
            elif "utils.workflow" in module:
                workflow_imports.append(import_line)
            elif "utils.general" in module:
                general_imports.append(import_line)
            elif "models" in module:
                model_imports.append(import_line)
            elif "constants" in module:
                constant_imports.append(import_line)

        # Add imports in organized groups
        if activity_imports:
            lines.append("")
            lines.append("# Activity imports")
            lines.extend(activity_imports)

        if workflow_imports:
            lines.append("")
            lines.append("# Workflow imports")
            lines.extend(workflow_imports)

        if general_imports:
            lines.append("")
            lines.append("# General utility imports")
            lines.extend(general_imports)

        if model_imports:
            lines.append("")
            lines.append("# Model imports")
            lines.extend(model_imports)

        if constant_imports:
            lines.append("")
            lines.append("# Constant imports")
            lines.extend(constant_imports)

        lines.extend(
            [
                "",
                "class AWA:",
                '    """Facade class for AWA SDK providing convenient access to all utilities and models.',
                "    ",
                "    Usage:",
                "        from awa.client import awa",
                "        ",
                "        # Access workflow utilities directly",
                "        await awa.execute_agent(config)",
                "        ",
                "        # Access activity utilities directly",
                "        await awa.read_file(path)",
                "        ",
                "        # Access general utilities directly",
                "        paths = awa.get_workflow_paths()",
                "        ",
                "        # Access models directly",
                "        config = awa.AgentConfiguration(...)",
                "        ",
                "        # Access constants directly",
                "        timeout = awa.AGENT_TIMEOUT_SECONDS",
                '    """',
                "",
                "    # Direct class attributes for all utilities - no namespaces!",
                "    # This provides the best intellisense support",
                "",
            ],
        )

        # Add all items directly as class attributes
        # Activities
        if self.discoveries.get("activity"):
            lines.append("    # Activity utilities")
            for display_name, _module, actual_name, _item_type in sorted(
                self.discoveries.get("activity", []),
                key=lambda x: x[0],
            ):
                lines.append(f"    {display_name} = {actual_name}")
            lines.append("")

        # Workflows
        if self.discoveries.get("workflow"):
            lines.append("    # Workflow utilities")
            for display_name, _module, actual_name, _item_type in sorted(
                self.discoveries.get("workflow", []),
                key=lambda x: x[0],
            ):
                lines.append(f"    {display_name} = {actual_name}")
            lines.append("")

        # General utilities
        if self.discoveries.get("general"):
            lines.append("    # General utilities")
            for display_name, _module, actual_name, _item_type in sorted(
                self.discoveries.get("general", []),
                key=lambda x: x[0],
            ):
                lines.append(f"    {display_name} = {actual_name}")
            lines.append("")

        # Models
        if self.discoveries.get("models"):
            lines.append("    # Models")
            for display_name, _module, actual_name, _item_type in sorted(
                self.discoveries.get("models", []),
                key=lambda x: x[0],
            ):
                lines.append(f"    {display_name} = {actual_name}")
            lines.append("")

        # Constants
        if self.discoveries.get("constants"):
            lines.append("    # Constants")
            for display_name, _module, actual_name, _item_type in sorted(
                self.discoveries.get("constants", []),
                key=lambda x: x[0],
            ):
                lines.append(f"    {display_name} = {actual_name}")
            lines.append("")

        # Add singleton instance with proper naming to avoid shadowing
        lines.extend(
            [
                "",
                "# Create singleton instance",
                "awa = AWA()",
                "",
            ],
        )

        return "\n".join(lines)

    def _generate_facade_stub(self) -> str:
        """Generate the facade stub file content.

        Returns:
            The content of _facade.pyi

        """
        lines = [
            '"""Type stubs for AWA SDK facade.',
            "",
            "This file is automatically generated. Do not edit manually.",
            '"""',
            "",
            "from __future__ import annotations",
            "",
            "from typing import Any, Callable",
            "",
        ]

        # Import all discovered items for type hints
        imports_added = set()
        for items in self.discoveries.values():
            for _, module, actual_name, _ in items:
                import_key = f"{module}.{actual_name}"
                if import_key not in imports_added:
                    lines.append(f"from {module} import {actual_name}")
                    imports_added.add(import_key)

        lines.extend(
            [
                "",
                "class AWA:",
                '    """Facade class for AWA SDK providing convenient access to all utilities and models."""',
                "",
            ],
        )

        # Add all items directly as type annotations
        # Activities
        if self.discoveries.get("activity"):
            lines.append("    # Activity utilities")
            for display_name, _, actual_name, _ in sorted(
                self.discoveries.get("activity", []),
                key=lambda x: x[0],
            ):
                lines.append(f"    {display_name}: {actual_name}")
            lines.append("")

        # Workflows
        if self.discoveries.get("workflow"):
            lines.append("    # Workflow utilities")
            for display_name, _, actual_name, _ in sorted(
                self.discoveries.get("workflow", []),
                key=lambda x: x[0],
            ):
                lines.append(f"    {display_name}: {actual_name}")
            lines.append("")

        # General utilities
        if self.discoveries.get("general"):
            lines.append("    # General utilities")
            for display_name, _, actual_name, _ in sorted(
                self.discoveries.get("general", []),
                key=lambda x: x[0],
            ):
                lines.append(f"    {display_name}: {actual_name}")
            lines.append("")

        # Models
        if self.discoveries.get("models"):
            lines.append("    # Models")
            for display_name, _, actual_name, item_type in sorted(
                self.discoveries.get("models", []),
                key=lambda x: x[0],
            ):
                if item_type == "class":
                    lines.append(f"    {display_name}: type[{actual_name}]")
            lines.append("")

        # Constants
        if self.discoveries.get("constants"):
            lines.append("    # Constants")
            for display_name, _, _actual_name, _ in sorted(
                self.discoveries.get("constants", []),
                key=lambda x: x[0],
            ):
                # Constants are strings, so use str as the type
                lines.append(f"    {display_name}: str")
            lines.append("")

        # Add singleton instance with proper naming to avoid shadowing
        lines.extend(
            [
                "",
                "# Singleton instance",
                "awa: AWA",
                "",
            ],
        )

        return "\n".join(lines)

    def _generate_models_aggregator(self, output_dir: Path) -> None:
        """Generate models/__init__.py with all model re-exports.

        Args:
            output_dir: SDK client directory (e.g., sdk_dist/python/awa/client)

        """
        models_dir = output_dir / "models"
        if not models_dir.exists():
            activity.logger.warning("Models directory does not exist, skipping models aggregator generation")
            return

        models_init_path = models_dir / "__init__.py"

        # Generate the aggregator content
        lines = [
            '"""Model classes and types for AWA SDK.',
            "",
            "This module provides easy access to all model classes used in the AWA SDK.",
            "Import model types from this module for use in type annotations and instantiation.",
            "",
            "Example:",
            "    from awa.client.models import WorkflowPaths, CommandResult, AgentConfiguration",
            '"""',
            "",
            "# Core models",
        ]

        # Collect all __all__ entries
        all_exports = []

        # Sort models by category for better organization
        core_models = []
        agent_models = []
        exception_models = []

        for _, module, actual_name, item_type in sorted(
            self.discoveries.get("models", []),
            key=lambda x: (x[1], x[0]),  # Sort by module, then name
        ):
            if item_type == "class":
                import_line = f"from {module} import {actual_name}"

                # Categorize imports
                if "agent_modes" in module:
                    agent_models.append((import_line, actual_name))
                elif "exceptions" in module:
                    exception_models.append((import_line, actual_name))
                else:
                    core_models.append((import_line, actual_name))

                all_exports.append(actual_name)

        # Add core model imports
        if core_models:
            for import_line, _ in core_models:
                lines.append(import_line)
            lines.append("")

        # Add agent model imports
        if agent_models:
            lines.append("# Agent models")
            for import_line, _ in agent_models:
                lines.append(import_line)
            lines.append("")

        # Add exception imports
        if exception_models:
            lines.append("# Exception models")
            for import_line, _ in exception_models:
                lines.append(import_line)
            lines.append("")

        # Add __all__ export list
        if all_exports:
            lines.append("__all__ = [")
            for i, export_name in enumerate(sorted(all_exports)):
                comma = "," if i < len(all_exports) - 1 else ""
                lines.append(f'    "{export_name}"{comma}')
            lines.append("]")
        else:
            lines.append("__all__ = []")

        # Write the aggregator file
        aggregator_content = "\n".join(lines) + "\n"
        with Path.open(models_init_path, "w") as f:
            f.write(aggregator_content)

        activity.logger.info(f"Generated models aggregator: {models_init_path}")

    def generate(self, output_dir: Path) -> None:
        """Generate namespace modules and models aggregator.

        Args:
            output_dir: Directory to write the files to

        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate namespace modules (awa_activity, awa_workflow, etc.)
        self._generate_namespace_modules(output_dir)

        # Generate models aggregator __init__.py
        self._generate_models_aggregator(output_dir)

        # No longer generating the old facade - simplified!

        # Update __init__.py to export namespace modules
        init_path = output_dir / "__init__.py"

        # Generate clean __init__.py with only namespace modules
        init_lines = [
            '"""AWA Client SDK - Clean namespace-based API."""',
            "",
            "# Import namespace modules",
            "from . import (",
            "    awa_activity,",
            "    awa_workflow,",
            "    awa_general,",
            "    awa_constants,",
            "    models,",
            ")",
            "",
            "# Define what's exported",
            "__all__ = [",
            '    "awa_activity",',
            '    "awa_workflow",',
            '    "awa_general",',
            '    "awa_constants",',
            '    "models",',
            "]",
            "",
        ]

        # Write the __init__.py file with proper newlines
        init_content = "\n".join(init_lines)
        with Path.open(init_path, "w") as f:
            f.write(init_content)
        activity.logger.info(f"Updated: {init_path}")


@activity.defn(name=generate_sdk_constants.ACTIVITY_GENERATE_FACADE)
async def generate_facade_activity(sdk_path: str) -> None:
    """Generate facade pattern files for Python SDK.

    Args:
        sdk_path: Path to the Python SDK directory (e.g., sdk_dist/python)

    """
    activity.logger.info(f"Generating facade for Python SDK at: {sdk_path}")

    # Get paths
    sdk_root = Path(sdk_path) / "awa" / "client"

    if not sdk_root.exists():
        raise FileNotFoundError(f"SDK root directory not found: {sdk_root}")

    # Create and run the facade generator
    generator = FacadeGenerator(sdk_root)
    generator.discover()

    # Log discovery summary
    activity.logger.info("Discovered components:")
    for category, items in generator.discoveries.items():
        if items:
            activity.logger.info(f"  {category}: {len(items)} items")

    # Generate the facade files
    generator.generate(sdk_root)

    activity.logger.info("Facade generation completed successfully")
