"""Tests for the TestDoctorWorkflowInput model."""

import pytest
from pydantic import ValidationError

from cookbook.recipes.workflows.test_doctor.models.workflow_input import TestDoctorWorkflowInput

# Number of required fields in TestDoctorWorkflowInput
EXPECTED_REQUIRED_FIELDS_COUNT = 7

# Length for very long string testing
LONG_STRING_LENGTH = 1000


class TestTestDoctorWorkflowInput:
    """Test class for TestDoctorWorkflowInput model."""

    def test_valid_input_creation(self) -> None:
        """Test creating TestDoctorWorkflowInput with valid parameters."""
        # Arrange
        valid_data = {
            "branch_name": "feature/new-feature",
            "base_branch": "main",
            "repo_path": "/path/to/project",
            "working_directory": "src",
            "testing_guidelines_path": "/path/to/guidelines.md",
            "file_extensions": "py,cs,ts",
            "tests_directory": "tests",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**valid_data)

        # Assert
        assert workflow_input.branch_name == "feature/new-feature"
        assert workflow_input.base_branch == "main"
        assert workflow_input.repo_path == "/path/to/project"
        assert workflow_input.working_directory == "src"
        assert workflow_input.testing_guidelines_path == "/path/to/guidelines.md"
        assert workflow_input.file_extensions == "py,cs,ts"
        assert workflow_input.tests_directory == "tests"

    def test_field_types_are_strings(self) -> None:
        """Test that all fields are properly typed as strings."""
        # Arrange
        valid_data = {
            "branch_name": "feature/test",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py",
            "tests_directory": "tests",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**valid_data)

        # Assert
        assert isinstance(workflow_input.branch_name, str)
        assert isinstance(workflow_input.base_branch, str)
        assert isinstance(workflow_input.repo_path, str)
        assert isinstance(workflow_input.working_directory, str)
        assert isinstance(workflow_input.testing_guidelines_path, str)
        assert isinstance(workflow_input.file_extensions, str)
        assert isinstance(workflow_input.tests_directory, str)

    def test_missing_branch_name_raises_validation_error(self) -> None:
        """Test that missing branch_name raises ValidationError."""
        # Arrange
        invalid_data = {
            "base_branch": "main",
            "repo_path": "/path/to/project",
            "working_directory": "src",
            "testing_guidelines_path": "/path/to/guidelines.md",
            "file_extensions": "py,cs,ts",
            "tests_directory": "tests",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        assert "branch_name" in str(exc_info.value)

    def test_missing_base_branch_raises_validation_error(self) -> None:
        """Test that missing base_branch raises ValidationError."""
        # Arrange
        invalid_data = {
            "branch_name": "feature/new-feature",
            "repo_path": "/path/to/project",
            "working_directory": "src",
            "testing_guidelines_path": "/path/to/guidelines.md",
            "file_extensions": "py,cs,ts",
            "tests_directory": "tests",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        assert "base_branch" in str(exc_info.value)

    def test_missing_repo_path_raises_validation_error(self) -> None:
        """Test that missing repo_path raises ValidationError."""
        # Arrange
        invalid_data = {
            "branch_name": "feature/new-feature",
            "base_branch": "main",
            "working_directory": "src",
            "testing_guidelines_path": "/path/to/guidelines.md",
            "file_extensions": "py,cs,ts",
            "tests_directory": "tests",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        assert "repo_path" in str(exc_info.value)

    def test_missing_working_directory_raises_validation_error(self) -> None:
        """Test that missing working_directory raises ValidationError."""
        # Arrange
        invalid_data = {
            "branch_name": "feature/new-feature",
            "base_branch": "main",
            "repo_path": "/path/to/project",
            "testing_guidelines_path": "/path/to/guidelines.md",
            "file_extensions": "py,cs,ts",
            "tests_directory": "tests",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        assert "working_directory" in str(exc_info.value)

    def test_missing_testing_guidelines_path_raises_validation_error(self) -> None:
        """Test that missing testing_guidelines_path raises ValidationError."""
        # Arrange
        invalid_data = {
            "branch_name": "feature/new-feature",
            "base_branch": "main",
            "repo_path": "/path/to/project",
            "working_directory": "src",
            "file_extensions": "py,cs,ts",
            "tests_directory": "tests",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        assert "testing_guidelines_path" in str(exc_info.value)

    def test_missing_file_extensions_raises_validation_error(self) -> None:
        """Test that missing file_extensions raises ValidationError."""
        # Arrange
        invalid_data = {
            "branch_name": "feature/new-feature",
            "base_branch": "main",
            "repo_path": "/path/to/project",
            "working_directory": "src",
            "testing_guidelines_path": "/path/to/guidelines.md",
            "tests_directory": "tests",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        assert "file_extensions" in str(exc_info.value)

    def test_missing_tests_directory_raises_validation_error(self) -> None:
        """Test that missing tests_directory raises ValidationError."""
        # Arrange
        invalid_data = {
            "branch_name": "feature/new-feature",
            "base_branch": "main",
            "repo_path": "/path/to/project",
            "working_directory": "src",
            "testing_guidelines_path": "/path/to/guidelines.md",
            "file_extensions": "py,cs,ts",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        assert "tests_directory" in str(exc_info.value)

    def test_none_values_raise_validation_error(self) -> None:
        """Test that None values for required fields raise ValidationError."""
        # Arrange
        invalid_data = {
            "branch_name": None,
            "base_branch": "main",
            "repo_path": "/path/to/project",
            "working_directory": "src",
            "testing_guidelines_path": "/path/to/guidelines.md",
            "file_extensions": "py,cs,ts",
            "tests_directory": "tests",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        assert "branch_name" in str(exc_info.value)

    def test_empty_string_values_accepted(self) -> None:
        """Test that empty string values are accepted for all fields."""
        # Arrange
        data_with_empty_strings = {
            "branch_name": "",
            "base_branch": "",
            "repo_path": "",
            "working_directory": "",
            "testing_guidelines_path": "",
            "file_extensions": "",
            "tests_directory": "",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**data_with_empty_strings)

        # Assert
        assert workflow_input.branch_name == ""
        assert workflow_input.base_branch == ""
        assert workflow_input.repo_path == ""
        assert workflow_input.working_directory == ""
        assert workflow_input.testing_guidelines_path == ""
        assert workflow_input.file_extensions == ""
        assert workflow_input.tests_directory == ""

    def test_whitespace_only_values_accepted(self) -> None:
        """Test that whitespace-only values are accepted."""
        # Arrange
        data_with_whitespace = {
            "branch_name": "   ",
            "base_branch": "\t",
            "repo_path": "\n",
            "working_directory": " \t ",
            "testing_guidelines_path": " \t\n ",
            "file_extensions": "  ",
            "tests_directory": "\n\t",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**data_with_whitespace)

        # Assert
        assert workflow_input.branch_name == "   "
        assert workflow_input.base_branch == "\t"
        assert workflow_input.repo_path == "\n"
        assert workflow_input.working_directory == " \t "
        assert workflow_input.testing_guidelines_path == " \t\n "
        assert workflow_input.file_extensions == "  "
        assert workflow_input.tests_directory == "\n\t"

    def test_non_string_types_raise_validation_error(self) -> None:
        """Test that non-string types raise validation errors."""
        # Arrange
        data_with_int = {
            "branch_name": 123,
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**data_with_int)

        assert "branch_name" in str(exc_info.value)
        assert "string_type" in str(exc_info.value)

    def test_non_string_types_various_validation_errors(self) -> None:
        """Test that various non-string types raise appropriate validation errors."""
        # Test with boolean
        data_with_bool = {
            "branch_name": "feature/test",
            "base_branch": True,
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**data_with_bool)

        assert "base_branch" in str(exc_info.value)

        # Test with list
        data_with_list = {
            "branch_name": "feature/test",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": ["path", "to", "file"],
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**data_with_list)

        assert "testing_guidelines_path" in str(exc_info.value)

        # Test with set
        data_with_set = {
            "branch_name": "feature/test",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": {"py", "cs", "ts"},
            "tests_directory": "tests",
        }

        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**data_with_set)

        assert "file_extensions" in str(exc_info.value)

        # Test with dict
        data_with_dict = {
            "branch_name": "feature/test",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": {"dir": "src"},
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**data_with_dict)

        assert "working_directory" in str(exc_info.value)

    def test_special_characters_in_values(self) -> None:
        """Test that special characters are handled correctly."""
        # Arrange
        data_with_special_chars = {
            "branch_name": "feature/fix-#123-&-improve",
            "base_branch": "main@v2.0",
            "repo_path": "/path/with spaces/and-symbols!@#$",
            "working_directory": "src/main/java",
            "testing_guidelines_path": "/path/to/file with spaces & symbols.md",
            "file_extensions": "py,cs,ts,js,jsx,tsx",
            "tests_directory": "tests/unit & integration",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**data_with_special_chars)

        # Assert
        assert workflow_input.branch_name == "feature/fix-#123-&-improve"
        assert workflow_input.base_branch == "main@v2.0"
        assert workflow_input.repo_path == "/path/with spaces/and-symbols!@#$"
        assert workflow_input.working_directory == "src/main/java"
        assert workflow_input.testing_guidelines_path == "/path/to/file with spaces & symbols.md"
        assert workflow_input.file_extensions == "py,cs,ts,js,jsx,tsx"
        assert workflow_input.tests_directory == "tests/unit & integration"

    def test_unicode_characters_supported(self) -> None:
        """Test that Unicode characters are supported."""
        # Arrange
        data_with_unicode = {
            "branch_name": "feature/添加-新功能",
            "base_branch": "主分支",
            "repo_path": "/路径/到/项目",
            "working_directory": "源代码",
            "testing_guidelines_path": "/测试/指南.md",
            "file_extensions": "py,测试",
            "tests_directory": "测试目录",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**data_with_unicode)

        # Assert
        assert workflow_input.branch_name == "feature/添加-新功能"
        assert workflow_input.base_branch == "主分支"
        assert workflow_input.repo_path == "/路径/到/项目"
        assert workflow_input.working_directory == "源代码"
        assert workflow_input.testing_guidelines_path == "/测试/指南.md"
        assert workflow_input.file_extensions == "py,测试"
        assert workflow_input.tests_directory == "测试目录"

    def test_very_long_strings_accepted(self) -> None:
        """Test that very long strings are accepted."""
        # Arrange
        long_string = "a" * LONG_STRING_LENGTH
        data_with_long_strings = {
            "branch_name": long_string,
            "base_branch": long_string,
            "repo_path": long_string,
            "working_directory": long_string,
            "testing_guidelines_path": long_string,
            "file_extensions": long_string,
            "tests_directory": long_string,
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**data_with_long_strings)

        # Assert
        assert len(workflow_input.branch_name) == LONG_STRING_LENGTH
        assert len(workflow_input.base_branch) == LONG_STRING_LENGTH
        assert len(workflow_input.repo_path) == LONG_STRING_LENGTH
        assert len(workflow_input.working_directory) == LONG_STRING_LENGTH
        assert len(workflow_input.testing_guidelines_path) == LONG_STRING_LENGTH
        assert len(workflow_input.file_extensions) == LONG_STRING_LENGTH
        assert len(workflow_input.tests_directory) == LONG_STRING_LENGTH

    def test_model_equality(self) -> None:
        """Test model equality comparison."""
        # Arrange
        data = {
            "branch_name": "feature/test",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        # Act
        workflow_input1 = TestDoctorWorkflowInput(**data)
        workflow_input2 = TestDoctorWorkflowInput(**data)

        # Assert
        assert workflow_input1 == workflow_input2

    def test_model_inequality(self) -> None:
        """Test model inequality comparison."""
        # Arrange
        data1 = {
            "branch_name": "feature/test1",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }
        data2 = {
            "branch_name": "feature/test2",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        # Act
        workflow_input1 = TestDoctorWorkflowInput(**data1)
        workflow_input2 = TestDoctorWorkflowInput(**data2)

        # Assert
        assert workflow_input1 != workflow_input2

    def test_model_serialization_to_dict(self) -> None:
        """Test model serialization to dictionary."""
        # Arrange
        data = {
            "branch_name": "feature/test",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**data)
        serialized = workflow_input.model_dump()

        # Assert
        assert isinstance(serialized, dict)
        assert serialized == data

    def test_model_json_serialization(self) -> None:
        """Test model JSON serialization."""
        # Arrange
        data = {
            "branch_name": "feature/test",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**data)
        json_str = workflow_input.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "feature/test" in json_str
        assert "main" in json_str
        assert "src" in json_str

    def test_model_copy(self) -> None:
        """Test model copying functionality."""
        # Arrange
        original_data = {
            "branch_name": "feature/original",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        # Act
        original = TestDoctorWorkflowInput(**original_data)
        copied = original.model_copy()

        # Assert
        assert original == copied
        assert original is not copied

    def test_model_copy_with_updates(self) -> None:
        """Test model copying with field updates."""
        # Arrange
        original_data = {
            "branch_name": "feature/original",
            "base_branch": "main",
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        # Act
        original = TestDoctorWorkflowInput(**original_data)
        updated = original.model_copy(update={"branch_name": "feature/updated"})

        # Assert
        assert original.branch_name == "feature/original"
        assert updated.branch_name == "feature/updated"
        assert original.base_branch == updated.base_branch

    def test_field_descriptions_exist(self) -> None:
        """Test that field descriptions are properly set."""
        # Arrange & Act
        schema = TestDoctorWorkflowInput.model_json_schema()

        # Assert
        properties = schema["properties"]
        assert "description" in properties["branch_name"]
        assert "description" in properties["base_branch"]
        assert "description" in properties["repo_path"]
        assert "description" in properties["working_directory"]
        assert "description" in properties["testing_guidelines_path"]
        assert "description" in properties["file_extensions"]
        assert "description" in properties["tests_directory"]

        # Verify specific descriptions
        assert "feature branch" in properties["branch_name"]["description"]
        assert "base branch" in properties["base_branch"]["description"]
        assert "absolute path" in properties["repo_path"]["description"]
        assert "working directory" in properties["working_directory"]["description"]
        assert "testing guidelines" in properties["testing_guidelines_path"]["description"]
        assert "file extensions" in properties["file_extensions"]["description"]
        assert "tests should be placed" in properties["tests_directory"]["description"]

    def test_all_fields_required(self) -> None:
        """Test that all fields are marked as required in schema."""
        # Arrange & Act
        schema = TestDoctorWorkflowInput.model_json_schema()

        # Assert
        required_fields = schema["required"]
        assert "branch_name" in required_fields
        assert "base_branch" in required_fields
        assert "repo_path" in required_fields
        assert "working_directory" in required_fields
        assert "testing_guidelines_path" in required_fields
        assert "file_extensions" in required_fields
        assert "tests_directory" in required_fields
        assert len(required_fields) == EXPECTED_REQUIRED_FIELDS_COUNT

    def test_realistic_workflow_input_example(self) -> None:
        """Test with realistic workflow input data."""
        # Arrange
        realistic_data = {
            "branch_name": "feature/AWA-123-add-test-doctor-workflow",
            "base_branch": "main",
            "repo_path": "/Users/developer/projects/awa-cookbook/recipes",
            "working_directory": "workflows/test_doctor",
            "testing_guidelines_path": (
                "/Users/developer/projects/awa-cookbook/recipes/workflows/test_doctor/input/testing_guidelines.md"
            ),
            "file_extensions": "py,ts,js,cs,java",
            "tests_directory": "tests",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**realistic_data)

        # Assert
        assert workflow_input.branch_name == "feature/AWA-123-add-test-doctor-workflow"
        assert workflow_input.base_branch == "main"
        assert "/awa-cookbook/recipes" in workflow_input.repo_path
        assert workflow_input.working_directory == "workflows/test_doctor"
        assert "testing_guidelines.md" in workflow_input.testing_guidelines_path
        assert workflow_input.file_extensions == "py,ts,js,cs,java"
        assert workflow_input.tests_directory == "tests"

    def test_edge_case_single_character_values(self) -> None:
        """Test with single character values."""
        # Arrange
        single_char_data = {
            "branch_name": "a",
            "base_branch": "b",
            "repo_path": "/",
            "working_directory": ".",
            "testing_guidelines_path": "g",
            "file_extensions": "p",
            "tests_directory": "t",
        }

        # Act
        workflow_input = TestDoctorWorkflowInput(**single_char_data)

        # Assert
        assert workflow_input.branch_name == "a"
        assert workflow_input.base_branch == "b"
        assert workflow_input.repo_path == "/"
        assert workflow_input.working_directory == "."
        assert workflow_input.testing_guidelines_path == "g"
        assert workflow_input.file_extensions == "p"
        assert workflow_input.tests_directory == "t"

    def test_multiple_none_values_raise_validation_error(self) -> None:
        """Test that multiple None values raise ValidationError."""
        # Arrange
        invalid_data = {
            "branch_name": None,
            "base_branch": None,
            "repo_path": "/project",
            "working_directory": "src",
            "testing_guidelines_path": "/guidelines.md",
            "file_extensions": "py,cs",
            "tests_directory": "tests",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        error_str = str(exc_info.value)
        assert "branch_name" in error_str
        assert "base_branch" in error_str

    def test_all_none_values_raise_validation_error(self) -> None:
        """Test that all None values raise ValidationError."""
        # Arrange
        invalid_data = {
            "branch_name": None,
            "base_branch": None,
            "repo_path": None,
            "working_directory": None,
            "testing_guidelines_path": None,
            "file_extensions": None,
            "tests_directory": None,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestDoctorWorkflowInput(**invalid_data)

        error_str = str(exc_info.value)
        # Should contain errors for all fields
        assert "branch_name" in error_str
        assert "base_branch" in error_str
        assert "repo_path" in error_str
        assert "working_directory" in error_str
        assert "testing_guidelines_path" in error_str
        assert "file_extensions" in error_str
        assert "tests_directory" in error_str
