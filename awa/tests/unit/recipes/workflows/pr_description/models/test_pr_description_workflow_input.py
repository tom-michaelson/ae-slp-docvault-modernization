"""Unit tests for PR description workflow input model."""

from typing import Any

import pytest
from pydantic import ValidationError

from cookbook.recipes.workflows.pr_description.models.pr_description_workflow_input import PrDescriptionWorkflowInput


class TestPrDescriptionWorkflowInput:
    """Test cases for PrDescriptionWorkflowInput model."""

    def test_required_fields_valid(self) -> None:
        """Test that model can be created with only required fields."""
        input_data = {
            "branch_name": "feature/test-branch",
            "repo_path": "/path/to/repo",
        }

        model = PrDescriptionWorkflowInput(**input_data)

        assert model.branch_name == "feature/test-branch"
        assert model.repo_path == "/path/to/repo"
        assert model.base_branch == "main"  # Default value

    def test_all_fields_valid(self) -> None:
        """Test that model can be created with all fields provided."""
        input_data = {
            "branch_name": "hotfix/critical-fix",
            "repo_path": "/home/user/projects/my-repo",
            "base_branch": "develop",
        }

        model = PrDescriptionWorkflowInput(**input_data)

        assert model.branch_name == "hotfix/critical-fix"
        assert model.repo_path == "/home/user/projects/my-repo"
        assert model.base_branch == "develop"

    def test_missing_required_branch_name_field(self) -> None:
        """Test that ValidationError is raised when branch_name field is missing."""
        input_data = {
            "repo_path": "/path/to/repo",
        }

        with pytest.raises(ValidationError) as exc_info:
            PrDescriptionWorkflowInput(**input_data)

        assert "branch_name" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)

    def test_missing_required_repo_path_field(self) -> None:
        """Test that ValidationError is raised when repo_path field is missing."""
        input_data = {
            "branch_name": "feature/test",
        }

        with pytest.raises(ValidationError) as exc_info:
            PrDescriptionWorkflowInput(**input_data)

        assert "repo_path" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)

    def test_default_base_branch(self) -> None:
        """Test that base_branch defaults to 'main'."""
        input_data = {
            "branch_name": "feature/new-feature",
            "repo_path": "/repos/test-project",
        }

        model = PrDescriptionWorkflowInput(**input_data)
        assert model.base_branch == "main"

    def test_custom_base_branch(self) -> None:
        """Test that custom base_branch can be set."""
        input_data = {
            "branch_name": "feature/new-feature",
            "repo_path": "/repos/test-project",
            "base_branch": "staging",
        }

        model = PrDescriptionWorkflowInput(**input_data)
        assert model.base_branch == "staging"

    def test_empty_string_base_branch(self) -> None:
        """Test that base_branch can be set to empty string."""
        input_data = {
            "branch_name": "feature/test",
            "repo_path": "/path/to/repo",
            "base_branch": "",
        }

        model = PrDescriptionWorkflowInput(**input_data)
        assert model.base_branch == ""

    def test_various_branch_name_formats(self) -> None:
        """Test that various branch name formats are accepted."""
        branch_names = [
            "feature/new-feature",
            "hotfix/urgent-fix",
            "bugfix/issue-123",
            "chore/update-dependencies",
            "feat/user-authentication_v2",
            "fix/memory-leak.2024-01-15",
            "main",
            "develop",
            "release/v1.2.3",
            "user-branch",
            "CAPS-BRANCH",
            "123-numeric-start",
        ]

        for branch_name in branch_names:
            input_data = {
                "branch_name": branch_name,
                "repo_path": "/test/repo",
            }

            model = PrDescriptionWorkflowInput(**input_data)
            assert model.branch_name == branch_name

    def test_various_repo_path_formats(self) -> None:
        """Test that various repository path formats are accepted."""
        repo_paths = [
            "/absolute/path/to/repo",
            "./relative/path",
            "../parent/directory/repo",
            "~/home/user/repo",
            "/home/user/projects/my-awesome-project",
            "C:\\Windows\\Path\\To\\Repo",  # Windows path
            "/opt/temporary-repo",
            ".",  # Current directory
            "..",  # Parent directory
            "simple-repo-name",
        ]

        for repo_path in repo_paths:
            input_data = {
                "branch_name": "test-branch",
                "repo_path": repo_path,
            }

            model = PrDescriptionWorkflowInput(**input_data)
            assert model.repo_path == repo_path

    def test_various_base_branch_formats(self) -> None:
        """Test that various base branch formats are accepted."""
        base_branches = [
            "main",
            "master",
            "develop",
            "dev",
            "staging",
            "production",
            "release/v1.0",
            "hotfix/critical",
            "feature/base-feature",
            "",  # Empty string
        ]

        for base_branch in base_branches:
            input_data = {
                "branch_name": "test-branch",
                "repo_path": "/test/repo",
                "base_branch": base_branch,
            }

            model = PrDescriptionWorkflowInput(**input_data)
            assert model.base_branch == base_branch

    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"branch_name": None, "repo_path": "/test"},
            {"branch_name": "test", "repo_path": None},
            {"branch_name": 123, "repo_path": "/test"},
            {"branch_name": "test", "repo_path": 123},
            {"branch_name": [], "repo_path": "/test"},
            {"branch_name": "test", "repo_path": []},
            {"branch_name": {}, "repo_path": "/test"},
            {"branch_name": "test", "repo_path": {}},
        ],
    )
    def test_invalid_field_types(self, invalid_data: dict[str, Any]) -> None:
        """Test various invalid field types."""
        with pytest.raises(ValidationError):
            PrDescriptionWorkflowInput(**invalid_data)

    def test_model_serialization(self) -> None:
        """Test that model can be serialized to dict."""
        input_data = {
            "branch_name": "feature/serialization-test",
            "repo_path": "/path/to/my/repo",
            "base_branch": "develop",
        }

        model = PrDescriptionWorkflowInput(**input_data)
        serialized = model.model_dump()

        assert serialized == input_data
        assert isinstance(serialized, dict)

    def test_model_serialization_with_defaults(self) -> None:
        """Test serialization includes default values."""
        input_data = {
            "branch_name": "feature/test",
            "repo_path": "/test/repo",
        }

        model = PrDescriptionWorkflowInput(**input_data)
        serialized = model.model_dump()

        expected = {
            "branch_name": "feature/test",
            "repo_path": "/test/repo",
            "base_branch": "main",  # Default value included
        }
        assert serialized == expected

    def test_model_json_serialization(self) -> None:
        """Test that model can be serialized to JSON."""
        input_data = {
            "branch_name": "feature/json-test",
            "repo_path": "/json/test/repo",
            "base_branch": "staging",
        }

        model = PrDescriptionWorkflowInput(**input_data)
        json_str = model.model_dump_json()

        assert isinstance(json_str, str)
        assert "feature/json-test" in json_str
        assert "/json/test/repo" in json_str
        assert "staging" in json_str

    def test_model_equality(self) -> None:
        """Test that two models with same data are equal."""
        input_data = {
            "branch_name": "feature/equality-test",
            "repo_path": "/equality/test/repo",
            "base_branch": "develop",
        }

        model1 = PrDescriptionWorkflowInput(**input_data)
        model2 = PrDescriptionWorkflowInput(**input_data)

        assert model1 == model2

    def test_model_inequality(self) -> None:
        """Test that two models with different data are not equal."""
        input_data1 = {
            "branch_name": "feature/test1",
            "repo_path": "/test/repo1",
        }

        input_data2 = {
            "branch_name": "feature/test2",
            "repo_path": "/test/repo2",
        }

        model1 = PrDescriptionWorkflowInput(**input_data1)
        model2 = PrDescriptionWorkflowInput(**input_data2)

        assert model1 != model2

    def test_model_inequality_different_base_branch(self) -> None:
        """Test inequality when only base_branch differs."""
        base_data = {
            "branch_name": "feature/test",
            "repo_path": "/test/repo",
        }

        model1 = PrDescriptionWorkflowInput(**base_data, base_branch="main")
        model2 = PrDescriptionWorkflowInput(**base_data, base_branch="develop")

        assert model1 != model2

    def test_model_field_access(self) -> None:
        """Test that model fields can be accessed as attributes."""
        model = PrDescriptionWorkflowInput(
            branch_name="feature/access-test",
            repo_path="/access/test/repo",
            base_branch="custom-base",
        )

        assert model.branch_name == "feature/access-test"
        assert model.repo_path == "/access/test/repo"
        assert model.base_branch == "custom-base"

    def test_model_immutability(self) -> None:
        """Test that model fields are immutable after creation."""
        model = PrDescriptionWorkflowInput(
            branch_name="feature/immutable-test",
            repo_path="/immutable/test",
        )

        # Pydantic models are mutable by default, but we can test the current values
        original_branch = model.branch_name
        original_repo = model.repo_path
        original_base = model.base_branch

        # Values should remain as set
        assert model.branch_name == original_branch
        assert model.repo_path == original_repo
        assert model.base_branch == original_base

    def test_model_with_special_characters(self) -> None:
        """Test model handles special characters in field values."""
        input_data = {
            "branch_name": "feature/fix-issue-#123_with_special@chars",
            "repo_path": "/path/to/repo with spaces & symbols!",
            "base_branch": "release/v2.1.0-beta.1",
        }

        model = PrDescriptionWorkflowInput(**input_data)

        assert model.branch_name == "feature/fix-issue-#123_with_special@chars"
        assert model.repo_path == "/path/to/repo with spaces & symbols!"
        assert model.base_branch == "release/v2.1.0-beta.1"

    def test_model_with_unicode_characters(self) -> None:
        """Test model handles Unicode characters."""
        input_data = {
            "branch_name": "feature/支持中文-branch",
            "repo_path": "/path/to/项目/repo",
            "base_branch": "développement",
        }

        model = PrDescriptionWorkflowInput(**input_data)

        assert model.branch_name == "feature/支持中文-branch"
        assert model.repo_path == "/path/to/项目/repo"
        assert model.base_branch == "développement"

    def test_model_with_very_long_strings(self) -> None:
        """Test model handles very long string values."""
        long_branch = "feature/" + "very-long-branch-name" * 10  # 200+ characters
        long_path = "/very/long/path/" + "directory/" * 20  # 200+ characters
        long_base = "very-long-base-branch-name" * 5  # 125+ characters

        input_data = {
            "branch_name": long_branch,
            "repo_path": long_path,
            "base_branch": long_base,
        }

        model = PrDescriptionWorkflowInput(**input_data)

        assert model.branch_name == long_branch
        assert model.repo_path == long_path
        assert model.base_branch == long_base

    def test_model_deserialization_from_dict(self) -> None:
        """Test that model can be created from dictionary (deserialization)."""
        data_dict = {
            "branch_name": "feature/deserialization",
            "repo_path": "/deserialize/test",
            "base_branch": "master",
        }

        # Test model creation from dict
        model = PrDescriptionWorkflowInput(**data_dict)
        assert model.branch_name == "feature/deserialization"

        # Test round-trip serialization/deserialization
        serialized = model.model_dump()
        model_copy = PrDescriptionWorkflowInput(**serialized)
        assert model == model_copy
