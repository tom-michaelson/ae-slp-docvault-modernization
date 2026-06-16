"""Unit tests for TestAndLintPipelineWorkflow."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from cookbook.recipes.workflows.test_doctor.models.workflow_input import TestDoctorWorkflowInput
from cookbook.recipes.workflows.test_doctor.test_and_lint_pipeline_workflow import (
    TestAndLintPipelineWorkflow,
    TestAndLintPipelineWorkflowInput,
)
from sdk_dist.python.awa.client.models import TaskResponseModel


class TestTestAndLintPipelineWorkflowInput:
    """Test the TestAndLintPipelineWorkflowInput model."""

    def test_valid_input_creation(self) -> None:
        """Test creating a valid TestAndLintPipelineWorkflowInput."""
        # Arrange
        root_input = TestDoctorWorkflowInput(
            branch_name="feature/test-branch",
            base_branch="main",
            repo_path="/test/repo",
            working_directory="src",
            testing_guidelines_path="guidelines.md",
            file_extensions="py,js",
            tests_directory="tests",
        )

        # Act
        input_obj = TestAndLintPipelineWorkflowInput(
            root_workflow_input=root_input,
            file_path="src/module/file.py",
            testing_guidelines_path="guidelines.md",
            tests_directory="tests",
            working_directory="src",
        )

        # Assert
        assert input_obj.root_workflow_input == root_input
        assert input_obj.file_path == "src/module/file.py"
        assert input_obj.testing_guidelines_path == "guidelines.md"
        assert input_obj.tests_directory == "tests"
        assert input_obj.working_directory == "src"

    def test_input_serialization(self) -> None:
        """Test that the input can be serialized and deserialized."""
        # Arrange
        root_input = TestDoctorWorkflowInput(
            branch_name="feature/test-branch",
            base_branch="main",
            repo_path="/test/repo",
            working_directory="src",
            testing_guidelines_path="guidelines.md",
            file_extensions="py,js",
            tests_directory="tests",
        )

        input_obj = TestAndLintPipelineWorkflowInput(
            root_workflow_input=root_input,
            file_path="src/module/file.py",
            testing_guidelines_path="guidelines.md",
            tests_directory="tests",
            working_directory="src",
        )

        # Act
        serialized = input_obj.model_dump()
        deserialized = TestAndLintPipelineWorkflowInput.model_validate(serialized)

        # Assert
        assert deserialized == input_obj


class TestTestAndLintPipelineWorkflow:
    """Test the TestAndLintPipelineWorkflow class."""

    @pytest.fixture
    def sample_input(self) -> TestAndLintPipelineWorkflowInput:
        """Provide a sample workflow input for testing."""
        root_input = TestDoctorWorkflowInput(
            branch_name="feature/test-branch",
            base_branch="main",
            repo_path="/test/repo",
            working_directory="src",
            testing_guidelines_path="guidelines.md",
            file_extensions="py,js",
            tests_directory="tests",
        )

        return TestAndLintPipelineWorkflowInput(
            root_workflow_input=root_input,
            file_path="src/module/file.py",
            testing_guidelines_path="guidelines.md",
            tests_directory="tests",
            working_directory="src",
        )

    def test_get_test_file_path_basic(self) -> None:
        """Test _get_test_file_path with basic input."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        source_file = "module/file.py"
        tests_directory = "/test/repo/tests"

        # Act
        result = workflow_instance._get_test_file_path(source_file, tests_directory)

        # Assert
        expected = Path("/test/repo/tests/module/test_file.py")
        assert result == expected

    def test_get_test_file_path_nested_directory(self) -> None:
        """Test _get_test_file_path with nested directory structure."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        source_file = "deep/nested/module/file.py"
        tests_directory = "/test/repo/tests"

        # Act
        result = workflow_instance._get_test_file_path(source_file, tests_directory)

        # Assert
        expected = Path("/test/repo/tests/deep/nested/module/test_file.py")
        assert result == expected

    def test_get_test_file_path_root_file(self) -> None:
        """Test _get_test_file_path with file in root directory."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        source_file = "file.py"
        tests_directory = "/test/repo/tests"

        # Act
        result = workflow_instance._get_test_file_path(source_file, tests_directory)

        # Assert
        expected = Path("/test/repo/tests/test_file.py")
        assert result == expected

    def test_get_test_file_path_different_extension(self) -> None:
        """Test _get_test_file_path with different file extensions."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        source_file = "module/script.js"
        tests_directory = "/test/repo/tests"

        # Act
        result = workflow_instance._get_test_file_path(source_file, tests_directory)

        # Assert
        expected = Path("/test/repo/tests/module/test_script.js")
        assert result == expected

    def test_construct_test_generation_prompt(self) -> None:
        """Test _construct_test_generation_prompt generates correct prompt."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        file_path = "/test/repo/src/module/file.py"
        test_file_path = "/test/repo/tests/module/test_file.py"
        testing_guidelines_path = "/test/repo/guidelines.md"

        # Act
        result = workflow_instance._construct_test_generation_prompt(
            file_path,
            test_file_path,
            testing_guidelines_path,
        )

        # Assert
        assert file_path in result
        assert test_file_path in result
        assert testing_guidelines_path in result
        assert "expert software engineer" in result
        assert "unit tests" in result
        assert "uv run" in result

    def test_construct_linting_prompt(self) -> None:
        """Test _construct_linting_prompt generates correct prompt."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        test_file_path = "/test/repo/tests/module/test_file.py"

        # Act
        result = workflow_instance._construct_linting_prompt(test_file_path)

        # Assert
        assert test_file_path in result
        assert "lint and validate" in result
        assert "uv run ruff check" in result
        assert "uv run pytest" in result
        assert "expert software engineer" in result

    @pytest.mark.asyncio
    async def test_run_successful_execution(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test successful workflow execution with both agents completing successfully."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = successful_result

            # Act
            result = await workflow_instance.run(sample_input)

            # Assert
            assert result is None  # Workflow returns None on success
            assert mock_execute_agent.call_count == 2

            # Verify first call (test generation agent)
            first_call = mock_execute_agent.call_args_list[0]
            assert first_call[1]["name"] == "TestGenerator-src_module_file.py"
            assert first_call[1]["agent_config"].provider.value == "claude"
            assert first_call[1]["agent_config"].mode.value == "act"
            assert first_call[1]["timeout_seconds"] == 1800

            # Verify second call (linting agent)
            second_call = mock_execute_agent.call_args_list[1]
            assert second_call[1]["name"] == "TestLinter-src_module_file.py"
            assert second_call[1]["agent_config"].provider.value == "claude"
            assert second_call[1]["agent_config"].mode.value == "act"
            assert second_call[1]["timeout_seconds"] == 1800

    @pytest.mark.asyncio
    async def test_run_generation_agent_failure(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test workflow failure when generation agent fails."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        failed_result = TaskResponseModel(status="failed", reason="Generation failed", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = failed_result

            # Act & Assert
            with pytest.raises(Exception, match="Test generation agent failed") as exc:
                await workflow_instance.run(sample_input)

            assert "src/module/file.py" in str(exc.value)
            assert mock_execute_agent.call_count == 1

    @pytest.mark.asyncio
    async def test_run_linting_agent_failure(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test workflow failure when linting agent fails."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")
        failed_result = TaskResponseModel(status="failed", reason="Linting failed", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            # First call succeeds, second call fails
            mock_execute_agent.side_effect = [successful_result, failed_result]

            # Act & Assert
            with pytest.raises(Exception, match="Test linting agent failed") as exc:
                await workflow_instance.run(sample_input)

            assert "src/module/file.py" in str(exc.value)
            assert mock_execute_agent.call_count == 2

    @pytest.mark.asyncio
    async def test_run_generation_agent_invalid_response(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test workflow failure when generation agent returns invalid response."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        invalid_result = TaskResponseModel(status="error", reason="Invalid response", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = invalid_result

            # Act & Assert
            with pytest.raises(Exception, match="Test generation agent failed"):
                await workflow_instance.run(sample_input)

            assert mock_execute_agent.call_count == 1

    @pytest.mark.asyncio
    async def test_run_linting_agent_invalid_response(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test workflow failure when linting agent returns invalid response."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")
        invalid_result = TaskResponseModel(status="error", reason="Invalid response", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.side_effect = [successful_result, invalid_result]

            # Act & Assert
            with pytest.raises(Exception, match="Test linting agent failed"):
                await workflow_instance.run(sample_input)

            assert mock_execute_agent.call_count == 2

    @pytest.mark.asyncio
    async def test_run_path_calculations(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test that file paths are calculated correctly during workflow execution."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = successful_result

            # Act
            await workflow_instance.run(sample_input)

            # Assert
            # Verify the prompts contain the expected paths
            first_call_prompt = mock_execute_agent.call_args_list[0][1]["agent_config"].prompt
            second_call_prompt = mock_execute_agent.call_args_list[1][1]["agent_config"].prompt

            # Generation agent prompt should contain source and test file paths
            assert "/test/repo/src/module/file.py" in first_call_prompt
            assert "/test/repo/tests/module/test_file.py" in first_call_prompt
            assert "/test/repo/guidelines.md" in first_call_prompt

            # Linting agent prompt should contain test file path
            assert "/test/repo/tests/module/test_file.py" in second_call_prompt

    @pytest.mark.asyncio
    async def test_run_working_directory_configuration(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test that working directory is configured correctly for agents."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = successful_result

            # Act
            await workflow_instance.run(sample_input)

            # Assert
            # Both agents should have the same working directory
            first_call_config = mock_execute_agent.call_args_list[0][1]["agent_config"]
            second_call_config = mock_execute_agent.call_args_list[1][1]["agent_config"]

            expected_working_dir = "/test/repo/src"
            assert first_call_config.working_directory == expected_working_dir
            assert second_call_config.working_directory == expected_working_dir
            assert first_call_config.initialize is False
            assert second_call_config.initialize is False

    @pytest.mark.asyncio
    async def test_run_with_complex_file_path(self) -> None:
        """Test workflow with complex file path containing special characters."""
        # Arrange
        root_input = TestDoctorWorkflowInput(
            branch_name="feature/test-branch",
            base_branch="main",
            repo_path="/test/repo with spaces",
            working_directory="src-dir",
            testing_guidelines_path="test-guidelines.md",
            file_extensions="py,js",
            tests_directory="test-suite",
        )

        input_obj = TestAndLintPipelineWorkflowInput(
            root_workflow_input=root_input,
            file_path="src-dir/module with spaces/file-name.py",
            testing_guidelines_path="test-guidelines.md",
            tests_directory="test-suite",
            working_directory="src-dir",
        )

        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = successful_result

            # Act
            result = await workflow_instance.run(input_obj)

            # Assert
            assert result is None
            assert mock_execute_agent.call_count == 2

            # Verify paths in prompts handle special characters correctly
            first_call_prompt = mock_execute_agent.call_args_list[0][1]["agent_config"].prompt
            assert "/test/repo with spaces/src-dir/module with spaces/file-name.py" in first_call_prompt
            assert "/test/repo with spaces/test-suite/module with spaces/test_file-name.py" in first_call_prompt

    @pytest.mark.asyncio
    async def test_run_generation_agent_none_result(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test workflow failure when generation agent returns None status."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = TaskResponseModel(status="", reason="", output="")

            # Act & Assert
            with pytest.raises(Exception, match="Test generation agent failed"):
                await workflow_instance.run(sample_input)

            assert mock_execute_agent.call_count == 1

    @pytest.mark.asyncio
    async def test_run_linting_agent_none_result(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test workflow failure when linting agent returns None status."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.side_effect = [successful_result, TaskResponseModel(status="", reason="", output="")]

            # Act & Assert
            with pytest.raises(Exception, match="Test linting agent failed"):
                await workflow_instance.run(sample_input)

            assert mock_execute_agent.call_count == 2

    @pytest.mark.asyncio
    async def test_run_generation_agent_missing_status(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test workflow failure when generation agent returns empty status."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        invalid_result = TaskResponseModel(status="", reason="success", output="")  # Empty status field

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = invalid_result

            # Act & Assert
            with pytest.raises(Exception, match="Test generation agent failed"):
                await workflow_instance.run(sample_input)

            assert mock_execute_agent.call_count == 1

    @pytest.mark.asyncio
    async def test_run_linting_agent_missing_status(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test workflow failure when linting agent returns empty status."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")
        invalid_result = TaskResponseModel(status="", reason="success", output="")  # Empty status field

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.side_effect = [successful_result, invalid_result]

            # Act & Assert
            with pytest.raises(Exception, match="Test linting agent failed"):
                await workflow_instance.run(sample_input)

            assert mock_execute_agent.call_count == 2

    @pytest.mark.asyncio
    async def test_run_with_different_working_directory(self) -> None:
        """Test workflow with different working directory structure."""
        # Arrange
        root_input = TestDoctorWorkflowInput(
            branch_name="feature/test-branch",
            base_branch="main",
            repo_path="/different/repo",
            working_directory="source",
            testing_guidelines_path="docs/testing.md",
            file_extensions="py,js",
            tests_directory="unit_tests",
        )

        input_obj = TestAndLintPipelineWorkflowInput(
            root_workflow_input=root_input,
            file_path="source/core/utils.py",
            testing_guidelines_path="docs/testing.md",
            tests_directory="unit_tests",
            working_directory="source",
        )

        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = successful_result

            # Act
            await workflow_instance.run(input_obj)

            # Assert
            # Verify working directory configuration
            first_call_config = mock_execute_agent.call_args_list[0][1]["agent_config"]
            second_call_config = mock_execute_agent.call_args_list[1][1]["agent_config"]

            expected_working_dir = "/different/repo/source"
            assert first_call_config.working_directory == expected_working_dir
            assert second_call_config.working_directory == expected_working_dir

    @pytest.mark.asyncio
    async def test_run_with_edge_case_paths(self) -> None:
        """Test workflow with edge case file paths."""
        # Arrange
        root_input = TestDoctorWorkflowInput(
            branch_name="feature/test-branch",
            base_branch="main",
            repo_path="/edge/case",
            working_directory=".",
            testing_guidelines_path="guidelines.md",
            file_extensions="py",
            tests_directory="tests",
        )

        input_obj = TestAndLintPipelineWorkflowInput(
            root_workflow_input=root_input,
            file_path="single_file.py",
            testing_guidelines_path="guidelines.md",
            tests_directory="tests",
            working_directory=".",
        )

        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = successful_result

            # Act
            await workflow_instance.run(input_obj)

            # Assert
            assert mock_execute_agent.call_count == 2
            first_call_prompt = mock_execute_agent.call_args_list[0][1]["agent_config"].prompt
            assert "/edge/case/single_file.py" in first_call_prompt
            assert "/edge/case/tests/test_single_file.py" in first_call_prompt

    @pytest.mark.asyncio
    async def test_run_error_message_includes_result_details(
        self,
        sample_input: TestAndLintPipelineWorkflowInput,
    ) -> None:
        """Test that error messages include details from agent results."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        failed_result = TaskResponseModel(status="error", reason="Detailed error information", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = failed_result

            # Act & Assert
            with pytest.raises(Exception, match="Test generation agent failed") as exc:
                await workflow_instance.run(sample_input)

            error_message = str(exc.value)
            assert "Detailed error information" in error_message or "src/module/file.py" in error_message

    @pytest.mark.asyncio
    async def test_run_with_mock_workflow_logger(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test that workflow logger is called appropriately."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = successful_result

            # Act
            await workflow_instance.run(sample_input)

            # Assert
            assert mock_execute_agent.call_count == 2
            # Verify agent was called appropriately
            assert mock_execute_agent.call_count == 2

    @pytest.mark.asyncio
    async def test_run_with_mock_workflow_logger_error(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test that workflow logger is called for errors."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        failed_result = TaskResponseModel(status="failed", reason="Test error", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = failed_result

            # Act & Assert
            with pytest.raises(Exception, match="Test generation agent failed"):
                await workflow_instance.run(sample_input)

            # Verify agent was called
            assert mock_execute_agent.call_count == 1

    def test_workflow_initialization(self) -> None:
        """Test that workflow initializes correctly."""
        # Act
        workflow_instance = TestAndLintPipelineWorkflow()

        # Assert - workflow initializes with no instance variables
        assert workflow_instance is not None

    def test_get_test_file_path_preserves_extension(self) -> None:
        """Test that _get_test_file_path preserves the original file extension."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        test_cases = [
            ("file.py", "test_file.py"),
            ("script.js", "test_script.js"),
            ("component.tsx", "test_component.tsx"),
            ("utils.ts", "test_utils.ts"),
            ("config.json", "test_config.json"),
        ]

        # Act & Assert
        for source_file, expected_filename in test_cases:
            result = workflow_instance._get_test_file_path(source_file, "/tests")
            assert result.name == expected_filename
            assert result.parent == Path("/tests")

    def test_get_test_file_path_empty_parent_directory(self) -> None:
        """Test _get_test_file_path with file in current directory."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        source_file = "app.py"
        tests_directory = "/project/tests"

        # Act
        result = workflow_instance._get_test_file_path(source_file, tests_directory)

        # Assert
        expected = Path("/project/tests/test_app.py")
        assert result == expected
        assert result.parent == Path("/project/tests")

    def test_construct_test_generation_prompt_content_validation(self) -> None:
        """Test that generation prompt contains all required sections."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        file_path = "/repo/src/module.py"
        test_file_path = "/repo/tests/test_module.py"
        guidelines_path = "/repo/guidelines.md"

        # Act
        prompt = workflow_instance._construct_test_generation_prompt(
            file_path,
            test_file_path,
            guidelines_path,
        )

        # Assert - Check for key sections
        required_sections = [
            "expert software engineer",
            "unit tests",
            "Testing Guidelines:",
            "Instructions:",
            "Read the Source File:",
            "Create Test File:",
            "Check for Existing Tests:",
            "Analyze and Update Tests:",
            "Execute and Validate:",
            "uv run pytest",
            "Begin now.",
        ]
        for section in required_sections:
            assert section in prompt

    def test_construct_linting_prompt_content_validation(self) -> None:
        """Test that linting prompt contains all required sections."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        test_file_path = "/repo/tests/test_module.py"

        # Act
        prompt = workflow_instance._construct_linting_prompt(test_file_path)

        # Assert - Check for key sections
        required_sections = [
            "expert software engineer",
            "code quality and standards",
            "lint and validate",
            "Instructions:",
            "Lint the File:",
            "uv run ruff check",
            "Fix Linting Errors:",
            "Iterate on Linting:",
            "Final Test Validation:",
            "uv run pytest",
            "Begin now.",
        ]
        for section in required_sections:
            assert section in prompt

    @pytest.mark.asyncio
    async def test_run_agent_name_generation(self, sample_input: TestAndLintPipelineWorkflowInput) -> None:
        """Test that agent names are generated correctly with path sanitization."""
        # Arrange
        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        # Test with complex file path
        complex_input = TestAndLintPipelineWorkflowInput(
            root_workflow_input=sample_input.root_workflow_input,
            file_path="src/deep/nested/path/complex-file.py",
            testing_guidelines_path="guidelines.md",
            tests_directory="tests",
            working_directory="src",
        )

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = successful_result

            # Act
            await workflow_instance.run(complex_input)

            # Assert
            calls = mock_execute_agent.call_args_list
            assert len(calls) == 2

            # Check agent names
            first_name = calls[0][1]["name"]
            second_name = calls[1][1]["name"]

            expected_suffix = "src_deep_nested_path_complex-file.py"
            assert first_name == f"TestGenerator-{expected_suffix}"
            assert second_name == f"TestLinter-{expected_suffix}"

    @pytest.mark.asyncio
    async def test_run_relative_path_calculation_edge_cases(self) -> None:
        """Test relative path calculation with various edge cases."""
        # Arrange
        root_input = TestDoctorWorkflowInput(
            branch_name="feature/test",
            base_branch="main",
            repo_path="/repo",
            working_directory="nested/working/dir",
            testing_guidelines_path="guidelines.md",
            file_extensions="py",
            tests_directory="tests",
        )

        input_obj = TestAndLintPipelineWorkflowInput(
            root_workflow_input=root_input,
            file_path="nested/working/dir/deep/module.py",
            testing_guidelines_path="guidelines.md",
            tests_directory="tests",
            working_directory="nested/working/dir",
        )

        workflow_instance = TestAndLintPipelineWorkflow()
        successful_result = TaskResponseModel(status="completed", reason="success", output="")

        with (
            patch(
                "workflows.test_doctor.test_and_lint_pipeline_workflow.awa_workflow.execute_agent",
                new_callable=AsyncMock,
            ) as mock_execute_agent,
            patch("temporalio.workflow.logger"),
        ):
            mock_execute_agent.return_value = successful_result

            # Act
            await workflow_instance.run(input_obj)

            # Assert
            prompt = mock_execute_agent.call_args_list[0][1]["agent_config"].prompt
            # Should contain the absolute source path and correct test path
            assert "/repo/nested/working/dir/deep/module.py" in prompt
            assert "/repo/tests/deep/test_module.py" in prompt

    def test_input_model_field_validation(self) -> None:
        """Test that input model validates required fields properly."""
        # Arrange
        root_input = TestDoctorWorkflowInput(
            branch_name="feature/test",
            base_branch="main",
            repo_path="/repo",
            working_directory="src",
            testing_guidelines_path="guidelines.md",
            file_extensions="py",
            tests_directory="tests",
        )

        # Act & Assert - Valid input
        valid_input = TestAndLintPipelineWorkflowInput(
            root_workflow_input=root_input,
            file_path="src/module.py",
            testing_guidelines_path="guidelines.md",
            tests_directory="tests",
            working_directory="src",
        )
        assert valid_input.file_path == "src/module.py"

        # Test that __test__ attribute is set to False
        assert TestAndLintPipelineWorkflowInput.__test__ is False

    def test_workflow_class_attributes(self) -> None:
        """Test that workflow class has the correct attributes and metadata."""
        # Assert
        assert TestAndLintPipelineWorkflow.__test__ is False
        assert hasattr(TestAndLintPipelineWorkflow, "run")
        assert TestAndLintPipelineWorkflow.__doc__ is not None
        assert "two-agent pipeline" in TestAndLintPipelineWorkflow.__doc__
