"""Child workflow for processing a single language in SDK generation."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from temporalio import workflow

from awa.core import constants as core_constants
from awa.core.utils.concurrency_utils import ConcurrencyUtils
from awa.sdk import constants as sdk_constants
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum
from awa.sdk.models.build_prompt_params import BuildPromptParams
from awa.sdk.models.command_result import CommandInput, CommandResult
from awa.sdk.models.exceptions.retryable_application_error import RetryableApplicationError
from awa.sdk.models.input_params import InputParams
from awa.sdk.models.transform_params import TransformParams
from awa.sdk.models.workflow_paths import WorkflowPaths
from awa.sdk.utils.activity import (
    copy_directory_activity,
    copy_file_activity,
    is_directory_activity,
    read_file_activity,
    run_command_activity,
    write_file_activity,
)
from awa.sdk.utils.workflow import execute_agent_workflow, execute_baml_transform_workflow
from awa.workflows.generate_sdk import constants as generate_sdk_constants
from awa.workflows.generate_sdk.activities.fix_python_sdk_imports_activity_wrapper import (
    fix_python_sdk_imports_activity,
)
from awa.workflows.generate_sdk.models.generate_sdk_models_input import GenerateSdkModelsInput
from awa.workflows.generate_sdk.models.sdk_config import SdkConfig, SdkLanguageConfig

if TYPE_CHECKING:
    from collections.abc import Callable


class GenerateSdkForLanguageInput(BaseModel):
    """Input for the single language SDK generation workflow."""

    language: SdkLanguageConfig
    workflow_paths: WorkflowPaths
    sdk_config: SdkConfig
    json_schemas_path: str
    python_constants: str
    python_models: str
    utility_functions: dict[str, list[dict[str, str]]]
    changed_components: dict[str, str]
    sdk_version: str


# Rebuild the model after all dependencies are defined
GenerateSdkForLanguageInput.model_rebuild()


@workflow.defn(name=generate_sdk_constants.WORKFLOW_GENERATE_SDK_FOR_LANGUAGE)
class GenerateSdkForLanguageWorkflow:
    """Workflow to process a single language for SDK generation."""

    @workflow.run
    async def run(self, workflow_input: GenerateSdkForLanguageInput) -> None:
        """Process a single language for SDK generation.

        Args:
            workflow_input: Input containing all necessary data for language processing

        """
        if workflow_input.language.name == "python":
            # Copy Python files to Python SDK directly from source
            await self._copy_python_sdk_files(workflow_input.workflow_paths, workflow_input.sdk_config)
            return

        # Ensure SDK directory exists for non-Python languages
        await self._ensure_sdk_directory_exists(
            workflow_input.workflow_paths,
            workflow_input.sdk_config,
            workflow_input.language.name,
        )

        # Check what needs to be regenerated based on changed components
        needs_models = any(comp in ["models", "constants"] for comp in workflow_input.changed_components)
        needs_constants = "constants" in workflow_input.changed_components
        changed_utils = {
            util_type: [
                func for func in funcs if f"{util_type}_utils/{func['name']}" in workflow_input.changed_components
            ]
            for util_type, funcs in workflow_input.utility_functions.items()
        }

        # Generate SDK models from JSON schemas if needed
        if needs_models:
            await self._generate_sdk_models(
                workflow_input.language,
                workflow_input.json_schemas_path,
                workflow_input.sdk_config.output_path,
            )

        # Update constants if needed
        translated_constants_content = ""
        if needs_constants:
            translated_constants_content = await self._update_constants_in_place(
                workflow_input.workflow_paths,
                workflow_input.language,
                workflow_input.python_constants,
                workflow_input.sdk_config,
            )
        else:
            # Load existing constants for utility function translation
            constants_file_path = str(
                Path(workflow_input.sdk_config.output_path)
                / f"{workflow_input.language.name}"
                / f"{workflow_input.language.constants_path}"
                / f"{workflow_input.language.constants_file_name}{workflow_input.language.ext}",
            )
            translated_constants_content = await read_file_activity(constants_file_path, default="")

        # Load target language models
        target_language_models = await read_file_activity(
            str(
                Path(workflow_input.workflow_paths.project_root)
                / workflow_input.sdk_config.output_path
                / workflow_input.language.name
                / workflow_input.language.model_path
                / f"{workflow_input.language.model_file_name}{workflow_input.language.ext}",
            ),
        )

        # Translate utility functions (only changed ones) in parallel
        await self._translate_utility_functions_parallel(
            workflow_paths=workflow_input.workflow_paths,
            language=workflow_input.language,
            python_constants=workflow_input.python_constants,
            target_language_constants=translated_constants_content,
            python_models=workflow_input.python_models,
            target_language_models=target_language_models,
            sdk_config=workflow_input.sdk_config,
            changed_utils=changed_utils,
        )

        # Ensure the test project builds successfully
        if workflow_input.language.test_command:
            await self._ensure_test_project_builds(
                language=workflow_input.language,
                workflow_paths=workflow_input.workflow_paths,
                sdk_config=workflow_input.sdk_config,
            )

            # Fix tests for each updated utility function in parallel
            await self._fix_utility_function_tests_parallel(
                language=workflow_input.language,
                workflow_paths=workflow_input.workflow_paths,
                sdk_config=workflow_input.sdk_config,
                changed_utils=changed_utils,
            )

        # Run tests and fix failures if any
        if workflow_input.language.test_command:
            await self._run_tests_and_fix_failures(
                language=workflow_input.language,
                workflow_paths=workflow_input.workflow_paths,
                sdk_config=workflow_input.sdk_config,
            )

    async def _translate_utility_functions_parallel(
        self,
        workflow_paths: WorkflowPaths,
        language: SdkLanguageConfig,
        python_constants: str,
        target_language_constants: str,
        python_models: str,
        target_language_models: str,
        sdk_config: SdkConfig,
        changed_utils: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Translate utility functions in parallel with controlled concurrency.

        Args:
            workflow_paths: Workflow paths configuration
            language: Target language configuration
            python_constants: Python constants content
            target_language_constants: Already translated constants for the target language
            python_models: Python models content
            target_language_models: Language models content
            sdk_config: SDK configuration
            changed_utils: Dictionary of changed utility functions by type

        """
        # Pre-read all files that would be read in the loop
        translate_utility_function_baml_content = await read_file_activity(
            str(Path(workflow_paths.workflow_root) / "baml_src" / "translate_utility_function.baml"),
        )
        conventions = await read_file_activity(
            str(Path(workflow_paths.project_root) / "awa" / "sdk" / "conventions" / f"{language.name}.md"),
        )
        translation_guide = await read_file_activity(
            str(
                Path(workflow_paths.project_root) / "awa" / "sdk" / "translation_guides" / f"{language.name}.md",
            ),
        )

        # Create tasks for parallel processing
        utility_translation_tasks = []
        for util_type in ["workflow", "activity", "general"]:
            for utility_function in changed_utils.get(util_type, []):

                def create_utility_processor(func: dict[str, Any], u_type: str) -> Callable:
                    async def process_utility_closure() -> None:
                        return await self._update_utility_function(
                            language=language,
                            utility_function=func,
                            util_type=u_type,
                            python_constants=python_constants,
                            target_language_constants=target_language_constants,
                            python_models=python_models,
                            target_language_models=target_language_models,
                            sdk_config=sdk_config,
                            translate_utility_function_baml_content=translate_utility_function_baml_content,
                            conventions=conventions,
                            translation_guide=translation_guide,
                        )

                    return process_utility_closure

                utility_translation_tasks.append(create_utility_processor(utility_function, util_type))

        # Execute utility function translations in parallel with controlled concurrency
        if utility_translation_tasks:
            await ConcurrencyUtils.run_with_controlled_concurrency(
                coroutine_funcs=utility_translation_tasks,
                max_concurrency=5,  # Limit to 5 concurrent utility function translations
            )

    async def _update_utility_function(
        self,
        language: SdkLanguageConfig,
        utility_function: dict[str, Any],
        util_type: str,
        python_constants: str,
        target_language_constants: str,
        python_models: str,
        target_language_models: str,
        sdk_config: SdkConfig,
        translate_utility_function_baml_content: str,
        conventions: str,
        translation_guide: str,
    ) -> None:
        """Update a single utility function using the new file structure.

        Args:
            language: Target language configuration
            utility_function: The utility function to translate
            util_type: Type of utility ("workflow", "activity", or "general")
            python_constants: Python constants content
            target_language_constants: Already translated constants for the target language
            python_models: Python models content
            target_language_models: Language models content
            sdk_config: SDK configuration
            translate_utility_function_baml_content: Pre-read BAML content
            conventions: Pre-read conventions content
            translation_guide: Pre-read translation guide content

        """
        function_name = utility_function["name"]

        # Determine output file path based on language configuration
        utils_file_path = self._get_utility_file_path(language, sdk_config, util_type, function_name)

        workflow.logger.info(f"Translating {util_type} function '{function_name}' for {language.name}")

        # Use execute_baml_transform utility function with output_path and output_json_path
        transform_params = TransformParams(
            baml_function_name="TranslateUtilityFunction",
            baml_content=translate_utility_function_baml_content,
            request={
                "function_name": function_name,
                "function_content": utility_function["function_content"],
                "python_constant_values": python_constants,
                "target_language_constant_values": target_language_constants,
                "python_models": python_models,
                "target_language_models": target_language_models,
                "target_language": language.name,
                "target_language_conventions": conventions,
                "target_language_sdk_translation_guide": translation_guide,
                "utility_type": util_type,
            },
            timeout_seconds=core_constants.DEFAULT_BAML_ACTIVITY_TIMEOUT_SECONDS,
            output_path=str(utils_file_path),
            output_json_path="$.translated_function_content",
        )

        await execute_baml_transform_workflow(
            transform_params=transform_params,
            additional_workflow_id_part=f"{function_name}-{language.name}",
        )

        workflow.logger.info(
            f"Successfully generated {util_type} function '{function_name}' for {language.name}",
        )

    def _get_utility_file_path(
        self,
        language: SdkLanguageConfig,
        sdk_config: SdkConfig,
        util_type: str,
        function_name: str,
    ) -> Path:
        """Get the output file path for a utility function based on language configuration.

        Args:
            language: Target language configuration
            sdk_config: SDK configuration
            util_type: Type of utility ("workflow", "activity", or "general")
            function_name: Name of the utility function

        Returns:
            Path to the output file for the utility function

        """
        # All SDKs use separate files for each utility function
        utils_dir = Path(sdk_config.output_path) / language.name / language.utils_base_path

        # Convert function name to appropriate case for the target language
        if language.utils_use_pascal_case:
            # Convert snake_case to PascalCase
            file_name = "".join(word.capitalize() for word in function_name.split("_"))
        else:
            # Keep original naming for other languages
            file_name = function_name

        if language.utils_organize_by_type:
            # Organize by util_type (e.g., Workflow/Activity subdirectories)
            utils_file_path = utils_dir / f"{util_type.capitalize()}" / f"{file_name}{language.ext}"
        else:
            # Place all utility functions in the base directory
            utils_file_path = utils_dir / f"{file_name}{language.ext}"

        return utils_file_path

    @staticmethod
    async def _copy_python_sdk_files(workflow_paths: WorkflowPaths, sdk_config: SdkConfig) -> None:
        """Copy Python SDK files to the output directory."""
        # Copy models directory
        models_source_path = str(Path(workflow_paths.project_root) / "awa" / "sdk" / "models")
        models_destination_path = str(Path(sdk_config.output_path) / "python" / "awa" / "client" / "models")
        await copy_directory_activity(models_source_path, models_destination_path)

        # Copy utils directory
        utils_source_path = str(Path(workflow_paths.project_root) / "awa" / "sdk" / "utils")
        utils_destination_path = str(Path(sdk_config.output_path) / "python" / "awa" / "client" / "utils")
        await copy_directory_activity(utils_source_path, utils_destination_path)

        # Copy constants file
        constants_source_path = str(Path(workflow_paths.project_root) / "awa" / "sdk" / "constants.py")
        constants_destination_path = str(Path(sdk_config.output_path) / "python" / "awa" / "client" / "constants.py")
        await copy_file_activity(constants_source_path, constants_destination_path)

        # Fix import statements to use awa.client instead of awa.sdk
        python_sdk_path = str(Path(sdk_config.output_path) / "python")
        await fix_python_sdk_imports_activity(python_sdk_path)

        # Generate facade pattern files for cleaner imports
        workflow.logger.info("Generating facade pattern for Python SDK")
        await workflow.execute_activity(
            generate_sdk_constants.ACTIVITY_GENERATE_FACADE,
            arg=python_sdk_path,
            task_queue=core_constants.TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=core_constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
        )
        workflow.logger.info("Facade generation completed")

    @staticmethod
    async def _update_constants_in_place(
        workflow_paths: WorkflowPaths,
        language: SdkLanguageConfig,
        python_constants: str,
        sdk_config: SdkConfig,
    ) -> str:
        """Update constants in-place for non-Python languages."""
        constants_file_path = str(
            Path(sdk_config.output_path)
            / f"{language.name}"
            / f"{language.constants_path}"
            / f"{language.constants_file_name}{language.ext}",
        )

        # Generate translated constants content
        translate_constants_baml_content = await read_file_activity(
            str(Path(workflow_paths.workflow_root) / "baml_src" / "translate_constants.baml"),
        )
        conventions = await read_file_activity(
            str(Path(workflow_paths.project_root) / "awa" / "sdk" / "conventions" / f"{language.name}.md"),
        )
        translate_constants_result_raw: dict[str, Any] = await workflow.execute_child_workflow(
            workflow=sdk_constants.WORKFLOW_TRANSFORM,
            arg={
                "baml_function_name": "TranslateConstants",
                "baml_content": translate_constants_baml_content,
                "request": {
                    "python_constants": python_constants,
                    "target_language": language.name,
                    "target_language_conventions": conventions,
                },
                "timeout_seconds": core_constants.DEFAULT_BAML_ACTIVITY_TIMEOUT_SECONDS,
            },
            id=f"TranslateConstants-{language.name}-{workflow.info().workflow_id}",
        )
        translated_constants_content = translate_constants_result_raw["translated_constants_content"]

        # Write the updated constants content
        await write_file_activity(constants_file_path, translated_constants_content)
        return translated_constants_content

    async def _ensure_sdk_directory_exists(
        self,
        workflow_paths: WorkflowPaths,
        sdk_config: SdkConfig,
        language_name: str,
    ) -> None:
        """Ensure SDK directory exists for non-Python languages."""
        sdk_directory_path = str(
            Path(workflow_paths.project_root) / sdk_config.output_path / language_name,
        )

        directory_exists: bool = await is_directory_activity(sdk_directory_path)

        if not directory_exists:
            workflow.logger.info(f"SDK directory will be created during model generation for {language_name}")
        else:
            workflow.logger.info(f"Using existing {language_name} SDK directory for in-place updates")

    @staticmethod
    async def _generate_sdk_models(language: SdkLanguageConfig, json_schemas_path: str, output_path: str) -> None:
        """Generate SDK models from JSON schemas for a specific language."""
        await workflow.execute_activity(
            activity=generate_sdk_constants.ACTIVITY_GENERATE_SDK_MODELS,
            arg=GenerateSdkModelsInput(
                language_config=language,
                json_schemas_path=json_schemas_path,
                output_path=output_path,
            ),
            start_to_close_timeout=timedelta(seconds=120),
        )

    async def _run_tests_and_fix_failures(
        self,
        language: SdkLanguageConfig,
        workflow_paths: WorkflowPaths,
        sdk_config: SdkConfig,
    ) -> None:
        """Run tests for the generated SDK and fix failures using an agent."""
        max_attempts = 3
        sdk_working_dir = str(Path(workflow_paths.project_root) / sdk_config.output_path / language.name)

        for attempt in range(1, max_attempts + 1):
            workflow.logger.info(f"Running tests for {language.name} SDK (attempt {attempt}/{max_attempts})")

            # Run the test command
            command_input = CommandInput(command=language.test_command, working_dir=sdk_working_dir)
            command_result: CommandResult = await run_command_activity(command_input)

            if command_result.success:
                workflow.logger.info(f"Tests passed for {language.name} SDK")
                return

            workflow.logger.warning(f"Tests failed for {language.name} SDK on attempt {attempt}")
            workflow.logger.info(f"Test output: {command_result.output}")

            if attempt == max_attempts:
                raise RetryableApplicationError(
                    f"Tests failed for {language.name} SDK after {max_attempts} attempts. "
                    f"Final test output: {command_result.output}",
                )

            # Use agent to fix the failing tests
            workflow.logger.info(f"Running agent to fix failing tests for {language.name} SDK")

            await execute_agent_workflow(
                agent_config=AgentConfiguration(
                    mode=AgentModeEnum.ACT,
                    provider=AgentProviderEnum.CLAUDE,
                    build_prompt_params=BuildPromptParams(
                        template_input=InputParams(
                            path=str(Path(workflow_paths.agent_prompts) / "run_tests_and_fix_failures.jinja"),
                        ),
                        variables={
                            "language_name": language.name,
                            "test_command": language.test_command,
                            "sdk_working_dir": str(sdk_working_dir),
                            "test_output": command_result.output,
                        },
                        inputs=[
                            InputParams(
                                name="conventions",
                                path=str(
                                    Path(workflow_paths.project_root)
                                    / "awa"
                                    / "sdk"
                                    / "conventions"
                                    / f"{language.name}.md",
                                ),
                            ),
                            InputParams(
                                name="translation_guide",
                                path=str(
                                    Path(workflow_paths.project_root)
                                    / "awa"
                                    / "sdk"
                                    / "translation_guides"
                                    / f"{language.name}.md",
                                ),
                            ),
                        ],
                    ),
                    working_directory=sdk_working_dir,
                ),
                timeout_seconds=300 * 4,
                name="Fix Tests",
            )

    async def _ensure_test_project_builds(
        self,
        language: SdkLanguageConfig,
        workflow_paths: WorkflowPaths,
        sdk_config: SdkConfig,
    ) -> None:
        """Ensure the test project builds successfully by commenting out problematic tests if needed."""
        workflow.logger.info(f"Ensuring {language.name} SDK test project builds")

        sdk_working_dir = str(Path(workflow_paths.project_root) / sdk_config.output_path / language.name)

        # Determine build command based on language
        build_command = self._get_build_command(language)
        if not build_command:
            workflow.logger.info(f"No build command defined for {language.name}, skipping build check")
            return

        # TODO Agent: The agent right below this line only needs to run if the test project
        # fails to build. So run the build command first, and then run the agent if the build fails.

        # Use agent to ensure the project builds
        await execute_agent_workflow(
            agent_config=AgentConfiguration(
                mode=AgentModeEnum.ACT,
                provider=AgentProviderEnum.CLAUDE,
                build_prompt_params=BuildPromptParams(
                    template_input=InputParams(
                        path=str(Path(workflow_paths.agent_prompts) / "build_test_project.jinja"),
                    ),
                    variables={
                        "language_name": language.name,
                        "build_command": build_command,
                        "sdk_working_dir": sdk_working_dir,
                    },
                    inputs=[
                        InputParams(
                            name="conventions",
                            path=str(
                                Path(workflow_paths.project_root)
                                / "awa"
                                / "sdk"
                                / "conventions"
                                / f"{language.name}.md",
                            ),
                        ),
                        InputParams(
                            name="translation_guide",
                            path=str(
                                Path(workflow_paths.project_root)
                                / "awa"
                                / "sdk"
                                / "translation_guides"
                                / f"{language.name}.md",
                            ),
                        ),
                    ],
                ),
                working_directory=sdk_working_dir,
            ),
            timeout_seconds=300 * 2,
            name="Ensure Build",
        )

    async def _fix_utility_function_tests_parallel(
        self,
        language: SdkLanguageConfig,
        workflow_paths: WorkflowPaths,
        sdk_config: SdkConfig,
        changed_utils: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Fix tests for each updated utility function in parallel."""
        workflow.logger.info(f"Fixing tests for updated utility functions in {language.name} SDK")

        sdk_working_dir = str(Path(workflow_paths.project_root) / sdk_config.output_path / language.name)

        # Collect all utility functions that need test fixes
        utility_functions_to_fix = [
            (util_type, func_info["name"]) for util_type, functions in changed_utils.items() for func_info in functions
        ]

        if not utility_functions_to_fix:
            workflow.logger.info("No utility functions to fix tests for")
            return

        # Fix tests for each utility function in parallel with concurrency limit
        async def fix_single_utility_tests(util_type: str, function_name: str) -> None:
            """Fix tests for a single utility function."""
            workflow.logger.info(f"Fixing tests for {util_type} function: {function_name}")

            # Get the path to the utility function file
            utility_file_path = self._get_utility_file_path(language, sdk_config, util_type, function_name)

            await execute_agent_workflow(
                agent_config=AgentConfiguration(
                    mode=AgentModeEnum.ACT,
                    provider=AgentProviderEnum.CLAUDE,
                    build_prompt_params=BuildPromptParams(
                        template_input=InputParams(
                            path=str(Path(workflow_paths.agent_prompts) / "fix_utility_function_tests.jinja"),
                        ),
                        variables={
                            "language_name": language.name,
                            "test_command": language.test_command or "test",
                            "sdk_working_dir": sdk_working_dir,
                            "utility_function_name": function_name,
                            "utility_function_file": str(utility_file_path),
                        },
                        inputs=[
                            InputParams(
                                name="conventions",
                                path=str(
                                    Path(workflow_paths.project_root)
                                    / "awa"
                                    / "sdk"
                                    / "conventions"
                                    / f"{language.name}.md",
                                ),
                            ),
                            InputParams(
                                name="translation_guide",
                                path=str(
                                    Path(workflow_paths.project_root)
                                    / "awa"
                                    / "sdk"
                                    / "translation_guides"
                                    / f"{language.name}.md",
                                ),
                            ),
                        ],
                    ),
                    working_directory=sdk_working_dir,
                ),
                timeout_seconds=300 * 2,
                name=f"Fix {function_name} Tests",
            )

        # Execute test fixes in parallel
        coroutine_funcs = [
            lambda ut=util_type, fn=func_name: fix_single_utility_tests(ut, fn)
            for util_type, func_name in utility_functions_to_fix
        ]
        await ConcurrencyUtils.run_with_controlled_concurrency(
            coroutine_funcs=coroutine_funcs,
            max_concurrency=3,
        )

    def _get_build_command(self, language: SdkLanguageConfig) -> str | None:
        """Get the build command for a specific language."""
        # Map of language names to their build commands
        build_commands = {
            "csharp": "dotnet build",
            "typescript": "npm run build",
            "javascript": "npm run build",
            "java": "mvn compile",
            "go": "go build ./...",
            "rust": "cargo build",
        }
        return build_commands.get(language.name.lower())
