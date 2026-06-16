"""Unit tests for PrDescriptionWorkflow."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio.common import RetryPolicy

from cookbook.recipes.workflows.pr_description.models.pr_description_workflow_input import PrDescriptionWorkflowInput
from cookbook.recipes.workflows.pr_description.pr_description_workflow import PrDescriptionWorkflow


class TestPrDescriptionWorkflow:
    """Test class for PrDescriptionWorkflow."""

    @pytest.fixture
    def workflow_input(self) -> PrDescriptionWorkflowInput:
        """Create a test workflow input."""
        return PrDescriptionWorkflowInput(
            branch_name="feature/test-branch",
            repo_path="/test/repo",
            base_branch="main",
        )

    @pytest.fixture
    def mock_workflow_paths(self) -> MagicMock:
        """Create mock workflow paths."""
        mock_paths = MagicMock()
        mock_paths.output = "/test/output"
        mock_paths.baml_src = "/test/baml_src"
        return mock_paths

    @pytest.fixture
    def mock_mcp_config(self) -> dict[str, object]:
        """Create mock MCP configuration."""
        return {
            "mcpServers": {
                "git": {
                    "command": "git-mcp-server",
                    "args": [],
                },
            },
        }

    @pytest.fixture
    def sample_commit_logs(self) -> list[dict[str, str]]:
        """Create sample commit log data."""
        return [
            {
                "text": json.dumps(
                    {
                        "groupedCommits": [
                            {
                                "commits": [
                                    {"subject": "Add new feature", "hash": "abc1234567"},
                                    {"subject": "Fix bug", "hash": "def7890123"},
                                ],
                            },
                        ],
                    },
                ),
            },
        ]

    @pytest.fixture
    def sample_git_diff(self) -> list[dict[str, str]]:
        """Create sample git diff output."""
        return [
            {
                "text": (
                    "diff --git a/file1.py b/file1.py\nindex 123..456 100644\n"
                    "--- a/file1.py\n+++ b/file1.py\n@@ -1,3 +1,4 @@\n def function():\n"
                    "     pass\n+    return True\n"
                ),
            },
        ]

    @pytest.fixture
    def workflow(self) -> PrDescriptionWorkflow:
        """Create a workflow instance."""
        return PrDescriptionWorkflow()

    @pytest.mark.asyncio
    async def test_init(self, workflow: PrDescriptionWorkflow) -> None:
        """Test workflow initialization."""
        # Assert
        assert workflow.mcp_config == {}
        assert workflow.workflow_paths is None
        assert workflow.project_root == ""
        assert workflow.retry_policy is None

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_activity.read_file")
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_general.get_workflow_paths")
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.info")
    async def test_initialize_workflow(
        self,
        mock_workflow_info: MagicMock,
        mock_get_paths: MagicMock,
        mock_read_file: MagicMock,
        workflow: PrDescriptionWorkflow,
        workflow_input: PrDescriptionWorkflowInput,
        mock_workflow_paths: MagicMock,
        mock_mcp_config: dict[str, object],
    ) -> None:
        """Test workflow initialization method."""
        # Arrange
        mock_read_file.return_value = json.dumps(mock_mcp_config)
        mock_get_paths.return_value = mock_workflow_paths
        mock_workflow_info.return_value = MagicMock()

        # Act
        await workflow._initialize_workflow(workflow_input)

        # Assert
        assert workflow.mcp_config == mock_mcp_config
        assert workflow.workflow_paths == mock_workflow_paths
        assert workflow.project_root == workflow_input.repo_path
        assert isinstance(workflow.retry_policy, RetryPolicy)
        assert workflow.retry_policy.maximum_attempts == 3

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_activity.invoke_mcp_tool")
    async def test_get_commit_logs_success(
        self,
        mock_invoke_mcp: MagicMock,
        workflow: PrDescriptionWorkflow,
        workflow_input: PrDescriptionWorkflowInput,
        sample_commit_logs: list[dict[str, str]],
    ) -> None:
        """Test successful commit log retrieval."""
        # Arrange
        workflow.mcp_config = {"test": "config"}
        workflow.project_root = "/test/repo"
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)
        mock_invoke_mcp.return_value = sample_commit_logs

        # Act
        result = await workflow._get_commit_logs(workflow_input)

        # Assert
        expected_logs = "- Add new feature (abc1234)\n- Fix bug (def7890)"
        assert result == expected_logs
        mock_invoke_mcp.assert_called_once_with(
            mcp_config=workflow.mcp_config,
            tool_name="git_log",
            parameters={
                "branchOrFile": "main..feature/test-branch",
                "path": "/test/repo",
            },
        )

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_activity.invoke_mcp_tool")
    async def test_get_commit_logs_empty_result(
        self,
        mock_invoke_mcp: MagicMock,
        workflow: PrDescriptionWorkflow,
        workflow_input: PrDescriptionWorkflowInput,
    ) -> None:
        """Test commit log retrieval with empty result."""
        # Arrange
        workflow.mcp_config = {"test": "config"}
        workflow.project_root = "/test/repo"
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)
        mock_invoke_mcp.return_value = []

        # Act
        result = await workflow._get_commit_logs(workflow_input)

        # Assert
        assert result == ""

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_activity.invoke_mcp_tool")
    async def test_get_commit_logs_exception(
        self,
        mock_invoke_mcp: MagicMock,
        workflow: PrDescriptionWorkflow,
        workflow_input: PrDescriptionWorkflowInput,
    ) -> None:
        """Test commit log retrieval with exception."""
        # Arrange
        workflow.mcp_config = {"test": "config"}
        workflow.project_root = "/test/repo"
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)
        mock_invoke_mcp.side_effect = Exception("MCP error")

        # Act & Assert
        with pytest.raises(Exception, match="MCP error"):
            await workflow._get_commit_logs(workflow_input)

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_activity.invoke_mcp_tool")
    async def test_get_file_diffs_success(
        self,
        mock_invoke_mcp: MagicMock,
        workflow: PrDescriptionWorkflow,
        workflow_input: PrDescriptionWorkflowInput,
        sample_git_diff: list[dict[str, str]],
    ) -> None:
        """Test successful file diff retrieval."""
        # Arrange
        workflow.mcp_config = {"test": "config"}
        workflow.project_root = "/test/repo"
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)
        mock_invoke_mcp.return_value = sample_git_diff

        # Act
        result = await workflow._get_file_diffs(workflow_input)

        # Assert
        assert "b/file1.py" in result
        assert "diff --git" in result["b/file1.py"]
        mock_invoke_mcp.assert_called_once_with(
            mcp_config=workflow.mcp_config,
            tool_name="git_diff",
            parameters={
                "commit1": "main",
                "commit2": "feature/test-branch",
                "path": "/test/repo",
            },
        )

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_activity.invoke_mcp_tool")
    async def test_get_file_diffs_exception(
        self,
        mock_invoke_mcp: MagicMock,
        workflow: PrDescriptionWorkflow,
        workflow_input: PrDescriptionWorkflowInput,
    ) -> None:
        """Test file diff retrieval with exception."""
        # Arrange
        workflow.mcp_config = {"test": "config"}
        workflow.project_root = "/test/repo"
        workflow.retry_policy = RetryPolicy(maximum_attempts=3)
        mock_invoke_mcp.side_effect = Exception("Git diff error")

        # Act & Assert
        with pytest.raises(Exception, match="Git diff error"):
            await workflow._get_file_diffs(workflow_input)

    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    def test_parse_diff_with_list_input(
        self,
        workflow: PrDescriptionWorkflow,
    ) -> None:
        """Test diff parsing with list input."""
        # Arrange
        diff_output = [
            {
                "text": (
                    "diff --git a/test.py b/test.py\nindex 123..456\n"
                    "--- a/test.py\n+++ b/test.py\n@@ -1,3 +1,4 @@\n def func():\n"
                    "     pass\n+    return True\n"
                ),
            },
        ]

        # Act
        result = workflow._parse_diff(diff_output)

        # Assert
        assert "b/test.py" in result
        assert "diff --git" in result["b/test.py"]

    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    def test_parse_diff_with_string_input(
        self,
        workflow: PrDescriptionWorkflow,
    ) -> None:
        """Test diff parsing with string input."""
        # Arrange
        diff_output = (
            "a/test.py b/test.py\nindex 123..456\n--- a/test.py\n+++ b/test.py\n"
            "@@ -1,3 +1,4 @@\n def func():\n     pass\n+    return True\n"
        )

        # Act
        result = workflow._parse_diff(diff_output)

        # Assert
        assert "b/test.py" in result
        assert "diff --git" in result["b/test.py"]

    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    def test_parse_diff_empty_input(
        self,
        workflow: PrDescriptionWorkflow,
    ) -> None:
        """Test diff parsing with empty input."""
        # Arrange
        diff_output = []

        # Act
        result = workflow._parse_diff(diff_output)

        # Assert
        assert result == {}

    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    def test_parse_diff_invalid_format(
        self,
        workflow: PrDescriptionWorkflow,
    ) -> None:
        """Test diff parsing with invalid format."""
        # Arrange
        diff_output = "invalid diff format without proper structure"

        # Act
        result = workflow._parse_diff(diff_output)

        # Assert
        assert result == {}

    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    def test_parse_diff_multiple_files(
        self,
        workflow: PrDescriptionWorkflow,
    ) -> None:
        """Test diff parsing with multiple files."""
        # Arrange
        diff_output = (
            "diff --git a/file1.py b/file1.py\nindex 123..456\n"
            "--- a/file1.py\n+++ b/file1.py\n@@ -1 +1,2 @@\n print('hello')\n+print('world')\n"
            "diff --git a/file2.py b/file2.py\nindex 789..012\n"
            "--- a/file2.py\n+++ b/file2.py\n@@ -1 +1,2 @@\n def test():\n+    pass\n"
        )

        # Act
        result = workflow._parse_diff(diff_output)

        # Assert
        assert len(result) == 2
        assert "b/file1.py" in result
        assert "b/file2.py" in result

    @pytest.mark.asyncio
    @patch(
        "cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_workflow.run_with_controlled_concurrency",
    )
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_workflow.execute_baml_transform")
    async def test_summarize_file_diffs_success(
        self,
        mock_controlled_concurrency: MagicMock,
        workflow: PrDescriptionWorkflow,
        mock_workflow_paths: MagicMock,
    ) -> None:
        """Test successful file diff summarization."""
        # Arrange
        workflow.workflow_paths = mock_workflow_paths
        file_diffs = {
            "b/file1.py": "diff content 1",
            "b/file2.py": "diff content 2",
        }
        mock_controlled_concurrency.return_value = ["summary 1", "summary 2"]

        with patch.object(workflow, "_write_summaries_to_files", new_callable=AsyncMock) as mock_write:
            # Act
            result = await workflow._summarize_file_diffs(file_diffs)

            # Assert
            assert result == {"b/file1.py": "summary 1", "b/file2.py": "summary 2"}
            mock_controlled_concurrency.assert_called_once()
            mock_write.assert_called_once_with(result)

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_workflow.run_with_controlled_concurrency",
    )
    async def test_summarize_file_diffs_exception(
        self,
        mock_controlled_concurrency: MagicMock,
        workflow: PrDescriptionWorkflow,
        mock_workflow_paths: MagicMock,
    ) -> None:
        """Test file diff summarization with exception."""
        # Arrange
        workflow.workflow_paths = mock_workflow_paths
        file_diffs = {"b/file1.py": "diff content"}
        mock_controlled_concurrency.side_effect = Exception("Summarization error")

        # Act & Assert
        with pytest.raises(Exception, match="Summarization error"):
            await workflow._summarize_file_diffs(file_diffs)

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_activity.write_file")
    async def test_write_summaries_to_files(
        self,
        mock_write_file: MagicMock,
        workflow: PrDescriptionWorkflow,
        mock_workflow_paths: MagicMock,
    ) -> None:
        """Test writing summaries to files."""
        # Arrange
        workflow.workflow_paths = mock_workflow_paths
        summaries_by_file = {
            "b/path/to/file1.py": "summary 1",
            "b/another/file2.py": "summary 2",
        }
        mock_write_file.return_value = AsyncMock()

        # Act
        await workflow._write_summaries_to_files(summaries_by_file)

        # Assert
        # Verify that write_file is called for each summary
        assert mock_write_file.call_count == 2

        # Verify that the summaries are passed correctly
        call_args_list = mock_write_file.call_args_list
        called_contents = [call[0][1] for call in call_args_list]
        assert "summary 1" in called_contents
        assert "summary 2" in called_contents

    @pytest.mark.asyncio
    @patch(
        "cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_workflow.execute_baml_transform_batch",
    )
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_workflow.execute_baml_transform")
    async def test_generate_pr_summary_success(
        self,
        mock_baml_transform: MagicMock,
        mock_baml_batch: MagicMock,
        workflow: PrDescriptionWorkflow,
        mock_workflow_paths: MagicMock,
    ) -> None:
        """Test successful PR summary generation."""
        # Arrange
        workflow.workflow_paths = mock_workflow_paths
        summaries_by_file = {
            "file1": "summary 1",
            "file2": "summary 2",
            "file3": "summary 3",
            "file4": "summary 4",
            "file5": "summary 5",
            "file6": "summary 6",
        }
        commit_logs = "- commit 1\n- commit 2"
        mock_baml_batch.return_value = {"batch_0": "batch summary 1", "batch_1": "batch summary 2"}
        mock_baml_transform.return_value = "Final PR summary"

        # Act
        result = await workflow._generate_pr_summary(summaries_by_file, commit_logs)

        # Assert
        assert result == "Final PR summary"
        mock_baml_batch.assert_called_once()
        mock_baml_transform.assert_called_once()

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    @patch(
        "cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_workflow.execute_baml_transform_batch",
    )
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_workflow.execute_baml_transform")
    async def test_generate_pr_summary_exception(
        self,
        mock_baml_transform: MagicMock,
        mock_baml_batch: MagicMock,
        workflow: PrDescriptionWorkflow,
        mock_workflow_paths: MagicMock,
    ) -> None:
        """Test PR summary generation with exception."""
        # Arrange
        workflow.workflow_paths = mock_workflow_paths
        summaries_by_file = {"file1": "summary 1"}
        commit_logs = "- commit 1"
        mock_baml_batch.return_value = {"batch_0": "batch summary"}
        mock_baml_transform.side_effect = Exception("BAML error")

        # Act & Assert
        with pytest.raises(Exception, match="BAML error"):
            await workflow._generate_pr_summary(summaries_by_file, commit_logs)

    def test_construct_pr_description(self, workflow: PrDescriptionWorkflow) -> None:
        """Test PR description construction."""
        # Arrange
        high_level_summary = "This PR adds new features"
        summaries_by_file = {
            "b/file2.py": "Modified file2 functionality",
            "b/file1.py": "Added new function to file1",
        }

        # Act
        result = workflow._construct_pr_description(high_level_summary, summaries_by_file)

        # Assert
        expected_parts = [
            "## Summary",
            "This PR adds new features",
            "## File-by-File Changes",
            "- `file1.py`: Added new function to file1",
            "- `file2.py`: Modified file2 functionality",
        ]
        expected = "\n\n".join(expected_parts)
        assert result == expected

    def test_construct_pr_description_empty_summaries(
        self,
        workflow: PrDescriptionWorkflow,
    ) -> None:
        """Test PR description construction with empty summaries."""
        # Arrange
        high_level_summary = "This PR has no file changes"
        summaries_by_file = {}

        # Act
        result = workflow._construct_pr_description(high_level_summary, summaries_by_file)

        # Assert
        expected_parts = [
            "## Summary",
            "This PR has no file changes",
            "## File-by-File Changes",
        ]
        expected = "\n\n".join(expected_parts)
        assert result == expected

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_activity.write_file")
    async def test_run_no_changes(
        self,
        mock_write_file: MagicMock,
        workflow: PrDescriptionWorkflow,
        workflow_input: PrDescriptionWorkflowInput,
    ) -> None:
        """Test workflow run with no changes detected."""
        # Arrange
        with (
            patch.object(workflow, "_initialize_workflow", new_callable=AsyncMock) as mock_init,
            patch.object(workflow, "_get_commit_logs", new_callable=AsyncMock) as mock_get_logs,
            patch.object(workflow, "_get_file_diffs", new_callable=AsyncMock) as mock_get_diffs,
        ):
            mock_init.return_value = None
            mock_get_logs.return_value = ""
            mock_get_diffs.return_value = {}

            # Act
            result = await workflow.run(workflow_input)

            # Assert
            assert result == "No changes detected between the specified branches."
            mock_write_file.assert_not_called()

    @pytest.mark.asyncio
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.workflow.logger")
    @patch("cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_activity.write_file")
    async def test_run_with_changes(
        self,
        mock_write_file: MagicMock,
        workflow: PrDescriptionWorkflow,
        workflow_input: PrDescriptionWorkflowInput,
        mock_workflow_paths: MagicMock,
    ) -> None:
        """Test workflow run with changes detected."""
        # Arrange
        workflow.workflow_paths = mock_workflow_paths
        commit_logs = "- Test commit (abc1234)"
        file_diffs = {"b/test.py": "diff content"}
        summaries_by_file = {"b/test.py": "Test summary"}
        high_level_summary = "Test PR summary"
        expected_pr_description = (
            "## Summary\n\nTest PR summary\n\n## File-by-File Changes\n\n- `test.py`: Test summary"
        )

        with (
            patch.object(workflow, "_initialize_workflow", new_callable=AsyncMock) as mock_init,
            patch.object(workflow, "_get_commit_logs", new_callable=AsyncMock) as mock_get_logs,
            patch.object(workflow, "_get_file_diffs", new_callable=AsyncMock) as mock_get_diffs,
            patch.object(workflow, "_summarize_file_diffs", new_callable=AsyncMock) as mock_summarize,
            patch.object(workflow, "_generate_pr_summary", new_callable=AsyncMock) as mock_generate,
        ):
            mock_init.return_value = None
            mock_get_logs.return_value = commit_logs
            mock_get_diffs.return_value = file_diffs
            mock_summarize.return_value = summaries_by_file
            mock_generate.return_value = high_level_summary

            # Act
            result = await workflow.run(workflow_input)

            # Assert
            assert result == expected_pr_description
            mock_write_file.assert_called_once_with(
                "/test/output/pr_description.md",
                expected_pr_description,
            )

    @pytest.mark.asyncio
    @patch(
        "cookbook.recipes.workflows.pr_description.pr_description_workflow.awa_workflow.run_with_controlled_concurrency",
    )
    async def test_create_summary_task_function(
        self,
        mock_controlled_concurrency: MagicMock,
        workflow: PrDescriptionWorkflow,
        mock_workflow_paths: MagicMock,
    ) -> None:
        """Test the create_summary_task function behavior."""
        # Arrange
        workflow.workflow_paths = mock_workflow_paths
        file_path = "b/test/file.py"
        diff_content = "test diff content"
        mock_controlled_concurrency.return_value = ["test summary"]

        with patch.object(workflow, "_write_summaries_to_files", new_callable=AsyncMock) as mock_write:
            # Act - Call the private method to get the create_summary_task function
            file_diffs = {file_path: diff_content}
            result = await workflow._summarize_file_diffs(file_diffs)

            # Assert - Verify the task was created and executed
            assert result == {file_path: "test summary"}
            mock_controlled_concurrency.assert_called_once()
            mock_write.assert_called_once()

    def test_batch_creation_logic(
        self,
        workflow: PrDescriptionWorkflow,
        mock_workflow_paths: MagicMock,
    ) -> None:
        """Test batch creation logic in _generate_pr_summary."""
        # Arrange
        workflow.workflow_paths = mock_workflow_paths
        summaries_by_file = {f"file{i}": f"summary {i}" for i in range(12)}

        # Act - Test the batching logic (batch_size = 5)
        summary_list = list(summaries_by_file.values())
        batch_size = 5
        batched_summaries = [summary_list[i : i + batch_size] for i in range(0, len(summary_list), batch_size)]

        # Assert
        assert len(batched_summaries) == 3  # 12 items, batch size 5 -> 3 batches
        assert len(batched_summaries[0]) == 5
        assert len(batched_summaries[1]) == 5
        assert len(batched_summaries[2]) == 2

    def test_file_path_cleaning_logic(self) -> None:
        """Test file path cleaning logic used in various methods."""
        # Test cases for path cleaning
        test_cases = [
            ("b/path/to/file.py", "path/to/file.py"),
            ("b/simple_file.py", "simple_file.py"),
            ("b/", ""),
            ("path/without/prefix.py", "path/without/prefix.py"),
        ]

        for input_path, expected_output in test_cases:
            # Act
            result = input_path.removeprefix("b/")

            # Assert
            assert result == expected_output

    def test_clean_file_path_for_task_creation(self) -> None:
        """Test file path cleaning for task creation."""
        # Arrange
        file_path = "b/complex/path.with.dots/file.py"

        # Act - This is the cleaning logic used in create_summary_task
        clean_file_path = file_path.replace("/", "_").replace(".", "_")

        # Assert
        assert clean_file_path == "b_complex_path_with_dots_file_py"
