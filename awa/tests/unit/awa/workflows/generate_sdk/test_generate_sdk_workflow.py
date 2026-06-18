"""Unit tests for the GenerateSdkWorkflow."""

from temporalio import activity

from awa.sdk import constants as sdk_constants
from awa.workflows.generate_sdk import constants as workflow_constants
from awa.workflows.generate_sdk.generate_sdk_workflow import GenerateSdkWorkflow
from awa.workflows.generate_sdk.models.generate_sdk_input import GenerateSdkInput


# Mock activities
@activity.defn(name=workflow_constants.ACTIVITY_GET_SDK_CONFIG)
async def get_sdk_config_activity_mock(_config_path: str | None = None) -> dict:
    """Mock get SDK config activity."""
    return {
        "output_path": "/mock/output",
        "languages": [
            {
                "name": "python",
                "enabled": True,
                "ext": ".py",
                "model_path": "models",
                "model_file_name": "models",
                "constants_path": "",
                "constants_file_name": "constants",
                "utils_base_path": "utils",
                "utils_use_pascal_case": False,
                "utils_organize_by_type": False,
                "test_command": None,
            },
            {
                "name": "typescript",
                "enabled": True,
                "ext": ".ts",
                "model_path": "models",
                "model_file_name": "models",
                "constants_path": "",
                "constants_file_name": "constants",
                "utils_base_path": "utils",
                "utils_use_pascal_case": True,
                "utils_organize_by_type": True,
                "test_command": "npm test",
            },
        ],
    }


@activity.defn(name=workflow_constants.ACTIVITY_GET_CHANGED_COMPONENTS)
async def get_changed_components_activity_mock() -> dict[str, str]:
    """Mock get changed components activity."""
    return {
        "models": "hash1",
        "constants": "hash2",
        "workflow_utils/test_workflow": "hash3",
    }


@activity.defn(name=workflow_constants.ACTIVITY_CALCULATE_ALL_COMPONENT_HASHES)
async def calculate_all_component_hashes_activity_mock() -> dict[str, str]:
    """Mock calculate all component hashes activity."""
    return {
        "models": "hash1",
        "constants": "hash2",
        "workflow_utils/test_workflow": "hash3",
        "activity_utils/test_activity": "hash4",
    }


@activity.defn(name=workflow_constants.ACTIVITY_STORE_COMPONENT_HASHES)
async def store_component_hashes_activity_mock(hashes: dict[str, str]) -> None:
    """Mock store component hashes activity."""


@activity.defn(name=sdk_constants.ACTIVITY_READ_FILE)
async def read_file_activity_mock(path: str, _default: str = "") -> str:
    """Mock read file activity."""
    if "constants.py" in path:
        return "mock python constants content"
    return "mock file content"


@activity.defn(name=sdk_constants.ACTIVITY_READ_DIRECTORY)
async def read_directory_activity_mock(_path: str) -> list[dict]:
    """Mock read directory activity."""
    return [
        {"file": "model1.py", "content": "mock model 1 content"},
        {"file": "model2.py", "content": "mock model 2 content"},
    ]


@activity.defn(name=workflow_constants.ACTIVITY_GENERATE_SCHEMAS)
async def generate_schemas_activity_mock(_input_data: dict) -> None:
    """Mock generate schemas activity."""


class TestGenerateSdkWorkflow:
    """Test cases for GenerateSdkWorkflow."""

    def test_workflow_is_properly_defined(self) -> None:
        """Test that the workflow is properly defined with the correct name."""
        # Act & Assert - Check that the workflow decorator was applied
        assert hasattr(GenerateSdkWorkflow, "__temporal_workflow_definition")
        workflow_def = getattr(GenerateSdkWorkflow, "__temporal_workflow_definition")
        assert workflow_def is not None
        assert workflow_def.name == "awa-generate-sdk"

    def test_workflow_structure_after_refactoring(self) -> None:
        """Test that the refactored workflow has the expected structure."""
        # Arrange & Act
        workflow = GenerateSdkWorkflow()

        # Assert
        assert hasattr(workflow, "run")
        assert callable(workflow.run)
        # Methods that were moved to child workflow should no longer exist
        assert not hasattr(workflow, "_process_single_language")
        assert not hasattr(workflow, "_translate_utility_functions_parallel")
        assert not hasattr(workflow, "_update_utility_function")

    def test_input_model_validation(self) -> None:
        """Test that the input model validates correctly."""
        # Act & Assert - Test valid input
        valid_input = GenerateSdkInput(config_path=None, force=False, bump=False)
        assert valid_input.config_path is None
        assert valid_input.force is False
        assert valid_input.bump is False

        # Test input with custom config path
        custom_input = GenerateSdkInput(config_path="/custom/path", force=True, bump=False)
        assert custom_input.config_path == "/custom/path"
        assert custom_input.force is True
        assert custom_input.bump is False

        # Test input with bump flag
        bump_input = GenerateSdkInput(config_path=None, force=False, bump=True)
        assert bump_input.config_path is None
        assert bump_input.force is False
        assert bump_input.bump is True

        # Test with both force and bump
        both_input = GenerateSdkInput(config_path=None, force=True, bump=True)
        assert both_input.config_path is None
        assert both_input.force is True
        assert both_input.bump is True

    def test_discover_utility_functions_structure(self) -> None:
        """Test that the workflow has the correct utility function discovery structure."""
        # Arrange
        workflow = GenerateSdkWorkflow()

        # Act & Assert
        # The workflow should have a _discover_utility_functions method
        assert hasattr(workflow, "_discover_utility_functions")
        assert callable(workflow._discover_utility_functions)

    def test_workflow_paths_generation(self) -> None:
        """Test that the workflow can generate workflow paths."""
        # Arrange
        workflow = GenerateSdkWorkflow()

        # Act & Assert
        # The workflow should have a _get_workflow_paths method
        assert hasattr(workflow, "_get_workflow_paths")
        assert callable(workflow._get_workflow_paths)

    def test_workflow_concurrency_limit(self) -> None:
        """Test that the workflow has a reasonable concurrency limit."""
        # Arrange
        workflow = GenerateSdkWorkflow()

        # Act & Assert
        assert hasattr(workflow, "language_max_concurrency")
        assert workflow.language_max_concurrency == 3

    def test_sdk_versioning_methods_exist(self) -> None:
        """Test that SDK versioning methods exist and are callable."""
        # Arrange
        workflow = GenerateSdkWorkflow()

        # Act & Assert
        assert hasattr(workflow, "_determine_sdk_version")
        assert callable(workflow._determine_sdk_version)
        assert hasattr(workflow, "_calculate_sdk_hash")
        assert callable(workflow._calculate_sdk_hash)
        assert hasattr(workflow, "_find_current_version_file")
        assert callable(workflow._find_current_version_file)
        assert hasattr(workflow, "_parse_version")
        assert callable(workflow._parse_version)
        assert hasattr(workflow, "_bump_patch_version")
        assert callable(workflow._bump_patch_version)
        assert hasattr(workflow, "_write_version_file")
        assert callable(workflow._write_version_file)
        assert hasattr(workflow, "_update_version_file_if_changed")
        assert callable(workflow._update_version_file_if_changed)

    def test_parse_version_valid_inputs(self) -> None:
        """Test version parsing with valid version strings."""
        # Arrange
        workflow = GenerateSdkWorkflow()

        # Act & Assert
        assert workflow._parse_version("1.2.3") == (1, 2, 3)
        assert workflow._parse_version("0.0.1") == (0, 0, 1)
        assert workflow._parse_version("10.20.30") == (10, 20, 30)

    def test_parse_version_invalid_inputs(self) -> None:
        """Test version parsing with invalid version strings."""
        # Arrange
        workflow = GenerateSdkWorkflow()

        # Act & Assert
        assert workflow._parse_version("invalid") == (0, 0, 0)
        assert workflow._parse_version("1.2") == (0, 0, 0)
        assert workflow._parse_version("1.2.3.4") == (1, 2, 3)  # Takes first 3 parts
        assert workflow._parse_version("") == (0, 0, 0)

    async def test_bump_patch_version_valid_inputs(self) -> None:
        """Test patch version bumping with valid version strings."""
        # Arrange
        workflow = GenerateSdkWorkflow()

        # Act & Assert
        assert await workflow._bump_patch_version("1.2.3") == "1.2.4"
        assert await workflow._bump_patch_version("0.0.1") == "0.0.2"
        assert await workflow._bump_patch_version("10.20.30") == "10.20.31"

    async def test_bump_patch_version_invalid_inputs(self) -> None:
        """Test patch version bumping with invalid version strings."""
        # Arrange
        workflow = GenerateSdkWorkflow()

        # Act & Assert
        assert await workflow._bump_patch_version("invalid") == "0.0.1"
        assert await workflow._bump_patch_version("1.2") == "0.0.1"
        assert await workflow._bump_patch_version("") == "0.0.1"
