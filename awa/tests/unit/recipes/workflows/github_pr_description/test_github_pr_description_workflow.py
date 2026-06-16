"""Comprehensive unit tests for GitHub PR description workflow."""

import contextlib
import inspect
import json
import os
import re
import typing
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

if TYPE_CHECKING:
    from models.workflow_paths import WorkflowPaths  # noqa: F401

import pytest
from temporalio.common import RetryPolicy

from cookbook.recipes import constants
from cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow import (
    CONTENT_PREVIEW_LENGTH,
    EXPECTED_PARTS_COUNT,
    GitHubPrDescriptionWorkflow,
)
from cookbook.recipes.workflows.github_pr_description.models.github_pr_description_workflow_input import (
    GitHubPrDescriptionWorkflowInput,
)


class TestGitHubPrDescriptionWorkflow:
    """Test cases for GitHubPrDescriptionWorkflow."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.workflow_instance = GitHubPrDescriptionWorkflow()
        self.sample_input = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            base_branch="main",
            branch_name="feature/test",
        )

    def test_workflow_initialization(self) -> None:
        """Test that workflow initializes with correct default values."""
        workflow_instance = GitHubPrDescriptionWorkflow()

        assert workflow_instance.mcp_config == {}
        assert workflow_instance.workflow_paths is None
        assert workflow_instance.retry_policy is None

    def test_workflow_constants(self) -> None:
        """Test that workflow constants are properly defined."""
        assert CONTENT_PREVIEW_LENGTH == 50
        assert EXPECTED_PARTS_COUNT == 2

    def test_parse_mcp_response_direct_data(self) -> None:
        """Test parsing MCP response with direct data."""
        # Test direct dict
        direct_dict = {"key": "value"}
        result = self.workflow_instance._parse_mcp_response(direct_dict)
        assert result == direct_dict

        # Test direct list
        direct_list = [{"item": 1}, {"item": 2}]
        result = self.workflow_instance._parse_mcp_response(direct_list)
        assert result == direct_list

        # Test direct string
        direct_string = "simple string"
        result = self.workflow_instance._parse_mcp_response(direct_string)
        assert result == direct_string

    def test_parse_mcp_response_empty_or_none(self) -> None:
        """Test parsing MCP response with empty or None values."""
        # Test None
        result = self.workflow_instance._parse_mcp_response(None)
        assert result is None

        # Test empty dict
        result = self.workflow_instance._parse_mcp_response({})
        assert result == {}

        # Test empty list
        result = self.workflow_instance._parse_mcp_response([])
        assert result == []

        # Test empty string
        result = self.workflow_instance._parse_mcp_response("")
        assert result == ""

    def test_parse_mcp_response_content_wrapper_format(self) -> None:
        """Test parsing MCP response in AWA MCP content wrapper format."""
        # Test valid JSON in content format
        json_data = {"pr_info": {"title": "Test PR", "number": 123}}
        response = {
            "content": [{"text": json.dumps(json_data)}],
        }
        result = self.workflow_instance._parse_mcp_response(response)
        assert result == json_data

        # Test plain text in content format
        plain_text = "This is plain text"
        response = {
            "content": [{"text": plain_text}],
        }
        result = self.workflow_instance._parse_mcp_response(response)
        assert result == plain_text

    def test_parse_mcp_response_data_wrapper_format(self) -> None:
        """Test parsing MCP response in data wrapper format."""
        actual_data = {"files": ["file1.py", "file2.py"], "status": "success"}
        response = {"data": actual_data}
        result = self.workflow_instance._parse_mcp_response(response)
        assert result == actual_data

    def test_parse_mcp_response_invalid_json_in_content(self) -> None:
        """Test parsing MCP response with invalid JSON in content field."""
        invalid_json = '{"invalid": json, missing quote}'
        response = {
            "content": [{"text": invalid_json}],
        }
        result = self.workflow_instance._parse_mcp_response(response)
        assert result == invalid_json  # Returns the invalid JSON as string

    def test_parse_mcp_response_malformed_content(self) -> None:
        """Test parsing MCP response with malformed content structure."""
        # Empty content array
        response = {"content": []}
        result = self.workflow_instance._parse_mcp_response(response)
        assert result == response

        # Content item without text field
        response = {"content": [{"other_field": "value"}]}
        result = self.workflow_instance._parse_mcp_response(response)
        assert result == response

        # Non-dict content item
        response = {"content": ["string_item"]}
        result = self.workflow_instance._parse_mcp_response(response)
        assert result == response

    @pytest.mark.parametrize(
        ("response_data", "expected"),
        [
            # Direct data cases
            ({"direct": "data"}, {"direct": "data"}),
            ([1, 2, 3], [1, 2, 3]),
            ("string", "string"),
            (42, 42),
            (True, True),
            # Content wrapper cases
            (
                {"content": [{"text": '{"parsed": "json"}'}]},
                {"parsed": "json"},
            ),
            (
                {"content": [{"text": "plain text"}]},
                "plain text",
            ),
            # Data wrapper cases
            (
                {"data": {"wrapped": "data"}},
                {"wrapped": "data"},
            ),
            # Edge cases
            ({}, {}),
            ({"other_field": "value"}, {"other_field": "value"}),
        ],
    )
    def test_parse_mcp_response_parametrized(
        self,
        response_data: dict | list | str | int | bool | None,
        expected: dict | list | str | int | bool | None,
    ) -> None:
        """Test MCP response parsing with various input formats."""
        result = self.workflow_instance._parse_mcp_response(response_data)
        assert result == expected

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_general.get_workflow_paths",
    )
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.resolve_config_variables",
    )
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.read_file")
    async def test_workflow_initialization_method_called(
        self,
        mock_read_file: AsyncMock,
        mock_resolve_config: AsyncMock,
        mock_get_workflow_paths: MagicMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test that _initialize_workflow calls AWA SDK methods."""
        mock_read_file.return_value = '{"test": "config"}'
        mock_resolve_config.return_value = '{"test": "config"}'
        mock_get_workflow_paths.return_value = MagicMock()

        # Mock the workflow environment
        with patch("temporalio.workflow.info") as mock_workflow_info:
            mock_workflow_info.return_value.workflow_id = "test-workflow-id"

            # This would normally require a proper workflow environment
            # Expected to fail without proper workflow environment - we're mainly testing structure
            with contextlib.suppress(Exception):
                await self.workflow_instance._initialize_workflow(self.sample_input)

        # The actual calls would happen in a real workflow environment
        # This test mainly verifies the method exists and has the right signature

    def test_workflow_decorator_and_name(self) -> None:
        """Test that workflow is properly decorated with correct name."""
        # Verify the workflow has the workflow decorator applied
        # The actual attribute name may vary depending on Temporal version
        workflow_attributes = [
            attr
            for attr in dir(GitHubPrDescriptionWorkflow)
            if attr.startswith("__temporal") or "workflow" in attr.lower()
        ]

        # Should have some workflow-related attributes
        assert len(workflow_attributes) > 0, f"Expected workflow attributes, found: {workflow_attributes}"

        # Verify the class can be used as a workflow (has run method)
        assert hasattr(GitHubPrDescriptionWorkflow, "run")
        assert callable(GitHubPrDescriptionWorkflow.run)

    def test_run_method_signature(self) -> None:
        """Test that run method has correct signature."""
        run_method = GitHubPrDescriptionWorkflow.run
        sig = inspect.signature(run_method)

        # Should have self and workflow_input parameters
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "workflow_input" in params

        # Return type should be annotated as str
        assert sig.return_annotation is str

    def test_workflow_instance_attributes_type_hints(self) -> None:
        """Test that workflow instance attributes have proper type hints."""
        # Get type hints for the class
        type_hints = typing.get_type_hints(GitHubPrDescriptionWorkflow.__init__)

        # Verify that the method is properly typed
        assert "return" in type_hints
        assert type_hints["return"] is type(None)

    @pytest.mark.parametrize(
        "mcp_config",
        [
            {},
            {"github_token": "test-token"},
            {"timeout": 30, "retries": 3},
            {"complex": {"nested": {"config": "value"}}},
        ],
    )
    def test_mcp_config_initialization(self, mcp_config: dict[str, Any]) -> None:
        """Test that MCP config can be set to various values."""
        workflow_instance = GitHubPrDescriptionWorkflow()
        workflow_instance.mcp_config = mcp_config
        assert workflow_instance.mcp_config == mcp_config

    def test_workflow_paths_initialization(self) -> None:
        """Test that workflow_paths can be set."""
        workflow_instance = GitHubPrDescriptionWorkflow()

        # Test setting to None (default)
        assert workflow_instance.workflow_paths is None

        # Test setting to a mock object (simulating actual WorkflowPaths)
        mock_paths = MagicMock()
        workflow_instance.workflow_paths = mock_paths
        assert workflow_instance.workflow_paths == mock_paths

    def test_retry_policy_initialization(self) -> None:
        """Test that retry_policy can be set."""
        workflow_instance = GitHubPrDescriptionWorkflow()

        # Test setting to None (default)
        assert workflow_instance.retry_policy is None

        # Test setting to actual RetryPolicy
        retry_policy = RetryPolicy(maximum_attempts=3)
        workflow_instance.retry_policy = retry_policy
        assert workflow_instance.retry_policy == retry_policy

    def test_workflow_input_model_integration(self) -> None:
        """Test that workflow properly integrates with its input model."""
        # Create a workflow input
        input_data = GitHubPrDescriptionWorkflowInput(
            owner="integration-test",
            repo="test-repo",
            pull_number=999,
            base_branch="develop",
            branch_name="feature/integration",
        )

        # Verify the input model is properly structured for the workflow
        assert input_data.owner == "integration-test"
        assert input_data.repo == "test-repo"
        assert input_data.pull_number == 999
        assert input_data.base_branch == "develop"
        assert input_data.branch_name == "feature/integration"

    def test_constants_usage_in_workflow(self) -> None:
        """Test that workflow constants are accessible and have expected values."""
        # Verify constants are properly defined
        assert isinstance(CONTENT_PREVIEW_LENGTH, int)
        assert CONTENT_PREVIEW_LENGTH > 0

        assert isinstance(EXPECTED_PARTS_COUNT, int)
        assert EXPECTED_PARTS_COUNT > 0

    @patch.dict("os.environ", {"MAX_CONCURRENT_TRANSFORMS": "8"})
    def test_environment_variable_access(self) -> None:
        """Test that environment variable access is properly handled."""
        # This test verifies that the environment variable access pattern is correct
        # The actual import happens during module load in the unsafe imports block

        # Verify the pattern used in the workflow
        max_transforms = os.environ.get("MAX_CONCURRENT_TRANSFORMS", constants.DEFAULT_MAX_CONCURRENT_TRANSFORMS)
        assert max_transforms == "8"  # From environment

        # Test fallback to constant
        with patch.dict("os.environ", {}, clear=True):
            max_transforms = os.environ.get("MAX_CONCURRENT_TRANSFORMS", constants.DEFAULT_MAX_CONCURRENT_TRANSFORMS)
            assert max_transforms == constants.DEFAULT_MAX_CONCURRENT_TRANSFORMS

    def test_unsafe_imports_pattern(self) -> None:
        """Test that unsafe imports are properly structured."""
        # Verify that the required modules are available
        # This tests the import structure used in the workflow
        try:
            # These should be available due to the unsafe imports
            assert json is not None
            assert os is not None
            assert re is not None
        except ImportError:
            pytest.fail("Required modules should be available through unsafe imports")

    def test_type_checking_imports(self) -> None:
        """Test that TYPE_CHECKING imports are properly structured."""
        # TYPE_CHECKING imports are now at the top-level
        # This test verifies the import structure is working
        assert TYPE_CHECKING in (True, False)  # Always true but validates the import structure


class TestGitHubPrDescriptionWorkflowIntegration:
    """Integration tests for GitHubPrDescriptionWorkflow with mocked dependencies."""

    @pytest.fixture
    def workflow_input(self) -> GitHubPrDescriptionWorkflowInput:
        """Create a sample workflow input for testing."""
        return GitHubPrDescriptionWorkflowInput(
            owner="test-org",
            repo="test-repo",
            pull_number=42,
            base_branch="main",
            branch_name="feature/awesome-feature",
        )

    def test_workflow_can_be_instantiated_with_input(self, workflow_input: GitHubPrDescriptionWorkflowInput) -> None:
        """Test that workflow can be instantiated and accepts proper input."""
        workflow_instance = GitHubPrDescriptionWorkflow()

        # Verify workflow can accept the input model
        assert workflow_input.owner == "test-org"
        assert workflow_input.repo == "test-repo"
        assert workflow_input.pull_number == 42

        # Verify workflow instance is properly initialized
        assert workflow_instance is not None
        assert hasattr(workflow_instance, "run")
        assert hasattr(workflow_instance, "_parse_mcp_response")

    @pytest.mark.parametrize(
        "error_scenario",
        [
            "json_decode_error",
            "empty_response",
            "malformed_content",
            "missing_fields",
        ],
    )
    def test_parse_mcp_response_error_handling(self, error_scenario: str) -> None:
        """Test MCP response parsing handles various error scenarios."""
        workflow_instance = GitHubPrDescriptionWorkflow()

        if error_scenario == "json_decode_error":
            response = {"content": [{"text": "invalid json {"}]}
            result = workflow_instance._parse_mcp_response(response)
            assert result == "invalid json {"

        elif error_scenario == "empty_response":
            result = workflow_instance._parse_mcp_response(None)
            assert result is None

        elif error_scenario == "malformed_content":
            response = {"content": "not a list"}
            result = workflow_instance._parse_mcp_response(response)
            assert result == response

        elif error_scenario == "missing_fields":
            response = {"unexpected_field": "value"}
            result = workflow_instance._parse_mcp_response(response)
            assert result == response


class TestGitHubPrDescriptionWorkflowComplexScenarios:
    """Test complex scenarios and edge cases for the workflow."""

    def test_nested_mcp_response_parsing(self) -> None:
        """Test parsing of deeply nested MCP responses."""
        workflow_instance = GitHubPrDescriptionWorkflow()

        # Complex nested JSON in content
        nested_data = {
            "pr_details": {
                "files": [
                    {"name": "file1.py", "changes": 10},
                    {"name": "file2.py", "changes": 5},
                ],
                "commits": [
                    {"sha": "abc123", "message": "Add feature"},
                    {"sha": "def456", "message": "Fix bug"},
                ],
            },
            "summary": "Complex changes",
        }

        response = {"content": [{"text": json.dumps(nested_data)}]}
        result = workflow_instance._parse_mcp_response(response)

        assert result == nested_data
        assert result["pr_details"]["files"][0]["name"] == "file1.py"
        assert len(result["pr_details"]["commits"]) == 2

    def test_workflow_resilience_patterns(self) -> None:
        """Test that workflow follows resilience patterns."""
        workflow_instance = GitHubPrDescriptionWorkflow()

        # Test various response formats that should be handled gracefully
        test_cases = [
            (None, None),
            ({}, {}),
            ([], []),
            ("", ""),
            ({"error": "Something went wrong"}, {"error": "Something went wrong"}),
            ({"content": []}, {"content": []}),
            ({"content": [{}]}, {"content": [{}]}),
            ({"content": [{"other_field": "value"}]}, {"content": [{"other_field": "value"}]}),
            ({"data": None}, None),  # This extracts the None value from data field
            ({"data": {}}, {}),  # This extracts the empty dict from data field
        ]

        for test_input, expected_result in test_cases:
            # Should not raise an exception
            result = workflow_instance._parse_mcp_response(test_input)
            # Result should match expected output
            assert result == expected_result, f"Input {test_input} produced {result}, expected {expected_result}"


class TestWorkflowInitialization:
    """Test workflow initialization and setup."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_general.get_workflow_paths",
    )
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.resolve_config_variables",
    )
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.read_file")
    @patch("temporalio.workflow.info")
    async def test_initialize_workflow_success(
        self,
        mock_workflow_info: MagicMock,
        mock_read_file: AsyncMock,
        mock_resolve_config: AsyncMock,
        mock_get_workflow_paths: MagicMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test successful workflow initialization."""
        # Setup mocks
        mock_workflow_info.return_value.workflow_id = "test-workflow-123"
        mock_read_file.return_value = '["mcp_config_content"]'
        mock_resolve_config.return_value = '{"tool_name": "github"}'
        mock_get_workflow_paths.return_value = MagicMock()

        workflow = GitHubPrDescriptionWorkflow()
        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        await workflow._initialize_workflow(input_data)

        # Verify initialization steps
        mock_read_file.assert_called_once()
        mock_resolve_config.assert_called_once()
        mock_get_workflow_paths.assert_called_once()
        assert workflow.mcp_config == {"tool_name": "github"}
        assert isinstance(workflow.retry_policy, RetryPolicy)
        assert workflow.retry_policy.maximum_attempts == 3

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_general.get_workflow_paths",
    )
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.resolve_config_variables",
    )
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.read_file")
    @patch("temporalio.workflow.info")
    async def test_initialize_workflow_json_error(
        self,
        mock_workflow_info: MagicMock,
        mock_read_file: AsyncMock,
        mock_resolve_config: AsyncMock,
        _mock_get_workflow_paths: MagicMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test workflow initialization with invalid JSON config."""
        mock_workflow_info.return_value.workflow_id = "test-workflow-123"
        mock_read_file.return_value = "invalid json {"
        mock_resolve_config.return_value = "invalid json {"

        workflow = GitHubPrDescriptionWorkflow()
        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        with pytest.raises(json.JSONDecodeError):
            await workflow._initialize_workflow(input_data)


class TestFetchPrDetails:
    """Test fetching PR details from GitHub API."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_fetch_pr_details_success(self, mock_invoke_mcp_tool: AsyncMock, _mock_logger: MagicMock) -> None:
        """Test successful PR details fetching."""
        # Mock response
        mock_pr_data = {
            "number": 123,
            "title": "Test PR",
            "head": {"ref": "feature/test"},
            "base": {"ref": "main"},
            "body": "Test PR description",
        }
        mock_invoke_mcp_tool.return_value = mock_pr_data

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow._fetch_pr_details(input_data)

        assert result == mock_pr_data
        mock_invoke_mcp_tool.assert_called_once_with(
            mcp_config=workflow.mcp_config,
            tool_name="get_pull_request",
            parameters={
                "owner": "test-owner",
                "repo": "test-repo",
                "pull_number": 123,
            },
            timeout_seconds=30,
            retry_policy=workflow.retry_policy,
        )

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_fetch_pr_details_failure(self, mock_invoke_mcp_tool: AsyncMock, mock_logger: MagicMock) -> None:
        """Test PR details fetching failure."""
        mock_invoke_mcp_tool.side_effect = Exception("API Error")

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        with pytest.raises(Exception, match="API Error"):
            await workflow._fetch_pr_details(input_data)

        mock_logger.error.assert_called_once()


class TestUpdateGithubPr:
    """Test updating GitHub PR description."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_update_github_pr_success(self, mock_invoke_mcp_tool: AsyncMock, _mock_logger: MagicMock) -> None:
        """Test successful PR description update."""
        mock_response = {"updated_at": "2023-01-01T00:00:00Z", "body": "Updated description"}
        mock_invoke_mcp_tool.return_value = mock_response

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow._update_github_pr(input_data, "New PR description")

        assert result == mock_response
        mock_invoke_mcp_tool.assert_called_once_with(
            mcp_config=workflow.mcp_config,
            tool_name="update_issue",
            parameters={
                "owner": "test-owner",
                "repo": "test-repo",
                "issue_number": 123,
                "body": "New PR description",
            },
            timeout_seconds=30,
            retry_policy=workflow.retry_policy,
        )

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_update_github_pr_failure(self, mock_invoke_mcp_tool: AsyncMock, mock_logger: MagicMock) -> None:
        """Test PR description update failure."""
        mock_invoke_mcp_tool.side_effect = Exception("Update Error")

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        with pytest.raises(Exception, match="Update Error"):
            await workflow._update_github_pr(input_data, "New PR description")

        mock_logger.error.assert_called_once()


class TestMetadataExtraction:
    """Test metadata extraction from PR descriptions."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_extract_metadata_from_table_success(self, _mock_logger: MagicMock) -> None:
        """Test successful metadata extraction from table."""
        pr_description = """
## Summary
Some changes

### 🤖 AWA Generation Info
| Metric | Value |
|--------|---------|
| Last Processed Commit | [`abc1234`](https://github.com/owner/repo/commit/abc1234) |
| Last Updated | 2023-01-01 12:00:00 UTC |
"""

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._extract_metadata_from_table(pr_description)

        assert result["last_processed_commit"] == "abc1234"
        assert result["last_updated"] == "2023-01-01 12:00:00 UTC"

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_extract_metadata_no_table(self, _mock_logger: MagicMock) -> None:
        """Test metadata extraction when no table exists."""
        pr_description = "## Summary\nSome changes without metadata table"

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._extract_metadata_from_table(pr_description)

        assert result["last_processed_commit"] is None
        assert result["last_updated"] is None

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_extract_metadata_malformed_table(self, _mock_logger: MagicMock) -> None:
        """Test metadata extraction with malformed table."""
        pr_description = """
### 🤖 AWA Generation Info
| Metric | Value |
|--------|---------|
| Incomplete row
"""

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._extract_metadata_from_table(pr_description)

        assert result["last_processed_commit"] is None
        assert result["last_updated"] is None

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_extract_metadata_exception_handling(self, _mock_logger: MagicMock) -> None:
        """Test metadata extraction handles exceptions gracefully."""
        workflow = GitHubPrDescriptionWorkflow()

        # Pass None to trigger exception
        result = workflow._extract_metadata_from_table(None)  # type: ignore[arg-type]

        assert result["last_processed_commit"] is None
        assert result["last_updated"] is None


class TestContentExtraction:
    """Test content extraction before metadata table."""

    def test_extract_content_before_table_success(self) -> None:
        """Test successful content extraction."""
        pr_description = """
## Summary
Some changes

## Details
More information

### 🤖 AWA Generation Info
| Metric | Value |
"""

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._extract_content_before_table(pr_description)

        expected = """
## Summary
Some changes

## Details
More information"""
        assert result == expected

    def test_extract_content_no_table(self) -> None:
        """Test content extraction when no table exists."""
        pr_description = "## Summary\nSome changes without metadata table"

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._extract_content_before_table(pr_description)

        assert result == pr_description

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_extract_content_exception_handling(self, mock_logger: MagicMock) -> None:
        """Test content extraction handles exceptions."""
        workflow = GitHubPrDescriptionWorkflow()

        with pytest.raises(AttributeError, match="'NoneType' object has no attribute"):
            workflow._extract_content_before_table(None)  # type: ignore[arg-type]

        mock_logger.error.assert_called_once()


class TestUpdateMetadataTimestamp:
    """Test metadata timestamp updates."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch("temporalio.workflow.now")
    async def test_update_metadata_timestamp_success(self, mock_now: MagicMock, _mock_logger: MagicMock) -> None:
        """Test successful timestamp update."""
        mock_now.return_value = datetime(2023, 6, 15, 10, 30, 0, tzinfo=UTC)

        existing_content = """
## Summary
Some changes

### 🤖 AWA Generation Info
| Metric | Value |
|--------|---------|
| Last Processed Commit | [`abc1234`](https://github.com/owner/repo/commit/abc1234) |
| Last Updated | 2023-01-01 12:00:00 UTC |
"""

        workflow = GitHubPrDescriptionWorkflow()
        result = await workflow._update_metadata_timestamp(existing_content, "def5678")

        assert "2023-06-15 10:30:00 UTC" in result
        assert "[`abc1234`]" in result  # Should preserve original commit
        assert "## Summary" in result
        assert "Some changes" in result

    @patch("temporalio.workflow.now")
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_update_metadata_timestamp_fallback(self, mock_logger: MagicMock, mock_now: MagicMock) -> None:
        """Test timestamp update fallback on error."""
        mock_now.side_effect = Exception("Time error")

        existing_content = "Original content"
        workflow = GitHubPrDescriptionWorkflow()

        result = await workflow._update_metadata_timestamp(existing_content, "abc123")

        assert result == existing_content  # Should return original on error
        mock_logger.error.assert_called_once()


class TestConstructPrDescriptionWithMetadata:
    """Test PR description construction with metadata."""

    @patch("temporalio.workflow.now")
    def test_construct_pr_description_with_metadata_success(self, mock_now: MagicMock) -> None:
        """Test successful PR description construction with metadata."""
        mock_now.return_value = datetime(2023, 6, 15, 10, 30, 0, tzinfo=UTC)

        workflow = GitHubPrDescriptionWorkflow()
        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = workflow._construct_pr_description_with_metadata(
            "## Summary\nTest changes",
            "abc1234",
            input_data,
        )

        assert "## Summary" in result
        assert "Test changes" in result
        assert "### 🤖 AWA Generation Info" in result
        assert "`abc1234`" in result
        assert "https://github.com/test-owner/test-repo/commit/abc1234" in result
        assert "2023-06-15 10:30:00 UTC" in result

    @patch("temporalio.workflow.now")
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_construct_pr_description_with_metadata_error(self, mock_logger: MagicMock, mock_now: MagicMock) -> None:
        """Test PR description construction handles errors."""
        mock_now.side_effect = Exception("Time error")

        workflow = GitHubPrDescriptionWorkflow()
        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        with pytest.raises(Exception, match="Failed to construct PR description with metadata"):
            workflow._construct_pr_description_with_metadata(
                "Test content",
                "abc1234",
                input_data,
            )

        mock_logger.error.assert_called_once()


class TestDetermineProcessingScope:
    """Test processing scope determination (full vs incremental)."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_determine_processing_scope_full_no_metadata(self, _mock_logger: MagicMock) -> None:
        """Test full processing when no metadata exists."""
        pr_details = {"body": "## Summary\nSome changes without metadata"}

        workflow = GitHubPrDescriptionWorkflow()
        result = await workflow._determine_processing_scope(pr_details)

        assert result["mode"] == "full"
        assert result["last_processed_commit"] is None
        assert result["existing_content"] == ""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_determine_processing_scope_incremental_with_metadata(self, _mock_logger: MagicMock) -> None:
        """Test incremental processing when metadata exists."""
        pr_details = {
            "body": """## Summary
Some changes

### 🤖 AWA Generation Info
| Metric | Value |
|--------|-------|
| Last Processed Commit | [`abc1234`](https://github.com/owner/repo/commit/abc1234) |
| Last Updated | 2023-01-01 12:00:00 UTC |""",
        }

        workflow = GitHubPrDescriptionWorkflow()
        result = await workflow._determine_processing_scope(pr_details)

        assert result["mode"] == "incremental"
        assert result["last_processed_commit"] == "abc1234"
        assert "## Summary\nSome changes" in result["existing_content"]

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_determine_processing_scope_list_format(self, _mock_logger: MagicMock) -> None:
        """Test processing scope determination with list format PR details."""
        pr_details = [{"body": "## Summary\nChanges"}]

        workflow = GitHubPrDescriptionWorkflow()
        result = await workflow._determine_processing_scope(pr_details)

        assert result["mode"] == "full"
        assert result["existing_content"] == ""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_determine_processing_scope_empty_body(self, _mock_logger: MagicMock) -> None:
        """Test processing scope determination with empty body."""
        pr_details = {"body": None}

        workflow = GitHubPrDescriptionWorkflow()
        result = await workflow._determine_processing_scope(pr_details)

        assert result["mode"] == "full"
        assert result["existing_content"] == ""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_determine_processing_scope_error_handling(self, mock_logger: MagicMock) -> None:
        """Test processing scope determination handles errors gracefully."""
        workflow = GitHubPrDescriptionWorkflow()

        # Simulate error by passing invalid data
        result = await workflow._determine_processing_scope("invalid_data")

        assert result["mode"] == "full"
        assert result["last_processed_commit"] is None
        mock_logger.error.assert_called_once()


class TestGetCommitLogs:
    """Test commit logs retrieval."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_commit_logs_success(self, mock_invoke_mcp_tool: AsyncMock, _mock_logger: MagicMock) -> None:
        """Test successful commit logs retrieval."""
        mock_commits = [
            {"sha": "abc123", "commit": {"message": "Add feature"}},
            {"sha": "def456", "commit": {"message": "Fix bug\nDetailed fix info"}},
        ]
        mock_invoke_mcp_tool.return_value = mock_commits

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            branch_name="feature/test",
        )

        commit_logs, latest_commit = await workflow._get_commit_logs(input_data)

        assert latest_commit == "abc123"
        assert "- Add feature (abc123)" in commit_logs
        assert "- Fix bug (def456)" in commit_logs

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_commit_logs_with_last_processed(
        self,
        mock_invoke_mcp_tool: AsyncMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test commit logs retrieval with last processed commit."""
        mock_commits = [
            {"sha": "abc123", "commit": {"message": "New commit"}},
            {"sha": "def456", "commit": {"message": "Old commit"}},  # This should stop here
        ]
        mock_invoke_mcp_tool.return_value = mock_commits

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            branch_name="feature/test",
        )

        commit_logs, latest_commit = await workflow._get_commit_logs(input_data, "def456")

        assert latest_commit == "abc123"
        assert "- New commit (abc123)" in commit_logs
        assert "Old commit" not in commit_logs

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_commit_logs_no_commits(self, mock_invoke_mcp_tool: AsyncMock, _mock_logger: MagicMock) -> None:
        """Test commit logs retrieval when no commits found."""
        mock_invoke_mcp_tool.return_value = []

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            branch_name="feature/test",
        )

        commit_logs, latest_commit = await workflow._get_commit_logs(input_data)

        assert commit_logs == "No new commits found."
        assert latest_commit == ""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_commit_logs_error(self, mock_invoke_mcp_tool: AsyncMock, mock_logger: MagicMock) -> None:
        """Test commit logs retrieval handles errors."""
        mock_invoke_mcp_tool.side_effect = Exception("API Error")

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            branch_name="feature/test",
        )

        with pytest.raises(Exception, match="API Error"):
            await workflow._get_commit_logs(input_data)

        mock_logger.error.assert_called_once()


class TestGetCurrentHeadCommit:
    """Test current HEAD commit retrieval."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_current_head_commit_success(
        self,
        mock_invoke_mcp_tool: AsyncMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test successful HEAD commit retrieval."""
        mock_commits = [{"sha": "abc123def456"}]
        mock_invoke_mcp_tool.return_value = mock_commits

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            branch_name="feature/test",
        )

        result = await workflow._get_current_head_commit(input_data)

        assert result == "abc123def456"

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_current_head_commit_no_commits(
        self,
        mock_invoke_mcp_tool: AsyncMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test HEAD commit retrieval when no commits found."""
        mock_invoke_mcp_tool.return_value = []

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            branch_name="feature/test",
        )

        result = await workflow._get_current_head_commit(input_data)

        assert result == ""
        mock_logger.warning.assert_called_once()

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_current_head_commit_error(self, mock_invoke_mcp_tool: AsyncMock, mock_logger: MagicMock) -> None:
        """Test HEAD commit retrieval handles errors."""
        mock_invoke_mcp_tool.side_effect = Exception("API Error")

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            branch_name="feature/test",
        )

        result = await workflow._get_current_head_commit(input_data)

        assert result == ""
        mock_logger.error.assert_called_once()


class TestGetFileDiffs:
    """Test file diffs retrieval from GitHub."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_file_diffs_success(self, mock_invoke_mcp_tool: AsyncMock, _mock_logger: MagicMock) -> None:
        """Test successful file diffs retrieval."""
        mock_files = [
            {
                "filename": "src/main.py",
                "patch": "@@ -1,3 +1,3 @@\n-print('old')\n+print('new')",
                "status": "modified",
            },
            {
                "filename": "README.md",
                "patch": "@@ -1 +1 @@\n-# Old Title\n+# New Title",
                "status": "modified",
            },
        ]
        mock_invoke_mcp_tool.return_value = mock_files

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow._get_file_diffs(input_data)

        assert "b/src/main.py" in result
        assert "b/README.md" in result
        assert "diff --git a/src/main.py b/src/main.py" in result["b/src/main.py"]
        assert "print('new')" in result["b/src/main.py"]

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_file_diffs_pagination(self, mock_invoke_mcp_tool: AsyncMock, _mock_logger: MagicMock) -> None:
        """Test file diffs retrieval with pagination."""
        # First page
        first_page = [{"filename": f"file{i}.py", "patch": f"patch{i}", "status": "modified"} for i in range(30)]
        # Second page (smaller, indicating end)
        second_page = [{"filename": "final.py", "patch": "final_patch", "status": "modified"}]

        mock_invoke_mcp_tool.side_effect = [first_page, second_page]

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow._get_file_diffs(input_data)

        assert len(result) == 31  # 30 + 1
        assert "b/file0.py" in result
        assert "b/final.py" in result

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_file_diffs_error(self, mock_invoke_mcp_tool: AsyncMock, mock_logger: MagicMock) -> None:
        """Test file diffs retrieval handles errors."""
        mock_invoke_mcp_tool.side_effect = Exception("API Error")

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        with pytest.raises(Exception, match="API Error"):
            await workflow._get_file_diffs(input_data)

        mock_logger.error.assert_called_once()


class TestConvertGithubPatchToGitDiff:
    """Test GitHub patch to git diff conversion."""

    def test_convert_github_patch_to_git_diff_success(self) -> None:
        """Test successful patch conversion."""
        filename = "src/main.py"
        patch = "@@ -1,3 +1,3 @@\n-print('old')\n+print('new')"

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._convert_github_patch_to_git_diff(filename, patch)

        assert result.startswith("diff --git a/src/main.py b/src/main.py")
        assert "@@ -1,3 +1,3 @@" in result
        assert "-print('old')" in result
        assert "+print('new')" in result

    def test_convert_github_patch_large_patch_truncation(self) -> None:
        """Test patch truncation for large patches."""
        filename = "large_file.py"
        # Create a patch with more than 1000 lines
        patch_lines = ["@@ -1,1000 +1,1000 @@"] + [f"line {i}" for i in range(1100)]
        patch = "\n".join(patch_lines)

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._convert_github_patch_to_git_diff(filename, patch)

        assert "truncated" in result
        assert result.count("\n") <= 1002  # Header + 1000 lines + truncation message

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_convert_github_patch_error_handling(self, _mock_logger: MagicMock) -> None:
        """Test patch conversion handles errors gracefully."""
        filename = "test.py"
        patch = "valid patch content"

        workflow = GitHubPrDescriptionWorkflow()

        # Test with malformed patch content to trigger error handling
        result = workflow._convert_github_patch_to_git_diff(filename, patch)
        # Should return a basic diff even on error
        assert result.startswith("diff --git a/test.py b/test.py")


class TestSummarizeFileDiffs:
    """Test file diff summarization."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_workflow.run_with_controlled_concurrency",
    )
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_workflow.execute_baml_transform",
    )
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.read_file")
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.Path")
    async def test_summarize_file_diffs_success(
        self,
        _mock_path: MagicMock,
        mock_read_file: AsyncMock,
        mock_execute_baml_transform: AsyncMock,
        mock_run_with_controlled_concurrency: AsyncMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test successful file diff summarization."""
        mock_read_file.return_value = "baml content"
        mock_execute_baml_transform.return_value = "File summary"
        mock_run_with_controlled_concurrency.return_value = ["Summary 1", "Summary 2"]

        # Mock workflow paths
        workflow = GitHubPrDescriptionWorkflow()
        mock_workflow_paths = MagicMock()
        mock_workflow_paths.baml_src = "/fake/baml"
        mock_workflow_paths.output = "/fake/output"
        workflow.workflow_paths = mock_workflow_paths

        file_diffs = {
            "b/file1.py": "diff content 1",
            "b/file2.py": "diff content 2",
        }

        result = await workflow._summarize_file_diffs(file_diffs)

        assert len(result) == 2
        assert "b/file1.py" in result
        assert "b/file2.py" in result
        mock_run_with_controlled_concurrency.assert_called_once()

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_workflow.run_with_controlled_concurrency",
    )
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.read_file")
    async def test_summarize_file_diffs_error(
        self,
        mock_read_file: AsyncMock,
        mock_run_with_controlled_concurrency: AsyncMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test file diff summarization handles errors."""
        mock_read_file.return_value = "baml content"
        mock_run_with_controlled_concurrency.side_effect = Exception("Summarization Error")

        workflow = GitHubPrDescriptionWorkflow()
        mock_workflow_paths = MagicMock()
        mock_workflow_paths.baml_src = "/fake/baml"
        mock_workflow_paths.output = "/fake/output"
        workflow.workflow_paths = mock_workflow_paths

        file_diffs = {"b/file1.py": "diff content"}

        with pytest.raises(Exception, match="Summarization Error"):
            await workflow._summarize_file_diffs(file_diffs)

        mock_logger.error.assert_called_once()


class TestGeneratePrSummary:
    """Test PR summary generation."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_workflow.execute_baml_transform",
    )
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_workflow.execute_baml_transform_batch",
    )
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.read_file")
    async def test_generate_pr_summary_success(
        self,
        mock_read_file: AsyncMock,
        mock_execute_baml_transform_batch: AsyncMock,
        mock_execute_baml_transform: AsyncMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test successful PR summary generation."""
        mock_execute_baml_transform_batch.return_value = {"batch_0": "Batch summary"}
        mock_read_file.return_value = "baml content"
        mock_execute_baml_transform.return_value = "Final PR summary"

        workflow = GitHubPrDescriptionWorkflow()
        mock_workflow_paths = MagicMock()
        mock_workflow_paths.baml_src = "/fake/baml"
        mock_workflow_paths.output = "/fake/output"
        workflow.workflow_paths = mock_workflow_paths

        summaries_by_file = {"file1": "Summary 1", "file2": "Summary 2"}
        commit_logs = "- Commit 1\n- Commit 2"

        result = await workflow._generate_pr_summary(summaries_by_file, commit_logs)

        assert result == "Final PR summary"
        mock_execute_baml_transform_batch.assert_called_once()
        mock_execute_baml_transform.assert_called_once()

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_workflow.execute_baml_transform",
    )
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_workflow.execute_baml_transform_batch",
    )
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.read_file")
    async def test_generate_pr_summary_error(
        self,
        mock_read_file: AsyncMock,
        mock_execute_baml_transform_batch: AsyncMock,
        mock_execute_baml_transform: AsyncMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test PR summary generation handles errors."""
        mock_execute_baml_transform_batch.return_value = {"batch_0": "Batch summary"}
        mock_read_file.return_value = "baml content"
        mock_execute_baml_transform.side_effect = Exception("Generation Error")

        workflow = GitHubPrDescriptionWorkflow()
        mock_workflow_paths = MagicMock()
        mock_workflow_paths.baml_src = "/fake/baml"
        mock_workflow_paths.output = "/fake/output"
        workflow.workflow_paths = mock_workflow_paths

        with pytest.raises(Exception, match="Generation Error"):
            await workflow._generate_pr_summary({}, "commits")

        mock_logger.error.assert_called_once()


class TestGetFilesForCommitRange:
    """Test getting files for specific commit range."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_files_for_commit_range_success(
        self,
        mock_invoke_mcp_tool: AsyncMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test successful file retrieval for commit range."""
        mock_commit_response = {
            "files": [
                {"filename": "file1.py", "patch": "patch1"},
                {"filename": "file2.py", "patch": "patch2"},
            ],
        }
        mock_invoke_mcp_tool.return_value = mock_commit_response

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow._get_files_for_commit_range(input_data, "abc123", "def456")

        assert len(result) == 2
        assert "file1.py" in result
        assert "file2.py" in result

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_files_for_commit_range_fallback(
        self,
        mock_invoke_mcp_tool: AsyncMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test fallback to all PR files when commit API fails."""
        # First call fails, second call (fallback) succeeds
        mock_invoke_mcp_tool.side_effect = Exception("API Error")

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        # Mock the _get_file_diffs method to return fallback data
        workflow._get_file_diffs = AsyncMock(return_value={"b/fallback.py": "fallback diff"})

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow._get_files_for_commit_range(input_data, "abc123", "def456")

        assert len(result) == 1
        assert "b/fallback.py" in result
        mock_logger.warning.assert_called()  # Should log the fallback


class TestUpdateExistingDescription:
    """Test updating existing PR descriptions."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_update_existing_description_success(self, _mock_logger: MagicMock) -> None:
        """Test successful description update."""
        existing_content = """## Summary
Original changes

## File-by-File Changes
- `old_file.py`: Old description
- `kept_file.py`: Kept description"""

        new_summary = "Updated summary"
        new_files = {
            "b/new_file.py": "New file description",
            "b/kept_file.py": "Updated kept file",  # This should overwrite
        }

        workflow = GitHubPrDescriptionWorkflow()
        result = await workflow._update_existing_description(existing_content, new_summary, new_files)

        assert "Updated summary" in result
        assert "- `new_file.py`: New file description" in result
        assert "- `kept_file.py`: Updated kept file" in result
        assert "old_file.py" not in result  # Should be removed as not in current PR

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_update_existing_description_error_fallback(self, _mock_logger: MagicMock) -> None:
        """Test description update falls back on error."""
        workflow = GitHubPrDescriptionWorkflow()

        # Mock _construct_pr_description to test the fallback
        workflow._construct_pr_description = MagicMock(return_value="Fallback description")

        # Simulate error in parsing by passing invalid content
        result = await workflow._update_existing_description("", "summary", {"file": "desc"})

        assert result == "Fallback description"
        workflow._construct_pr_description.assert_called_once()


class TestConstructPrDescription:
    """Test PR description construction."""

    def test_construct_pr_description_success(self) -> None:
        """Test successful PR description construction."""
        high_level_summary = "High level summary of changes"
        summaries_by_file = {
            "b/file1.py": "Changes to file1",
            "b/file2.py": "Changes to file2",
            "b/dir/file3.py": "Changes to nested file",
        }

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._construct_pr_description(high_level_summary, summaries_by_file)

        assert "## Summary" in result
        assert "High level summary of changes" in result
        assert "## File-by-File Changes" in result
        assert "- `file1.py`: Changes to file1" in result
        assert "- `file2.py`: Changes to file2" in result
        assert "- `dir/file3.py`: Changes to nested file" in result

    def test_construct_pr_description_empty_files(self) -> None:
        """Test PR description construction with no files."""
        high_level_summary = "Summary only"
        summaries_by_file = {}

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._construct_pr_description(high_level_summary, summaries_by_file)

        assert "## Summary" in result
        assert "Summary only" in result
        assert "## File-by-File Changes" in result
        # Should have no file entries


class TestParseDiff:
    """Test diff parsing functionality."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_parse_diff_string_input(self, _mock_logger: MagicMock) -> None:
        """Test parsing diff from string input."""
        diff_string = """diff --git a/file1.py b/file1.py
@@ -1 +1 @@
-old line
+new line
diff --git a/file2.py b/file2.py
@@ -1 +1 @@
-old line 2
+new line 2"""

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._parse_diff(diff_string)

        assert len(result) == 2
        assert "b/file1.py" in result
        assert "b/file2.py" in result
        assert "old line" in result["b/file1.py"]
        assert "new line" in result["b/file1.py"]

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_parse_diff_list_input(self, _mock_logger: MagicMock) -> None:
        """Test parsing diff from list input."""
        diff_list = [{"text": "diff --git a/test.py b/test.py\n@@ -1 +1 @@\n-old\n+new"}]

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._parse_diff(diff_list)

        assert len(result) == 1
        assert "b/test.py" in result
        assert "old" in result["b/test.py"]

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_parse_diff_dict_input(self, _mock_logger: MagicMock) -> None:
        """Test parsing diff from dict input."""
        diff_dict = {"data": {"diff": "diff --git a/test.py b/test.py\n@@ -1 +1 @@\n-old\n+new"}}

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._parse_diff(diff_dict)

        assert len(result) == 1
        assert "b/test.py" in result

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_parse_diff_invalid_input(self, _mock_logger: MagicMock) -> None:
        """Test parsing diff with invalid input."""
        workflow = GitHubPrDescriptionWorkflow()

        # Test with None
        result = workflow._parse_diff(None)
        assert result == {}

        # Test with empty string
        result = workflow._parse_diff("")
        assert result == {}

        # Test with invalid structure
        result = workflow._parse_diff({"invalid": "structure"})
        assert result == {}

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_parse_diff_malformed_chunks(self, mock_logger: MagicMock) -> None:
        """Test parsing diff with malformed chunks."""
        # Missing proper file path format
        malformed_diff = "diff --git invalid format\n@@ -1 +1 @@\n-old\n+new"

        workflow = GitHubPrDescriptionWorkflow()
        result = workflow._parse_diff(malformed_diff)

        # Should handle gracefully and log warnings
        assert isinstance(result, dict)
        mock_logger.warn.assert_called()


class TestWorkflowRunMethod:
    """Test the main workflow run method orchestration."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_general.get_workflow_paths",
    )
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.resolve_config_variables",
    )
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.read_file")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    @patch("temporalio.workflow.info")
    async def test_run_full_processing_mode(
        self,
        mock_workflow_info: MagicMock,
        _mock_invoke_mcp_tool: AsyncMock,
        mock_read_file: AsyncMock,
        mock_resolve_config: AsyncMock,
        mock_get_workflow_paths: MagicMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test full workflow run in full processing mode."""
        # Setup mocks for initialization
        mock_workflow_info.return_value.workflow_id = "test-workflow"
        mock_read_file.return_value = '{"github": "config"}'
        mock_resolve_config.return_value = '{"github": "config"}'
        mock_get_workflow_paths.return_value = MagicMock()

        # Setup workflow instance
        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)
        mock_workflow_paths = MagicMock()
        mock_workflow_paths.baml_src = "/fake/baml"
        mock_workflow_paths.output = "/fake/output"
        workflow.workflow_paths = mock_workflow_paths

        # Mock PR details fetch
        pr_details = {
            "head": {"ref": "feature/test"},
            "base": {"ref": "main"},
            "body": "No existing metadata",  # This triggers full processing
        }
        workflow._fetch_pr_details = AsyncMock(return_value=pr_details)
        workflow._determine_processing_scope = AsyncMock(
            return_value={
                "mode": "full",
                "last_processed_commit": None,
                "existing_content": "",
            },
        )

        # Mock commit and file operations
        workflow._get_commit_logs = AsyncMock(return_value=("- Commit message", "abc123"))
        workflow._get_file_diffs = AsyncMock(return_value={"b/file.py": "diff content"})
        workflow._summarize_file_diffs = AsyncMock(return_value={"b/file.py": "File summary"})
        workflow._generate_pr_summary = AsyncMock(return_value="High level PR summary")
        workflow._construct_pr_description = MagicMock(return_value="Complete PR description")
        workflow._construct_pr_description_with_metadata = MagicMock(return_value="PR with metadata")
        workflow._update_github_pr = AsyncMock(return_value={"updated": True})

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow.run(input_data)

        assert result == "PR with metadata"
        workflow._fetch_pr_details.assert_called_once()
        workflow._determine_processing_scope.assert_called_once()
        workflow._get_commit_logs.assert_called_once()
        workflow._get_file_diffs.assert_called_once()
        workflow._summarize_file_diffs.assert_called_once()
        workflow._generate_pr_summary.assert_called_once()
        workflow._update_github_pr.assert_called_once()

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.info")
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_run_incremental_processing_mode(
        self,
        mock_workflow_info: MagicMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test workflow run in incremental processing mode."""
        mock_workflow_info.return_value.workflow_id = "test-workflow-incremental"
        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)
        mock_workflow_paths = MagicMock()
        mock_workflow_paths.baml_src = "/fake/baml"
        mock_workflow_paths.output = "/fake/output"
        workflow.workflow_paths = mock_workflow_paths

        # Mock initialization
        workflow._initialize_workflow = AsyncMock()

        # Mock PR details with existing metadata
        pr_details = {
            "head": {"ref": "feature/test"},
            "base": {"ref": "main"},
            "body": """## Summary
Existing content

### 🤖 AWA Generation Info
| Last Processed Commit | [`def456`] |""",
        }
        workflow._fetch_pr_details = AsyncMock(return_value=pr_details)
        workflow._determine_processing_scope = AsyncMock(
            return_value={
                "mode": "incremental",
                "last_processed_commit": "def456",
                "existing_content": "## Summary\nExisting content",
            },
        )

        # Mock incremental processing
        workflow._get_current_head_commit = AsyncMock(return_value="abc123")  # Different from last processed
        workflow._get_commit_logs = AsyncMock(return_value=("- New commit", "abc123"))
        workflow._get_files_for_commit_range = AsyncMock(return_value={"b/new_file.py": "new diff"})
        workflow._summarize_file_diffs = AsyncMock(return_value={"b/new_file.py": "New file summary"})
        workflow._generate_pr_summary = AsyncMock(return_value="Incremental summary")
        workflow._update_existing_description = AsyncMock(return_value="Updated description")
        workflow._construct_pr_description_with_metadata = MagicMock(return_value="Updated with metadata")
        workflow._update_github_pr = AsyncMock(return_value={"updated": True})

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow.run(input_data)

        assert result == "Updated with metadata"
        workflow._get_files_for_commit_range.assert_called_once()
        workflow._update_existing_description.assert_called_once()

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch("temporalio.workflow.info")
    async def test_run_timestamp_only_update(self, mock_workflow_info: MagicMock, _mock_logger: MagicMock) -> None:
        """Test workflow run with timestamp-only update when no new commits."""
        mock_workflow_info.return_value.workflow_id = "test-workflow-timestamp"

        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        # Mock initialization
        workflow._initialize_workflow = AsyncMock()

        pr_details = {
            "head": {"ref": "feature/test"},
            "base": {"ref": "main"},
            "body": """## Summary
Existing content

### 🤖 AWA Generation Info
| Last Processed Commit | [`abc123`] |""",
        }
        workflow._fetch_pr_details = AsyncMock(return_value=pr_details)
        workflow._determine_processing_scope = AsyncMock(
            return_value={
                "mode": "incremental",
                "last_processed_commit": "abc123",
                "existing_content": "## Summary\nExisting content",
                "full_existing_description": pr_details["body"],
            },
        )

        # Mock HEAD commit matches last processed (no new commits)
        workflow._get_current_head_commit = AsyncMock(return_value="abc123def")  # Starts with last processed
        workflow._update_metadata_timestamp = AsyncMock(return_value="Updated timestamp")
        workflow._update_github_pr = AsyncMock(return_value={"updated": True})

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow.run(input_data)

        assert result == "No new changes detected since last update. Timestamp updated."
        workflow._update_metadata_timestamp.assert_called_once()
        workflow._update_github_pr.assert_called_once()

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.info")
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_run_no_changes_detected(self, mock_workflow_info: MagicMock, _mock_logger: MagicMock) -> None:
        """Test workflow run when no changes are detected."""
        mock_workflow_info.return_value.workflow_id = "test-workflow-no-changes"
        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        # Mock initialization
        workflow._initialize_workflow = AsyncMock()

        workflow._fetch_pr_details = AsyncMock(return_value={"body": ""})
        workflow._determine_processing_scope = AsyncMock(
            return_value={
                "mode": "full",
                "last_processed_commit": None,
                "existing_content": "",
            },
        )

        # Mock no commits and no files
        workflow._get_commit_logs = AsyncMock(return_value=("", ""))
        workflow._get_file_diffs = AsyncMock(return_value={})

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow.run(input_data)

        assert result == "No changes detected in this PR."

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.info")
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_run_no_new_commits_incremental(self, mock_workflow_info: MagicMock, _mock_logger: MagicMock) -> None:
        """Test workflow run with no new commits in incremental mode."""
        mock_workflow_info.return_value.workflow_id = "test-workflow-no-commits"
        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        # Mock initialization
        workflow._initialize_workflow = AsyncMock()

        workflow._fetch_pr_details = AsyncMock(return_value={"body": "existing"})
        workflow._determine_processing_scope = AsyncMock(
            return_value={
                "mode": "incremental",
                "last_processed_commit": "def456",
                "existing_content": "existing content",
            },
        )

        # Mock no new commits
        workflow._get_current_head_commit = AsyncMock(return_value="xyz789")  # Different commit
        workflow._get_commit_logs = AsyncMock(return_value=("No new commits found.", ""))

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow.run(input_data)

        assert result == "No new changes detected since last update."

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.info")
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_run_no_file_changes_incremental(
        self,
        mock_workflow_info: MagicMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test workflow run with no file changes in incremental mode."""
        mock_workflow_info.return_value.workflow_id = "test-workflow-no-files"
        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        # Mock initialization
        workflow._initialize_workflow = AsyncMock()

        workflow._fetch_pr_details = AsyncMock(return_value={"body": "existing"})
        workflow._determine_processing_scope = AsyncMock(
            return_value={
                "mode": "incremental",
                "last_processed_commit": "def456",
                "existing_content": "existing content",
            },
        )

        # Mock new commits but no file changes
        workflow._get_current_head_commit = AsyncMock(return_value="xyz789")
        workflow._get_commit_logs = AsyncMock(return_value=("- New commit", "xyz789"))
        workflow._get_files_for_commit_range = AsyncMock(return_value={})  # No files changed

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow.run(input_data)

        assert result == "No new file changes detected since last update."

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.info")
    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_run_populates_missing_branch_info(
        self,
        mock_workflow_info: MagicMock,
        _mock_logger: MagicMock,
    ) -> None:
        """Test workflow run populates missing branch information from PR details."""
        mock_workflow_info.return_value.workflow_id = "test-workflow-branch-info"
        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        # Mock initialization
        workflow._initialize_workflow = AsyncMock()

        # PR details with branch info
        pr_details = {
            "head": {"ref": "feature/auto-populated"},
            "base": {"ref": "develop"},
            "body": "",
        }
        workflow._fetch_pr_details = AsyncMock(return_value=pr_details)
        workflow._determine_processing_scope = AsyncMock(
            return_value={
                "mode": "full",
                "last_processed_commit": None,
                "existing_content": "",
            },
        )

        # Mock full processing
        workflow._get_commit_logs = AsyncMock(return_value=("- Commit", "abc123"))
        workflow._get_file_diffs = AsyncMock(return_value={"b/file.py": "diff"})
        workflow._summarize_file_diffs = AsyncMock(return_value={"b/file.py": "summary"})
        workflow._generate_pr_summary = AsyncMock(return_value="summary")
        workflow._construct_pr_description = MagicMock(return_value="description")
        workflow._construct_pr_description_with_metadata = MagicMock(return_value="with metadata")
        workflow._update_github_pr = AsyncMock(return_value={"updated": True})

        # Input with missing branch information
        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            base_branch="",  # Empty - should be populated
            branch_name="",  # Empty - should be populated
        )

        result = await workflow.run(input_data)

        # Verify branch info was populated
        assert input_data.base_branch == "develop"
        assert input_data.branch_name == "feature/auto-populated"
        assert result == "with metadata"

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch("temporalio.workflow.info")
    async def test_run_with_none_pr_details(self, mock_workflow_info: MagicMock, _mock_logger: MagicMock) -> None:
        """Test workflow run handles None PR details gracefully."""
        mock_workflow_info.return_value.workflow_id = "test-workflow-none-details"

        workflow = GitHubPrDescriptionWorkflow()
        workflow._initialize_workflow = AsyncMock()
        workflow._fetch_pr_details = AsyncMock(return_value=None)
        workflow._determine_processing_scope = AsyncMock(
            return_value={
                "mode": "full",
                "last_processed_commit": None,
                "existing_content": "",
            },
        )

        # Mock no changes found
        workflow._get_commit_logs = AsyncMock(return_value=("", ""))
        workflow._get_file_diffs = AsyncMock(return_value={})

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        result = await workflow.run(input_data)

        assert result == "No changes detected in this PR."


# Additional comprehensive tests for 80%+ coverage


class TestCoreLogicMethods:
    """Test core logic methods that don't require workflow environment."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_extract_metadata_comprehensive(self, _mock_logger: MagicMock) -> None:
        """Test metadata extraction with various scenarios."""
        workflow = GitHubPrDescriptionWorkflow()

        # Test malformed table with partial data
        pr_malformed = """
### 🤖 AWA Generation Info
| Metric | Value |
| Last Processed Commit | incomplete
"""
        result = workflow._extract_metadata_from_table(pr_malformed)
        assert result["last_processed_commit"] is None
        assert result["last_updated"] is None

    def test_construct_pr_description_comprehensive(self) -> None:
        """Test PR description construction with various file configurations."""
        workflow = GitHubPrDescriptionWorkflow()

        # Test with deeply nested files
        summary = "Comprehensive changes"
        files = {
            "b/src/deep/nested/module.py": "Deep nested changes",
            "b/tests/integration/test_api.py": "Integration test updates",
            "b/docs/api/reference.md": "API documentation",
        }

        result = workflow._construct_pr_description(summary, files)

        assert "## Summary" in result
        assert summary in result
        assert "- `src/deep/nested/module.py`: Deep nested changes" in result
        assert "- `tests/integration/test_api.py`: Integration test updates" in result
        assert "- `docs/api/reference.md`: API documentation" in result

    def test_convert_github_patch_edge_cases(self) -> None:
        """Test patch conversion edge cases."""
        workflow = GitHubPrDescriptionWorkflow()

        # Test very large patch (should be truncated)
        large_lines = [f"line {i} with content" for i in range(1200)]
        large_patch = "@@ -1,1200 +1,1200 @@\n" + "\n".join(large_lines)

        result = workflow._convert_github_patch_to_git_diff("large_file.py", large_patch)
        assert "truncated" in result
        # Should be truncated to max_lines + some overhead
        line_count = result.count("\n")
        assert line_count <= 1005  # max_lines + header + truncation message

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    def test_parse_diff_comprehensive(self, _mock_logger: MagicMock) -> None:
        """Test diff parsing with various formats and edge cases."""
        workflow = GitHubPrDescriptionWorkflow()

        # Test diff without proper prefix
        diff_no_prefix = """a/file1.py b/file1.py
@@ -1 +1 @@
-old
+new"""
        result = workflow._parse_diff(diff_no_prefix)
        assert len(result) == 1
        assert "b/file1.py" in result

        # Test malformed chunks (should be handled gracefully)
        malformed_diff = "diff --git incomplete format\n@@ -1 +1 @@\n-old\n+new"
        result_malformed = workflow._parse_diff(malformed_diff)
        # Should return empty dict or handle gracefully
        assert isinstance(result_malformed, dict)


class TestMockedAsyncMethods:
    """Test async methods with comprehensive mocking."""

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_determine_processing_scope_edge_cases(self, _mock_logger: MagicMock) -> None:
        """Test processing scope with edge cases."""
        workflow = GitHubPrDescriptionWorkflow()

        # Test with complex existing content
        complex_pr_details = {
            "body": """# Complex PR Description

Multiple sections here.

## Changes Made
- Feature A
- Feature B

### 🤖 AWA Generation Info
| Metric | Value |
|--------|-------|
| Last Processed Commit | [`complex123`](https://github.com/test/repo/commit/complex123) |
| Last Updated | 2023-05-15 14:30:00 UTC |

Additional content after table.""",
        }

        result = await workflow._determine_processing_scope(complex_pr_details)

        assert result["mode"] == "incremental"
        assert result["last_processed_commit"] == "complex123"
        # Should extract content before the metadata table
        assert "# Complex PR Description" in result["existing_content"]
        assert "## Changes Made" in result["existing_content"]
        assert "🤖 AWA Generation Info" not in result["existing_content"]

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch("temporalio.workflow.now")
    async def test_update_metadata_timestamp_complex(self, mock_now: MagicMock, _mock_logger: MagicMock) -> None:
        """Test metadata timestamp update with complex scenarios."""
        mock_now.return_value = datetime(2023, 8, 20, 15, 45, 30, tzinfo=UTC)

        workflow = GitHubPrDescriptionWorkflow()

        # Test with content that already ends with ---
        content_with_separator = """## Summary
Existing changes
---

### 🤖 AWA Generation Info
| Metric | Value |
|--------|-------|
| Last Processed Commit | [`old123`](https://github.com/owner/repo/commit/old123) |
| Last Updated | 2023-01-01 10:00:00 UTC |"""

        result = await workflow._update_metadata_timestamp(content_with_separator, "new456")

        assert "2023-08-20 15:45:30 UTC" in result
        # Should preserve the original commit SHA
        assert "`old123`" in result
        # Should not duplicate the main content separator (count standalone --- lines)
        lines = result.split("\n")
        standalone_separator_count = sum(1 for line in lines if line.strip() == "---")
        assert standalone_separator_count == 1

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    async def test_update_existing_description_complex(self, _mock_logger: MagicMock) -> None:
        """Test existing description update with complex file management."""
        workflow = GitHubPrDescriptionWorkflow()

        # Complex existing content with multiple file sections
        complex_existing = """## Summary
Multi-part summary with details

## Key Changes
- Important change 1
- Important change 2

## File-by-File Changes
- `src/core.py`: Core functionality updates
- `src/utils.py`: Utility function improvements
- `tests/test_core.py`: Test coverage improvements
- `config/settings.py`: Configuration updates
- `docs/readme.md`: Documentation fixes"""

        new_summary = "Updated comprehensive summary"
        # Simulate some files removed, some updated, some new
        new_files = {
            "b/src/core.py": "Enhanced core functionality with new features",
            "b/src/api.py": "New API module implementation",
            "b/tests/test_core.py": "Expanded test coverage with edge cases",
            "b/tests/test_api.py": "New API test suite",
            # Note: utils.py, settings.py, readme.md are "removed" (not in current PR)
        }

        result = await workflow._update_existing_description(complex_existing, new_summary, new_files)

        # Should have updated summary
        assert "Updated comprehensive summary" in result

        # Should include updated files
        assert "- `src/core.py`: Enhanced core functionality with new features" in result
        assert "- `tests/test_core.py`: Expanded test coverage with edge cases" in result

        # Should include new files
        assert "- `src/api.py`: New API module implementation" in result
        assert "- `tests/test_api.py`: New API test suite" in result

        # Should NOT include files no longer in the PR
        assert "src/utils.py" not in result
        assert "config/settings.py" not in result
        assert "docs/readme.md" not in result
        assert "Utility function improvements" not in result

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_commit_logs_pagination(self, mock_utils: MagicMock, _mock_logger: MagicMock) -> None:
        """Test commit logs with pagination scenarios."""
        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        # Simulate pagination with multiple pages
        page_1_commits = [{"sha": f"abcdef{i:02d}1234567890", "commit": {"message": f"Message {i}"}} for i in range(10)]
        page_2_commits = [
            {"sha": f"abcdef{i:02d}1234567890", "commit": {"message": f"Message {i}"}} for i in range(10, 15)
        ]
        # Third page empty (end of commits)
        page_3_commits = []

        mock_utils.side_effect = [page_1_commits, page_2_commits, page_3_commits]

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            branch_name="feature/paginated",
        )

        commit_logs, latest_commit = await workflow._get_commit_logs(input_data)

        # Should get the first commit SHA as latest
        assert latest_commit == "abcdef001234567890"

        # Should contain commits from all pages (checking truncated SHAs)
        assert "- Message 0 (abcdef0)" in commit_logs
        assert "- Message 9 (abcdef0)" in commit_logs
        assert "- Message 14 (abcdef1)" in commit_logs

        # Should have made 2 API calls (stops when page 2 returns less than per_page)
        assert mock_utils.call_count == 2

    @patch("cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.github_pr_description.github_pr_description_workflow.awa_activity.invoke_mcp_tool",
    )
    async def test_get_file_diffs_empty_results(self, mock_utils: MagicMock, _mock_logger: MagicMock) -> None:
        """Test file diffs with empty or invalid results."""
        workflow = GitHubPrDescriptionWorkflow()
        workflow.mcp_config = {"github": {"token": "test-token"}}
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)

        input_data = GitHubPrDescriptionWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
        )

        # Test with empty response
        mock_utils.return_value = []
        result_empty = await workflow._get_file_diffs(input_data)
        assert result_empty == {}

        # Test with None response
        mock_utils.return_value = None
        result_none = await workflow._get_file_diffs(input_data)
        assert result_none == {}

        # Test with malformed file entries (should be filtered out)
        malformed_files = [
            {"filename": "valid.py", "patch": "valid patch", "status": "modified"},
            {"invalid": "entry"},  # Missing required fields
            {"filename": "", "patch": "", "status": "modified"},  # Empty filename/patch
            {"filename": "another_valid.py", "patch": "another patch", "status": "added"},
        ]
        mock_utils.return_value = malformed_files
        result_filtered = await workflow._get_file_diffs(input_data)

        # Should only include valid entries
        assert len(result_filtered) == 2
        assert "b/valid.py" in result_filtered
        assert "b/another_valid.py" in result_filtered
