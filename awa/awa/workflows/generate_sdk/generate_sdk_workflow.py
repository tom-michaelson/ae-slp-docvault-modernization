"""Enhanced Generate SDK workflow with granular hash tracking and improved utility generation."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from temporalio import workflow

from awa.core import constants as core_constants
from awa.core.utils.cache_utils import CacheUtils
from awa.core.utils.concurrency_utils import ConcurrencyUtils
from awa.sdk.models.command_result import CommandInput, CommandResult
from awa.sdk.utils.activity import (
    delete_directory_activity,
    read_directory_activity,
    read_file_activity,
    run_command_activity,
    write_file_activity,
)
from awa.sdk.utils.general import get_workflow_paths_direct
from awa.workflows.generate_sdk import constants as generate_sdk_constants
from awa.workflows.generate_sdk.generate_sdk_for_language_workflow import GenerateSdkForLanguageInput
from awa.workflows.generate_sdk.models.generate_sdk_input import GenerateSdkInput
from awa.workflows.generate_sdk.models.generate_sdk_schemas_input import GenerateSdkSchemasInput
from awa.workflows.generate_sdk.models.sdk_config import SdkConfig, SdkLanguageConfig

if TYPE_CHECKING:
    from collections.abc import Callable

    from awa.sdk.models.workflow_paths import WorkflowPaths


@workflow.defn(name=generate_sdk_constants.WORKFLOW_GENERATE_SDK)
class GenerateSdkWorkflow:
    """SDK generation workflow with granular change tracking and automatic versioning.

    This workflow orchestrates the generation of SDK code across multiple languages from
    Python source models and utility functions. It includes:

    - Automatic detection of changed components (models, constants, utilities)
    - Parallel processing of multiple language targets
    - Semantic versioning with automatic patch version bumping
    - Test execution and automatic test fixing using AI agents
    - Granular hash-based change tracking for efficient regeneration

    The workflow ensures that only changed components are regenerated, making the
    SDK generation process efficient and maintainable.
    """

    language_max_concurrency = 3

    def __init__(self) -> None:
        """Initialize the workflow."""
        self.models_path = "awa/sdk/models"

    @workflow.run
    async def run(self, workflow_input: GenerateSdkInput | None = None) -> list[str]:
        """Generate SDK models for specified languages with granular change tracking.

        Args:
            workflow_input: Configuration for SDK generation including languages and output paths

        Returns:
            List of generated SDK file paths

        """
        try:
            all_generated_files: list[str] = []

            # 1. Load SDK configuration
            sdk_config_dict: dict[str, Any] = await workflow.execute_activity(
                generate_sdk_constants.ACTIVITY_GET_SDK_CONFIG,
                arg=str(workflow_input.config_path) if workflow_input and workflow_input.config_path else None,
                task_queue=core_constants.TASK_QUEUE,
                start_to_close_timeout=timedelta(seconds=core_constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )
            sdk_config: SdkConfig = SdkConfig(**sdk_config_dict)
            workflow_paths: WorkflowPaths = self._get_workflow_paths()
            enabled_languages_plus_python = [
                language for language in sdk_config.languages if language.enabled or language.name == "python"
            ]

            # 2. Check for changes using granular hash tracking (unless force=True or bump=True)
            changed_components: dict[str, str] = {}
            if not (workflow_input and workflow_input.force):
                workflow.logger.info("Checking for SDK component changes using granular tracking...")

                # Get changed components
                changed_components = await workflow.execute_activity(
                    activity=generate_sdk_constants.ACTIVITY_GET_CHANGED_COMPONENTS,
                    start_to_close_timeout=timedelta(seconds=core_constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
                )

                if not changed_components:
                    # If bump flag is set, we only bump the version without regenerating SDK
                    if workflow_input and workflow_input.bump:
                        workflow.logger.info(
                            "No SDK components have changed, but bump flag is set - bumping version only",
                        )
                        # Just bump the version without regeneration
                        sdk_version = await self._determine_sdk_version(workflow_paths, bump=True)
                        workflow.logger.info(f"Bumped SDK version to: {sdk_version}")

                        # Update version file with current hash (no changes)
                        await self._update_version_file_if_changed(workflow_paths, sdk_version)

                        # Return empty list since we didn't generate anything
                        return []
                    workflow.logger.info("No SDK components have changed, skipping regeneration")
                    return []

                workflow.logger.info(f"Found {len(changed_components)} changed components:")
                for component_path in changed_components:
                    workflow.logger.info(f"  - {component_path}")
            else:
                workflow.logger.info("Force flag set, regenerating all SDKs")
                # Get all component hashes for storage after generation
                changed_components = await workflow.execute_activity(
                    activity=generate_sdk_constants.ACTIVITY_CALCULATE_ALL_COMPONENT_HASHES,
                    start_to_close_timeout=timedelta(seconds=core_constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
                )

            # 3. Prepare Python source data
            python_constants = await read_file_activity(
                str(Path(workflow_paths.project_root) / "awa" / "sdk" / "constants.py"),
            )

            python_models_directory_results = await read_directory_activity(
                str(Path(workflow_paths.project_root) / "awa" / "sdk" / "models"),
            )
            python_models = json.dumps(
                {result.file: result.content for result in python_models_directory_results},
                indent=2,
            )

            # 4. Generate JSON schemas from original Python models
            json_schemas_path = str(Path(sdk_config.output_path) / "json_schemas")

            # Clean up existing JSON schemas before regeneration
            workflow.logger.info("Cleaning up existing JSON schemas")
            await delete_directory_activity(json_schemas_path)

            await workflow.execute_activity(
                activity=generate_sdk_constants.ACTIVITY_GENERATE_SCHEMAS,
                arg=GenerateSdkSchemasInput(models_path=self.models_path, output_path=json_schemas_path),
                start_to_close_timeout=timedelta(seconds=120),
            )

            # 5. Discover utility functions from individual files
            utility_functions = await self._discover_utility_functions(workflow_paths)

            # 6. Determine SDK version before generation
            # Pass bump flag from input (it will have effect when hash matches)
            should_bump = workflow_input and workflow_input.bump
            sdk_version = await self._determine_sdk_version(workflow_paths, bump=should_bump)
            workflow.logger.info(f"SDK version for this generation: {sdk_version}")

            # Process each language using child workflows in parallel
            language_processing_tasks = []
            for language in enabled_languages_plus_python:

                def create_language_processor(lang: SdkLanguageConfig) -> Callable:
                    async def process_language_closure() -> None:
                        language_input = GenerateSdkForLanguageInput(
                            language=lang,
                            workflow_paths=workflow_paths,
                            sdk_config=sdk_config,
                            json_schemas_path=json_schemas_path,
                            python_constants=python_constants,
                            python_models=python_models,
                            utility_functions=utility_functions,
                            changed_components=changed_components,
                            sdk_version=sdk_version,
                        )
                        return await workflow.execute_child_workflow(
                            workflow=generate_sdk_constants.WORKFLOW_GENERATE_SDK_FOR_LANGUAGE,
                            arg=language_input,
                            id=f"GenerateSdkForLanguage-{lang.name}-{workflow.info().workflow_id}",
                        )

                    return process_language_closure

                language_processing_tasks.append(create_language_processor(language))

            await ConcurrencyUtils.run_with_controlled_concurrency(
                coroutine_funcs=language_processing_tasks,
                max_concurrency=self.language_max_concurrency,
            )

            # 7. Build/package SDKs via external scripts (independently runnable)
            await self._package_sdks(workflow_paths, sdk_config, sdk_version)

            # 8. Store updated hashes after successful generation
            await workflow.execute_activity(
                activity=generate_sdk_constants.ACTIVITY_STORE_COMPONENT_HASHES,
                arg=changed_components,
                start_to_close_timeout=timedelta(seconds=core_constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )
            workflow.logger.info("Stored updated component hashes")

            # 9. Update version file with new hash
            await self._update_version_file_if_changed(workflow_paths, sdk_version)

        except Exception:
            workflow.logger.exception("Unhandled exception")
            raise

        return all_generated_files

    async def _package_sdks(self, workflow_paths: WorkflowPaths, sdk_config: SdkConfig, sdk_version: str) -> None:
        """Invoke packaging scripts for each enabled language in parallel."""
        project_root = str(Path(workflow_paths.project_root))

        # Get all enabled languages (including Python which should always be packaged)
        enabled_languages = [lang for lang in sdk_config.languages if lang.enabled or lang.name == "python"]

        # Create packaging tasks for languages that have packaging scripts
        packaging_tasks = []

        for language_config in enabled_languages:
            # Check if a packaging script exists for this language
            script_path = Path(project_root) / f"scripts/sdk/package_sdk_{language_config.name}.py"

            def create_packaging_task(lang_cfg: SdkLanguageConfig, script: Path) -> Callable:
                async def package_language() -> None:
                    if script.exists():
                        cmd = f"uv run {script} --version {sdk_version}"
                        result: CommandResult = await run_command_activity(
                            CommandInput(command=cmd, working_dir=project_root),
                        )
                        if not result.success:
                            raise RuntimeError(f"{lang_cfg.name.capitalize()} packaging script failed: {result.output}")
                        workflow.logger.info(f"{lang_cfg.name.capitalize()} packaging script completed successfully")
                    else:
                        workflow.logger.debug(f"No packaging script found for {lang_cfg.name} at {script}")

                return package_language

            packaging_tasks.append(create_packaging_task(language_config, script_path))

        # Execute all packaging tasks in parallel with controlled concurrency
        if packaging_tasks:
            await ConcurrencyUtils.run_with_controlled_concurrency(
                coroutine_funcs=packaging_tasks,
                max_concurrency=self.language_max_concurrency,
            )
            workflow.logger.info(f"Completed packaging for {len(packaging_tasks)} language(s)")

    async def _discover_utility_functions(self, workflow_paths: WorkflowPaths) -> dict[str, list[dict[str, str]]]:
        """Discover utility functions by reading individual files.

        Args:
            workflow_paths: Workflow paths configuration

        Returns:
            Dictionary with "workflow", "activity", and "general" keys, each containing a list
            of utility function definitions.

        """
        workflow.logger.info("Discovering utility functions from individual files")

        utils_path = Path(workflow_paths.project_root) / "awa" / "sdk" / "utils"
        utility_functions = {"workflow": [], "activity": [], "general": []}

        for util_type in ["workflow", "activity", "general"]:
            type_path = utils_path / util_type
            if type_path.exists():
                for py_file in type_path.glob("*.py"):
                    if py_file.name != "__init__.py":
                        function_name = py_file.stem
                        function_content = await read_file_activity(str(py_file))

                        # Simple extraction: assume the function name matches the file name
                        # and extract the entire file content
                        utility_functions[util_type].append(
                            {
                                "name": function_name,
                                "function_content": function_content,
                                "file_path": str(py_file.relative_to(workflow_paths.project_root)),
                            },
                        )

        workflow.logger.info(
            f"Discovered utility functions - "
            f"workflow: {len(utility_functions['workflow'])}, "
            f"activity: {len(utility_functions['activity'])}, "
            f"general: {len(utility_functions['general'])}",
        )
        return utility_functions

    def _get_workflow_paths(self) -> WorkflowPaths:
        """Get workflow paths using workflow info."""
        workflow_dir = Path(__file__).parent
        return get_workflow_paths_direct(
            workflow_dir,
            workflow.info().workflow_type,
            workflow.info().workflow_id,
        )

    async def _determine_sdk_version(self, workflow_paths: WorkflowPaths, bump: bool = False) -> str:
        """Determine SDK version by computing hash of entire original SDK and bumping version if changed.

        Args:
            workflow_paths: Workflow paths configuration
            bump: If True, bump version even if hash is unchanged

        Returns:
            The SDK version to use for this generation

        """
        workflow.logger.info("Determining SDK version")

        try:
            # Calculate hash of the entire original SDK
            sdk_root = Path(workflow_paths.project_root) / "awa" / "sdk"
            sdk_hash = await self._calculate_sdk_hash(sdk_root)
            workflow.logger.info(f"Calculated SDK hash: {sdk_hash[:8]}...")

            # Find current version file in sdk_dist/.hash/
            version_dir = Path(workflow_paths.project_root) / "sdk_dist" / ".hash"
            current_version_file = await self._find_current_version_file(version_dir)

            if current_version_file is None:
                workflow.logger.warning("No version file found, starting with initial version")
                current_version = "1.0.0"
                stored_hash = ""
            else:
                current_version = current_version_file.stem
                stored_hash = await read_file_activity(str(current_version_file), default="")
                stored_hash = stored_hash.strip()
                hash_display = stored_hash[:8] if stored_hash else "empty"
                workflow.logger.info(f"Current version: {current_version}, stored hash: {hash_display}...")

            # Compare hashes to determine if version bump is needed
            if sdk_hash != stored_hash:
                workflow.logger.info("SDK hash has changed, bumping version")
                new_version = await self._bump_patch_version(current_version)
                workflow.logger.info(f"Bumping version from {current_version} to {new_version}")
                return new_version
            if bump:
                workflow.logger.info("Bump flag set, forcing version bump despite unchanged hash")
                new_version = await self._bump_patch_version(current_version)
                workflow.logger.info(f"Bumping version from {current_version} to {new_version}")
                return new_version
            workflow.logger.info("SDK hash unchanged, using current version")
            return current_version

        except Exception:
            workflow.logger.exception("Failed to determine SDK version")
            raise

    async def _update_version_file_if_changed(self, workflow_paths: WorkflowPaths, sdk_version: str) -> None:
        """Update version file with new hash after successful generation.

        Args:
            workflow_paths: Workflow paths configuration
            sdk_version: The version that was used for generation

        """
        try:
            # Calculate current hash
            sdk_root = Path(workflow_paths.project_root) / "awa" / "sdk"
            sdk_hash = await self._calculate_sdk_hash(sdk_root)

            # Ensure version directory exists
            version_dir = Path(workflow_paths.project_root) / "sdk_dist" / ".hash"

            # Note: File deletion would need to be done via activities if needed
            # For now, we'll just create/overwrite the new version file

            # Create new version file with hash
            new_version_file = version_dir / f"{sdk_version}.version"
            await self._write_version_file(new_version_file, sdk_hash)
            workflow.logger.info(f"Updated version file: {new_version_file.name}")

        except Exception:
            workflow.logger.exception("Failed to update version file")
            raise

    async def _calculate_sdk_hash(self, sdk_root: Path) -> str:
        """Calculate hash of entire original SDK.

        Args:
            sdk_root: Path to awa/sdk directory

        Returns:
            SHA-256 hash of the entire SDK

        """
        # Collect all SDK files
        sdk_data = {}

        # Include constants.py
        constants_file = sdk_root / "constants.py"
        if constants_file.exists():
            content = await read_file_activity(str(constants_file), default="")
            sdk_data["constants.py"] = content

        # Include all model files
        models_dir = sdk_root / "models"
        if models_dir.exists():
            for py_file in models_dir.rglob("*.py"):
                if py_file.name != "__init__.py":
                    relative_path = str(py_file.relative_to(sdk_root))
                    content = await read_file_activity(str(py_file), default="")
                    sdk_data[relative_path] = content

        # Include all utils files
        utils_dir = sdk_root / "utils"
        if utils_dir.exists():
            for py_file in utils_dir.rglob("*.py"):
                if py_file.name != "__init__.py":
                    relative_path = str(py_file.relative_to(sdk_root))
                    content = await read_file_activity(str(py_file), default="")
                    sdk_data[relative_path] = content

        return CacheUtils.hash(sdk_data)

    async def _find_current_version_file(self, version_dir: Path) -> Path | None:
        """Find the current version file in the version directory.

        Args:
            version_dir: Path to sdk_dist/.hash directory

        Returns:
            Path to current version file or None if not found

        """
        # Check if directory exists and list files using activities
        try:
            dir_results = await read_directory_activity(str(version_dir))
            version_files = [version_dir / result.file for result in dir_results if result.file.endswith(".version")]
        except (OSError, FileNotFoundError, PermissionError):
            # Directory doesn't exist or error reading
            return None

        if not version_files:
            return None

        # Return the version file with highest version number
        return max(version_files, key=lambda f: self._parse_version(f.stem))

    def _parse_version(self, version_str: str) -> tuple[int, int, int]:
        """Parse version string into tuple for comparison.

        Args:
            version_str: Version string like "1.2.3"

        Returns:
            Tuple of (major, minor, patch) integers

        """
        try:
            parts = version_str.split(".")
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            # Default to 0.0.0 for invalid versions
            return (0, 0, 0)

    async def _bump_patch_version(self, current_version: str) -> str:
        """Bump the patch version.

        Args:
            current_version: Current version string like "1.2.3"

        Returns:
            New version string with patch incremented

        """
        try:
            major, minor, patch = self._parse_version(current_version)
            return f"{major}.{minor}.{patch + 1}"
        except (ValueError, IndexError):
            # If parsing fails, default to 1.0.1
            return "1.0.1"

    async def _write_version_file(self, version_file: Path, sdk_hash: str) -> None:
        """Write the new version file with the SDK hash.

        Args:
            version_file: Path to the new version file
            sdk_hash: Hash to store in the file

        """
        # Write hash to file (the activity will ensure directory exists)
        await write_file_activity(str(version_file), sdk_hash)
