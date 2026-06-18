"""Unit tests for GitHub PR description workflow input model."""

from typing import Any

import pytest
from pydantic import ValidationError

from cookbook.recipes.workflows.github_pr_description.models.github_pr_description_workflow_input import (
    GitHubPrDescriptionWorkflowInput,
)


class TestGitHubPrDescriptionWorkflowInput:
    """Test cases for GitHubPrDescriptionWorkflowInput model."""

    def test_required_fields_valid(self) -> None:
        """Test that model can be created with only required fields."""
        input_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 123,
        }

        model = GitHubPrDescriptionWorkflowInput(**input_data)

        assert model.owner == "test-owner"
        assert model.repo == "test-repo"
        assert model.pull_number == 123
        assert model.base_branch == ""  # Default value
        assert model.branch_name == ""  # Default value

    def test_all_fields_valid(self) -> None:
        """Test that model can be created with all fields provided."""
        input_data = {
            "owner": "acme-corp",
            "repo": "awesome-project",
            "pull_number": 456,
            "base_branch": "main",
            "branch_name": "feature/new-feature",
        }

        model = GitHubPrDescriptionWorkflowInput(**input_data)

        assert model.owner == "acme-corp"
        assert model.repo == "awesome-project"
        assert model.pull_number == 456
        assert model.base_branch == "main"
        assert model.branch_name == "feature/new-feature"

    def test_missing_required_owner_field(self) -> None:
        """Test that ValidationError is raised when owner field is missing."""
        input_data = {
            "repo": "test-repo",
            "pull_number": 123,
        }

        with pytest.raises(ValidationError) as exc_info:
            GitHubPrDescriptionWorkflowInput(**input_data)

        assert "owner" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)

    def test_missing_required_repo_field(self) -> None:
        """Test that ValidationError is raised when repo field is missing."""
        input_data = {
            "owner": "test-owner",
            "pull_number": 123,
        }

        with pytest.raises(ValidationError) as exc_info:
            GitHubPrDescriptionWorkflowInput(**input_data)

        assert "repo" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)

    def test_missing_required_pull_number_field(self) -> None:
        """Test that ValidationError is raised when pull_number field is missing."""
        input_data = {
            "owner": "test-owner",
            "repo": "test-repo",
        }

        with pytest.raises(ValidationError) as exc_info:
            GitHubPrDescriptionWorkflowInput(**input_data)

        assert "pull_number" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)

    def test_invalid_pull_number_type(self) -> None:
        """Test that ValidationError is raised for invalid pull_number type."""
        input_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": "not-a-number",
        }

        with pytest.raises(ValidationError) as exc_info:
            GitHubPrDescriptionWorkflowInput(**input_data)

        assert "pull_number" in str(exc_info.value)
        assert "Input should be a valid integer" in str(exc_info.value)

    def test_negative_pull_number(self) -> None:
        """Test that negative pull numbers are accepted (validation is lenient)."""
        input_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": -1,
        }

        # The model doesn't validate pull number range, so this should pass
        model = GitHubPrDescriptionWorkflowInput(**input_data)
        assert model.pull_number == -1

    def test_zero_pull_number(self) -> None:
        """Test that zero pull number is accepted."""
        input_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 0,
        }

        model = GitHubPrDescriptionWorkflowInput(**input_data)
        assert model.pull_number == 0

    def test_string_fields_validation(self) -> None:
        """Test that string fields accept various string values."""
        input_data = {
            "owner": "user-with-dashes_and_underscores123",
            "repo": "repo.with.dots-and-dashes_123",
            "pull_number": 999,
            "base_branch": "feature/complex-branch-name_v2.1",
            "branch_name": "hotfix/urgent_fix-2024.01",
        }

        model = GitHubPrDescriptionWorkflowInput(**input_data)

        assert model.owner == "user-with-dashes_and_underscores123"
        assert model.repo == "repo.with.dots-and-dashes_123"
        assert model.base_branch == "feature/complex-branch-name_v2.1"
        assert model.branch_name == "hotfix/urgent_fix-2024.01"

    def test_empty_string_optional_fields(self) -> None:
        """Test that optional fields can be explicitly set to empty strings."""
        input_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 123,
            "base_branch": "",
            "branch_name": "",
        }

        model = GitHubPrDescriptionWorkflowInput(**input_data)

        assert model.base_branch == ""
        assert model.branch_name == ""

    def test_model_serialization(self) -> None:
        """Test that model can be serialized to dict."""
        input_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 123,
            "base_branch": "main",
            "branch_name": "feature/test",
        }

        model = GitHubPrDescriptionWorkflowInput(**input_data)
        serialized = model.model_dump()

        assert serialized == input_data
        assert isinstance(serialized, dict)

    def test_model_json_serialization(self) -> None:
        """Test that model can be serialized to JSON."""
        input_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 123,
        }

        model = GitHubPrDescriptionWorkflowInput(**input_data)
        json_str = model.model_dump_json()

        assert isinstance(json_str, str)
        assert "test-owner" in json_str
        assert "test-repo" in json_str
        assert "123" in json_str

    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"owner": None, "repo": "test", "pull_number": 1},
            {"owner": "test", "repo": None, "pull_number": 1},
            {"owner": "test", "repo": "test", "pull_number": None},
            {"owner": 123, "repo": "test", "pull_number": 1},
            {"owner": "test", "repo": 123, "pull_number": 1},
        ],
    )
    def test_invalid_field_types(self, invalid_data: dict[str, Any]) -> None:
        """Test various invalid field types."""
        with pytest.raises(ValidationError):
            GitHubPrDescriptionWorkflowInput(**invalid_data)

    def test_field_descriptions(self) -> None:
        """Test that field descriptions are properly defined."""
        fields = GitHubPrDescriptionWorkflowInput.model_fields

        assert "owner" in fields
        assert "GitHub org/username" in fields["owner"].description

        assert "repo" in fields
        assert "Repository name" in fields["repo"].description

        assert "pull_number" in fields
        assert "PR number" in fields["pull_number"].description

        assert "base_branch" in fields
        assert "Base branch" in fields["base_branch"].description

        assert "branch_name" in fields
        assert "Head branch" in fields["branch_name"].description

    def test_model_equality(self) -> None:
        """Test that two models with same data are equal."""
        input_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pull_number": 123,
        }

        model1 = GitHubPrDescriptionWorkflowInput(**input_data)
        model2 = GitHubPrDescriptionWorkflowInput(**input_data)

        assert model1 == model2

    def test_model_inequality(self) -> None:
        """Test that two models with different data are not equal."""
        input_data1 = {
            "owner": "test-owner1",
            "repo": "test-repo",
            "pull_number": 123,
        }

        input_data2 = {
            "owner": "test-owner2",
            "repo": "test-repo",
            "pull_number": 123,
        }

        model1 = GitHubPrDescriptionWorkflowInput(**input_data1)
        model2 = GitHubPrDescriptionWorkflowInput(**input_data2)

        assert model1 != model2
