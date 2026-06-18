from pathlib import Path

from pydantic import BaseModel
from temporalio import workflow

from sdk_dist.python.awa.client import awa_workflow
from sdk_dist.python.awa.client.models import AgentConfiguration, AgentModeEnum, AgentProviderEnum, TaskResponseModel

from .models.workflow_input import TestDoctorWorkflowInput


class TestGenerationError(Exception):
    """Raised when test generation fails."""


class TestLintingError(Exception):
    """Raised when test linting fails."""


class TestAndLintPipelineWorkflowInput(BaseModel):
    """Input for the TestAndLintPipelineWorkflow."""

    __test__ = False

    root_workflow_input: TestDoctorWorkflowInput
    file_path: str
    testing_guidelines_path: str
    tests_directory: str
    working_directory: str


@workflow.defn(name="test-and-lint-pipeline")
class TestAndLintPipelineWorkflow:
    """Workflow that generates, lints, and validates unit tests for a single file using a two-agent pipeline.

    This workflow implements a two-stage process for creating comprehensive unit tests:
    1. Test Generation Agent: Reads the source file and creates/updates unit tests
    2. Test Linting Agent: Applies code quality standards and validates the tests

    The workflow ensures that generated tests follow project guidelines, pass linting,
    and execute successfully before completion.
    """

    __test__ = False

    def __init__(self) -> None:
        """Initialize the workflow."""

    @workflow.run
    async def run(self, workflow_input: TestAndLintPipelineWorkflowInput) -> None:
        """Generate, lint, and validate tests for a single file using a two-agent pipeline."""
        repo_path = Path(workflow_input.root_workflow_input.repo_path)
        agent_working_dir = str(repo_path / workflow_input.working_directory)
        tests_dir_abs = repo_path / workflow_input.root_workflow_input.tests_directory

        # Calculate the source file's path relative to the defined working directory
        # to ensure the test path is mirrored correctly.
        source_file_rel_to_working_dir = Path(workflow_input.file_path).relative_to(
            workflow_input.working_directory,
        )

        test_file_path = self._get_test_file_path(
            str(source_file_rel_to_working_dir),
            str(tests_dir_abs),
        )

        source_file_abs = repo_path / workflow_input.file_path

        # Agent 1: Generate and validate tests
        generation_prompt = self._construct_test_generation_prompt(
            str(source_file_abs),
            str(test_file_path),
            str(repo_path / workflow_input.root_workflow_input.testing_guidelines_path),
        )
        generation_agent_config = AgentConfiguration(
            provider=AgentProviderEnum.CLAUDE,
            mode=AgentModeEnum.ACT,
            prompt=generation_prompt,
            initialize=False,
            working_directory=agent_working_dir,
        )
        generation_agent_result: TaskResponseModel = await awa_workflow.execute_agent(
            agent_config=generation_agent_config,
            timeout_seconds=1800,
            name=f"TestGenerator-{workflow_input.file_path.replace('/', '_')}",
        )
        if generation_agent_result.status != "completed":
            error_message = (
                f"Test generation agent failed for {workflow_input.file_path}. Result: {generation_agent_result}"
            )
            workflow.logger.error(error_message)
            raise TestGenerationError(error_message)
        workflow.logger.info(f"Test generation agent succeeded for {workflow_input.file_path}.")

        # Agent 2: Lint and re-validate tests
        linting_prompt = self._construct_linting_prompt(str(test_file_path))
        linting_agent_config = AgentConfiguration(
            provider=AgentProviderEnum.CLAUDE,
            mode=AgentModeEnum.ACT,
            prompt=linting_prompt,
            initialize=False,
            working_directory=agent_working_dir,
        )
        linting_agent_result: TaskResponseModel = await awa_workflow.execute_agent(
            agent_config=linting_agent_config,
            timeout_seconds=1800,
            name=f"TestLinter-{workflow_input.file_path.replace('/', '_')}",
        )
        if linting_agent_result.status != "completed":
            error_message = f"Test linting agent failed for {workflow_input.file_path}. Result: {linting_agent_result}"
            workflow.logger.error(error_message)
            raise TestLintingError(error_message)

        workflow.logger.info(f"Agent pipeline successfully completed for {workflow_input.file_path}.")

    def _get_test_file_path(self, source_file: str, tests_directory: str) -> Path:
        """Determine the path for a new test file based on the source file."""
        p = Path(source_file)
        # Always prepend "test_" to the source file name to ensure a unique test file.
        file_name = f"test_{p.name}"
        # Construct path relative to tests_directory
        return Path(tests_directory) / p.parent / file_name

    def _construct_test_generation_prompt(
        self,
        file_path: str,
        test_file_path: str,
        testing_guidelines_path: str,
    ) -> str:
        """Construct the prompt for the test generation agent."""
        return f"""
You are an expert software engineer specializing in writing comprehensive and robust unit tests.
Your task is to write unit tests for the file located at: `{file_path}`.

**Testing Guidelines:**
You can find the testing guidelines and best practices in the file located at \
`{testing_guidelines_path}`. You are required to read this file and MUST adhere to its rules.

**Instructions:**
1.  **Read the Source File:** First, read the content of the source file at `{file_path}` \
to understand its functionality.
2.  **Create Test File:** Create a new test file at the following exact path: `{test_file_path}`.
3.  **Check for Existing Tests:** Check if a test file already exists at the determined path.
4.  **Analyze and Update Tests:**
    *   If a test file exists, review its contents to ensure it is comprehensive and covers \
all functionality, edge cases, and potential failure modes in the source file. If the tests \
are not comprehensive, update the file by adding the necessary tests.
    *   If no test file exists, create a new one at the determined path and write \
comprehensive unit tests.
5.  **Focus:** Your work must be confined to the single test file for `{file_path}`. \
Do not modify any other files.
6.  **Execute and Validate:** Run all tests in the file using the command \
`uv run pytest {test_file_path}`.
7.  **Iterate and Fix:** If any tests fail, you must debug the test code (not the source code) \
and fix it. Repeat step 7 until all tests pass.
8.  **Final Verification:** Conclude your task only when all tests in the file pass successfully.

Begin now.
"""

    def _construct_linting_prompt(self, test_file_path: str) -> str:
        """Construct the prompt for the linting and validation agent."""
        return f"""
You are an expert software engineer specializing in code quality and standards.
Your task is to lint and validate the test file located at: `{test_file_path}`.

**Instructions:**
1.  **Lint the File:** Run the linter on the test file using the command \
`uv run ruff check {test_file_path}`.
2.  **Fix Linting Errors:** If the linter reports any errors, you must fix them. You can \
attempt to fix them automatically with `uv run ruff check --fix {test_file_path}` or by \
editing the file manually.
3.  **Iterate on Linting:** Repeat steps 1 and 2 until the linter reports no errors.
4.  **Final Test Validation:** After all linting errors are fixed, run the tests one last time \
using `uv run pytest {test_file_path}` to ensure your changes have not introduced any regressions.
5.  **Fix Failing Tests:** If any tests fail, you must fix the test code until all tests pass.
6.  **Conclusion:** Conclude your task only when the file has no linting errors and all tests pass.

Begin now.
"""
