"""Unit tests for the GenerateSdkForLanguageWorkflow."""

import pytest
from temporalio import activity

from awa.sdk import constants as sdk_constants
from awa.sdk.models.workflow_paths import WorkflowPaths
from awa.workflows.generate_sdk import constants as workflow_constants
from awa.workflows.generate_sdk.generate_sdk_for_language_workflow import (
    GenerateSdkForLanguageInput,
    GenerateSdkForLanguageWorkflow,
)
from awa.workflows.generate_sdk.models.sdk_config import SdkConfig, SdkLanguageConfig


# Mock activities
@activity.defn(name=sdk_constants.ACTIVITY_COPY_DIRECTORY)
async def copy_directory_activity_mock(source: str, destination: str) -> None:
    """Mock copy directory activity."""


@activity.defn(name=sdk_constants.ACTIVITY_COPY_FILE)
async def copy_file_activity_mock(source: str, destination: str) -> None:
    """Mock copy file activity."""


@activity.defn(name=sdk_constants.ACTIVITY_IS_DIRECTORY)
async def is_directory_activity_mock(_path: str) -> bool:
    """Mock is directory activity."""
    return True


@activity.defn(name=sdk_constants.ACTIVITY_READ_FILE)
async def read_file_activity_mock(path: str, default: str = "") -> str:
    """Mock read file activity."""
    if "constants" in path:
        return "mock constants content"
    if "models" in path:
        return "mock models content"
    if "baml" in path:
        return "mock baml content"
    if "conventions" in path:
        return "mock conventions content"
    if "translation_guides" in path:
        return "mock translation guide content"
    return default


@activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
async def write_file_activity_mock(path: str, content: str) -> None:
    """Mock write file activity."""


@activity.defn(name=sdk_constants.ACTIVITY_RUN_COMMAND)
async def run_command_activity_mock(_command_input: dict) -> dict:
    """Mock run command activity."""
    return {"success": True, "output": "mock test output", "exit_code": 0}


@activity.defn(name=workflow_constants.ACTIVITY_GENERATE_SDK_MODELS)
async def generate_sdk_models_activity_mock(_input_data: dict) -> None:
    """Mock generate SDK models activity."""


class TestGenerateSdkForLanguageWorkflow:
    """Test cases for GenerateSdkForLanguageWorkflow."""

    @pytest.fixture
    def mock_workflow_paths(self) -> WorkflowPaths:
        """Create mock workflow paths."""
        return WorkflowPaths(
            input="/mock/input",
            output="/mock/output",
            baml_src="/mock/baml_src",
            agent_prompts="/mock/agent_prompts",
            project_root="/mock/project",
            workflow_root="/mock/workflow",
        )

    @pytest.fixture
    def mock_sdk_config(self) -> SdkConfig:
        """Create mock SDK config."""
        return SdkConfig(
            output_path="/mock/output",
            languages=[
                SdkLanguageConfig(
                    name="python",
                    enabled=True,
                    ext=".py",
                    model_path="models",
                    model_file_name="models",
                    constants_path="",
                    constants_file_name="constants",
                    utils_base_path="utils",
                    utils_use_pascal_case=False,
                    utils_organize_by_type=False,
                    test_command=None,
                ),
                SdkLanguageConfig(
                    name="csharp",
                    enabled=True,
                    ext=".cs",
                    model_path="models",
                    model_file_name="models",
                    constants_path="",
                    constants_file_name="constants",
                    utils_base_path="utils",
                    utils_use_pascal_case=True,
                    utils_organize_by_type=True,
                    test_command="dotnet test",
                ),
            ],
        )

    @pytest.fixture
    def mock_python_language_input(
        self,
        mock_workflow_paths: WorkflowPaths,
        mock_sdk_config: SdkConfig,
    ) -> GenerateSdkForLanguageInput:
        """Create mock input for Python language processing."""
        return GenerateSdkForLanguageInput(
            language=mock_sdk_config.languages[0],  # Python language
            workflow_paths=mock_workflow_paths,
            sdk_config=mock_sdk_config,
            json_schemas_path="/mock/schemas",
            python_constants="mock python constants",
            python_models="mock python models",
            utility_functions={"workflow": [], "activity": []},
            changed_components={"models": "hash1", "constants": "hash2"},
            sdk_version="1.0.0",
        )

    @pytest.fixture
    def mock_csharp_language_input(
        self,
        mock_workflow_paths: WorkflowPaths,
        mock_sdk_config: SdkConfig,
    ) -> GenerateSdkForLanguageInput:
        """Create mock input for C# language processing."""
        return GenerateSdkForLanguageInput(
            language=mock_sdk_config.languages[1],  # C# language
            workflow_paths=mock_workflow_paths,
            sdk_config=mock_sdk_config,
            json_schemas_path="/mock/schemas",
            python_constants="mock python constants",
            python_models="mock python models",
            utility_functions={
                "workflow": [{"name": "test_workflow", "function_content": "mock workflow content"}],
                "activity": [{"name": "test_activity", "function_content": "mock activity content"}],
            },
            changed_components={
                "models": "hash1",
                "constants": "hash2",
                "workflow_utils/test_workflow": "hash3",
                "activity_utils/test_activity": "hash4",
            },
        )

    def test_workflow_structure(self) -> None:
        """Test that the workflow has the expected structure and methods."""
        # Arrange & Act
        workflow = GenerateSdkForLanguageWorkflow()

        # Assert
        assert hasattr(workflow, "run")
        assert callable(workflow.run)
        assert hasattr(workflow, "_get_utility_file_path")
        assert callable(workflow._get_utility_file_path)

    def test_input_model_structure(
        self,
        mock_python_language_input: GenerateSdkForLanguageInput,
    ) -> None:
        """Test that the input model has the expected structure."""
        # Act & Assert
        assert hasattr(mock_python_language_input, "language")
        assert hasattr(mock_python_language_input, "workflow_paths")
        assert hasattr(mock_python_language_input, "sdk_config")
        assert hasattr(mock_python_language_input, "json_schemas_path")
        assert hasattr(mock_python_language_input, "python_constants")
        assert hasattr(mock_python_language_input, "python_models")
        assert hasattr(mock_python_language_input, "utility_functions")
        assert hasattr(mock_python_language_input, "changed_components")

    def test_workflow_is_properly_defined(self) -> None:
        """Test that the workflow is properly defined with the correct name."""
        # Act & Assert - Check that the workflow decorator was applied
        assert hasattr(GenerateSdkForLanguageWorkflow, "__temporal_workflow_definition")
        workflow_def = getattr(GenerateSdkForLanguageWorkflow, "__temporal_workflow_definition")
        assert workflow_def is not None
        assert workflow_def.name == "awa-generate-sdk-for-language"

    def test_get_utility_file_path_pascal_case_organized(self) -> None:
        """Test utility file path generation with PascalCase and organization by type."""
        # Arrange
        workflow = GenerateSdkForLanguageWorkflow()
        language = SdkLanguageConfig(
            name="csharp",
            enabled=True,
            ext=".cs",
            model_path="Models",
            model_file_name="Models",
            constants_path="",
            constants_file_name="Constants",
            utils_base_path="Utils",
            utils_use_pascal_case=True,
            utils_organize_by_type=True,
            test_command=None,
        )
        sdk_config = SdkConfig(output_path="/mock/output", languages=[language])

        # Act
        result = workflow._get_utility_file_path(language, sdk_config, "activity", "read_file")

        # Assert
        expected_path = "/mock/output/csharp/Utils/Activity/ReadFile.cs"
        assert str(result) == expected_path

    def test_get_utility_file_path_snake_case_flat(self) -> None:
        """Test utility file path generation with snake_case and flat organization."""
        # Arrange
        workflow = GenerateSdkForLanguageWorkflow()
        language = SdkLanguageConfig(
            name="python",
            enabled=True,
            ext=".py",
            model_path="models",
            model_file_name="models",
            constants_path="",
            constants_file_name="constants",
            utils_base_path="utils",
            utils_use_pascal_case=False,
            utils_organize_by_type=False,
            test_command=None,
        )
        sdk_config = SdkConfig(output_path="/mock/output", languages=[language])

        # Act
        result = workflow._get_utility_file_path(language, sdk_config, "workflow", "execute_agent")

        # Assert
        expected_path = "/mock/output/python/utils/execute_agent.py"
        assert str(result) == expected_path
