import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from awa.core.models.test_doctor import TestAndLintPipelineWorkflowInput, TestDoctorWorkflowInput
from awa.core.utils.streaming_clients import TestDoctorStreaming
from awa.core.workflows.test_and_lint_pipeline_workflow import CoreTestAndLintPipelineWorkflow
from awa.sdk.constants import ACTIVITY_INVOKE_MCP_TOOL, ACTIVITY_READ_FILE_AND_PARSE
from awa.sdk.utils.general import get_workflow_paths
from awa.sdk.utils.workflow import run_with_controlled_concurrency_workflow


@workflow.defn(name="awa-core-test-doctor")
class CoreTestDoctorWorkflow:
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
        # Use this workflow's ID as the parent session ID
        parent_session_id = workflow.info().workflow_id

        streaming = TestDoctorStreaming(parent_session_id)
        workflow.logger.info(f"TestDoctor parent session ID for streaming: {parent_session_id}")

        await self._initialize_workflow()

        await streaming.git_diff_started()
        changed_files = await self._get_changed_files(workflow_input)
        workflow.logger.info(f"Total changed files detected: {len(changed_files)}")
        await streaming.git_diff_completed(len(changed_files))

        if not changed_files:
            workflow.logger.warning(
                f"No changes detected between branches '{workflow_input.base_branch}' "
                f"and '{workflow_input.branch_name}'. Skipping test generation.",
            )
            return "No changes detected between the specified branches."

        await streaming.filtering_started()
        testable_files = self._filter_testable_files(
            changed_files,
            workflow_input.file_extensions,
            workflow_input.tests_directory,
        )
        workflow.logger.info(
            f"Filtered to {len(testable_files)} testable files out of {len(changed_files)} changed files. "
            f"Testable files: {testable_files}",
        )

        if not testable_files:
            await streaming.filtering_completed(0, len(changed_files))
            workflow.logger.warning(
                f"No testable files identified after filtering. "
                f"File extensions filter: {workflow_input.file_extensions}, "
                f"Tests directory: {workflow_input.tests_directory}",
            )
            return "No testable files identified."

        # Filter out empty or whitespace-only files before creating agent tasks.
        final_testable_files = []
        for file_path in testable_files:
            absolute_file_path = str(Path(workflow_input.repo_path) / file_path)
            workflow.logger.debug(f"Checking if file is empty: {absolute_file_path}")
            content = await workflow.execute_activity(
                ACTIVITY_READ_FILE_AND_PARSE,
                absolute_file_path,
                start_to_close_timeout=timedelta(seconds=30),
            )
            if content and content.strip():
                final_testable_files.append(file_path)
                workflow.logger.debug(f"File has content, including: {file_path}")
            else:
                workflow.logger.info(f"Skipping empty file: {file_path}")
                await streaming.file_skipped(file_path, "File is empty or contains only whitespace")

        workflow.logger.info(
            f"Final testable files after empty file filter: {len(final_testable_files)}, files: {final_testable_files}",
        )

        if not final_testable_files:
            await streaming.filtering_completed(0, len(changed_files))
            workflow.logger.warning("No non-empty testable files identified. Skipping test generation.")
            return "No testable files identified."

        await streaming.filtering_completed(len(final_testable_files), len(changed_files))
        workflow.logger.info(f"Identified testable files: {final_testable_files}")

        await streaming.workflow_started(len(final_testable_files))

        # Create child workflows with session tracking
        agent_tasks = [
            lambda fp=file_path, idx=i: self._process_file_with_tracking(
                workflow_input,
                fp,
                idx,
            )
            for i, file_path in enumerate(final_testable_files)
        ]

        await run_with_controlled_concurrency_workflow(agent_tasks, max_concurrency=2)

        await streaming.workflow_completed(len(final_testable_files))
        return "Test generation complete."

    async def _process_file_with_tracking(
        self,
        workflow_input: TestDoctorWorkflowInput,
        file_path: str,
        _index: int,
    ) -> Any:  # noqa: ANN401
        """Process a single file and pass parent session ID for streaming.

        Args:
            workflow_input: Root workflow input
            file_path: File path to process
            _index: Index of the file in the list (unused, kept for compatibility)

        Returns:
            Result from child workflow

        """
        # Use parent workflow's ID as the parent session ID
        parent_session_id = workflow.info().workflow_id

        # Generate child workflow ID
        child_workflow_id = f"TestAndLintPipeline-{file_path.replace('/', '_')}-{workflow.info().workflow_id}"

        # Execute child workflow
        # Pass parent session ID so child emits to parent for consolidated viewing
        return await workflow.execute_child_workflow(
            CoreTestAndLintPipelineWorkflow.run,
            TestAndLintPipelineWorkflowInput(
                root_workflow_input=workflow_input,
                file_path=file_path,
                testing_guidelines_path=workflow_input.testing_guidelines_path,
                tests_directory=workflow_input.tests_directory,
                working_directory=workflow_input.working_directory,
                session_id=parent_session_id,  # Pass parent session ID for event consolidation
            ),
            id=child_workflow_id,
            retry_policy=RetryPolicy(
                maximum_attempts=1,
            ),
            execution_timeout=timedelta(seconds=3600),
        )

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

        result = []
        for file in files:
            has_ext = any(file.endswith(ext) for ext in allowed_extensions)
            is_init = Path(file).name == "__init__.py"
            in_tests = file.startswith(tests_dir_prefix)

            if has_ext and not is_init and not in_tests:
                result.append(file)

        return result

    async def _initialize_workflow(self) -> None:
        """Initialize shared workflow properties."""
        # Assuming mcp.json is in a standard location relative to workflows
        mcp_config_path = str(Path(__file__).parent.parent / "mcp" / "git_mcp.json")
        mcp_config_str = await workflow.execute_activity(
            ACTIVITY_READ_FILE_AND_PARSE,
            mcp_config_path,
            start_to_close_timeout=timedelta(seconds=30),
        )
        self.mcp_config = json.loads(mcp_config_str)

        self.workflow_paths = get_workflow_paths(Path(__file__).parent, workflow.info())
        self.retry_policy = RetryPolicy(maximum_attempts=2)

    async def _get_changed_files(self, workflow_input: TestDoctorWorkflowInput) -> list[str]:
        """Get file diffs and parse them to get the names of changed files."""
        try:
            workflow.logger.info(
                f"Getting git diff between '{workflow_input.base_branch}' and '{workflow_input.branch_name}' "
                f"in repo: {workflow_input.repo_path}",
            )
            full_diff = await workflow.execute_activity(
                ACTIVITY_INVOKE_MCP_TOOL,
                args=[
                    self.mcp_config,
                    "git_diff",
                    {
                        "commit1": workflow_input.base_branch,
                        "commit2": workflow_input.branch_name,
                        "path": workflow_input.repo_path,
                    },
                ],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=self.retry_policy,
            )
            workflow.logger.info(
                f"Git diff result type: {type(full_diff)}, length: {len(full_diff) if full_diff else 0}",
            )
            parsed_files = self._parse_diff_for_filenames(full_diff)
            workflow.logger.info(f"Parsed {len(parsed_files)} changed files from git diff")
            return parsed_files
        except Exception as e:
            workflow.logger.error(f"Failed to get git diff: {e}")
            raise

    def _parse_diff_for_filenames(self, diff_output: dict) -> list[str]:
        """Parse the git diff output to get a list of changed file paths."""
        workflow.logger.info(f"Parsing git diff output type: {type(diff_output)}")

        # Handle MCP tool response format: {"content": [{"text": "..."}]}
        full_diff = diff_output["content"][0]["text"]
        workflow.logger.info(f"Extracted text from MCP format, length: {len(full_diff) if full_diff else 0}")

        file_paths = []
        if not full_diff or not isinstance(full_diff, str):
            workflow.logger.warning("No valid diff string found in input")
            return file_paths

        if not full_diff.startswith("diff --git"):
            full_diff = "diff --git " + full_diff

        # Split on diff markers, keeping all chunks (including the first one)
        diff_chunks = full_diff.split("\ndiff --git ")
        workflow.logger.info(f"Split into {len(diff_chunks)} diff chunks")

        for _i, chunk in enumerate(diff_chunks):
            if not chunk.strip():
                continue

            # Remove "diff --git " prefix if present (will be present on first chunk)
            modified_chunk = chunk.removeprefix("diff --git ")

            lines = modified_chunk.split("\n")
            if not lines:
                continue

            first_line = lines[0]
            try:
                file_path_part = first_line.split(" b/")[1]
                file_path = f"b/{file_path_part.split(' ')[0]}"
                clean_path = file_path.removeprefix("b/")
                file_paths.append(clean_path)
            except IndexError:
                workflow.logger.warning(f"Could not parse file path from diff chunk line: {first_line}")
                continue

        workflow.logger.info(f"Parsed changed file count: {len(file_paths)}")
        return file_paths
