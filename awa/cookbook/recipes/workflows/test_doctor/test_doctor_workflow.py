from datetime import timedelta
from pathlib import Path
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    import json

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from sdk_dist.python.awa.client import awa_activity, awa_general, awa_workflow

from .models.workflow_input import TestDoctorWorkflowInput
from .test_and_lint_pipeline_workflow import TestAndLintPipelineWorkflow, TestAndLintPipelineWorkflowInput


@recipe_exposed("Generates unit tests for changed files in a pull request")
@workflow.defn(name="test-doctor")
class TestDoctorWorkflow:
    """Workflow to generate unit tests for changed files in a pull request."""

    __test__ = False

    def __init__(self) -> None:
        """Initialize the TestDoctorWorkflow."""
        self.mcp_config: dict[str, Any] = {}
        self.workflow_paths: Any = None
        self.retry_policy: RetryPolicy | None = None

    @workflow.run
    async def run(self, workflow_input: TestDoctorWorkflowInput) -> str:
        """Execute the workflow to generate unit tests."""
        await self._initialize_workflow()

        changed_files = await self._get_changed_files(workflow_input)

        if not changed_files:
            workflow.logger.info("No changes detected between branches. Skipping test generation.")
            return "No changes detected between the specified branches."

        testable_files = self._filter_testable_files(
            changed_files,
            workflow_input.file_extensions,
            workflow_input.tests_directory,
        )

        if not testable_files:
            workflow.logger.info("No testable files identified. Skipping test generation.")
            return "No testable files identified."

        # Filter out empty or whitespace-only files before creating agent tasks.
        final_testable_files = []
        for file_path in testable_files:
            absolute_file_path = str(Path(workflow_input.repo_path) / file_path)
            content = await awa_activity.read_file(absolute_file_path)
            if content and content.strip():
                final_testable_files.append(file_path)
            else:
                workflow.logger.info(f"Skipping empty file: {file_path}")

        if not final_testable_files:
            workflow.logger.info("No non-empty testable files identified. Skipping test generation.")
            return "No testable files identified."

        workflow.logger.info(f"Identified testable files: {final_testable_files}")

        agent_tasks = [
            lambda fp=file_path: workflow.execute_child_workflow(
                TestAndLintPipelineWorkflow.run,
                TestAndLintPipelineWorkflowInput(
                    root_workflow_input=workflow_input,
                    file_path=fp,
                    testing_guidelines_path=workflow_input.testing_guidelines_path,
                    tests_directory=workflow_input.tests_directory,
                    working_directory=workflow_input.working_directory,
                ),
                id=f"TestAndLintPipeline-{fp.replace('/', '_')}-{workflow.info().workflow_id}",
                retry_policy=RetryPolicy(
                    maximum_attempts=1,
                ),
                execution_timeout=timedelta(seconds=3600),
            )
            for file_path in final_testable_files
        ]

        await awa_workflow.run_with_controlled_concurrency(agent_tasks, max_concurrency=2)

        return "Test generation complete."

    def _filter_testable_files(
        self,
        files: list[str],
        allowed_extensions_str: str,
        tests_directory: str,
    ) -> list[str]:
        """Filter a list of files to include only those with allowed extensions.

        Excludes __init__.py files and files already within the tests directory.
        """
        allowed_extensions = [ext.strip() for ext in allowed_extensions_str.split(",")]
        tests_dir_prefix = f"{tests_directory}/"
        return [
            file
            for file in files
            if any(file.endswith(ext) for ext in allowed_extensions)
            and Path(file).name != "__init__.py"
            and not file.startswith(tests_dir_prefix)
        ]

    async def _initialize_workflow(self) -> None:
        """Initialize shared workflow properties."""
        # Assuming mcp.json is in a standard location relative to workflows
        mcp_config_path = str(Path(__file__).parent.parent / "pr_description" / "input" / "mcp.json")
        mcp_config_str = await awa_activity.read_file(mcp_config_path)
        self.mcp_config = json.loads(mcp_config_str)

        self.workflow_paths = awa_general.get_workflow_paths(Path(__file__).parent, workflow.info())
        self.retry_policy = RetryPolicy(maximum_attempts=2)

    async def _get_changed_files(self, workflow_input: TestDoctorWorkflowInput) -> list[str]:
        """Get file diffs and parse them to get the names of changed files."""
        try:
            full_diff = await awa_activity.invoke_mcp_tool(
                mcp_config=self.mcp_config,
                tool_name="git_diff",
                parameters={
                    "commit1": workflow_input.base_branch,
                    "commit2": workflow_input.branch_name,
                    "path": workflow_input.repo_path,
                },
            )
            return self._parse_diff_for_filenames(full_diff)
        except Exception as e:
            workflow.logger.error(f"Failed to get git diff: {e}")
            raise

    def _parse_diff_for_filenames(self, diff_output: list | str) -> list[str]:
        """Parse the git diff output to get a list of changed file paths."""
        workflow.logger.info(f"Input to _parse_diff_for_filenames: {diff_output}")
        full_diff: str | None = None
        if isinstance(diff_output, list) and diff_output:
            full_diff = diff_output[0].get("text")
        elif isinstance(diff_output, str):
            full_diff = diff_output

        file_paths = []
        if not full_diff or not isinstance(full_diff, str):
            workflow.logger.warning("No valid diff string found in input.")
            return file_paths

        if not full_diff.startswith("diff --git"):
            full_diff = "diff --git " + full_diff

        diff_chunks = full_diff.split("\ndiff --git ")[1:]

        for chunk in diff_chunks:
            lines = chunk.split("\n")
            if not lines:
                continue

            first_line = lines[0]
            try:
                file_path_part = first_line.split(" b/")[1]
                file_path = f"b/{file_path_part.split(' ')[0]}"
                # Remove the "b/" prefix for a cleaner path
                file_paths.append(file_path.removeprefix("b/"))
            except IndexError:
                workflow.logger.warning(f"Could not parse file path from diff chunk line: {first_line}")
                continue

        workflow.logger.info(f"Parsed changed file count: {len(file_paths)}")
        return file_paths
