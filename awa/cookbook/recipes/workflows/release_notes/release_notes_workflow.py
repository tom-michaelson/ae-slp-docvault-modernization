import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    import json

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from sdk_dist.python.awa.client import awa_activity, awa_general, awa_workflow
from sdk_dist.python.awa.client.models import TransformParams, WorkflowPaths

from .models.release_notes_workflow_input import ReleaseNotesWorkflowInput


@recipe_exposed("Generates release notes from a range of commits")
@workflow.defn(name="release-notes")
class ReleaseNotesWorkflow:
    """Workflow to generate release notes from a range of commits."""

    def __init__(self) -> None:
        """Initialize the workflow with default configuration values.

        Sets up instance variables for MCP configuration, workflow paths,
        project root directory, and retry policy that will be populated
        during workflow execution.
        """
        self.mcp_config: dict[str, Any] = {}
        self.workflow_paths: WorkflowPaths | None = None
        self.project_root: str = ""
        self.retry_policy: RetryPolicy | None = None

    @workflow.run
    async def run(self, workflow_input: ReleaseNotesWorkflowInput) -> str:
        """Execute the workflow to generate Release Notes for latest changes."""
        await self._initialize_workflow(workflow_input)

        commit_logs = await self._get_commit_logs(workflow_input)
        file_diffs = await self._get_file_diffs(workflow_input)
        workflow.logger.info(f"COMMIT LOGS - {commit_logs}")
        workflow.logger.info(f"FILE DIFFS - {file_diffs}")

        if not commit_logs:
            workflow.logger.info("No unreleased Commit Changes. Skipping Release Notes generation.")
            return "No changes detected between the specified commits."

        summaries_by_file = await self._summarize_file_diffs(file_diffs)
        high_level_summary = await self._generate_release_notes(summaries_by_file, commit_logs)
        pr_description = self._construct_release_notes(high_level_summary, summaries_by_file)

        output_file_path = str(Path(self.workflow_paths.output) / "release_notes.md")
        await awa_activity.write_file(output_file_path, pr_description)

        workflow.logger.info(f"Generated Release Notes:\n{pr_description}")
        return pr_description

    async def _initialize_workflow(self, workflow_input: ReleaseNotesWorkflowInput) -> None:
        """Initialize shared workflow properties."""
        self.workflow_paths = awa_general.get_workflow_paths(Path(__file__).parent, workflow.info())

        mcp_config_path = str(Path(__file__).parent / "input" / "mcp.json")
        mcp_config_str = await awa_activity.read_file(mcp_config_path)
        self.mcp_config = json.loads(mcp_config_str)

        self.project_root = workflow_input.repo_path
        self.retry_policy = RetryPolicy(maximum_attempts=3)

    async def _get_commit_logs(self, workflow_input: ReleaseNotesWorkflowInput) -> str:
        """Get commit logs between two branches."""
        try:
            workflow.logger.info(
                f"Checking commits for {workflow_input.release_branch} since {workflow_input.last_released_commit}",
            )
            log_result = await awa_activity.invoke_mcp_tool(
                mcp_config=self.mcp_config,
                tool_name="git_log",
                parameters={
                    "branchOrFile": workflow_input.release_branch,
                    "path": self.project_root,
                },
                timeout_seconds=30,
                retry_policy=self.retry_policy,
            )

            all_commits = []
            if (
                log_result
                and log_result.get("content")
                and isinstance(log_result.get("content"), list)
                and log_result.get("content")[0].get("text")
            ):
                log_data = log_result.get("content")[0].get("text")

                # Parse the response, handling the "Success: " prefix
                data = self._parse_mcp_response(log_data)

                workflow.logger.info(f"Searching for: {workflow_input.last_released_commit}")
                if "commits" in data:
                    for commit in data["commits"]:
                        # Add commit info until hash of last released commit is found
                        if commit["hash"] and commit["hash"] == workflow_input.last_released_commit:
                            workflow.logger.info("Last released commit found! Breaking...")
                            break
                        all_commits.append(commit)
                    if len(data["commits"]) == len(all_commits):
                        workflow.logger.info("First commit not found.")
                        return None

            workflow.logger.info(f"Adding number of commits: {len(all_commits)}")
            commit_logs = "\n".join([f"- {c['subject']} ({c['hash'][:7]})" for c in all_commits])
            workflow.logger.info(f"Parsed commit logs: {commit_logs}")
        except Exception as e:
            workflow.logger.error(f"Failed to get commit logs: {e}")
            raise
        else:
            return commit_logs

    def _parse_mcp_response(self, response_str: str) -> dict:
        """Parse MCP tool response that may have 'Success: ' prefix."""
        try:
            # First try direct JSON parsing
            return json.loads(response_str)
        except json.JSONDecodeError:
            # Handle "Success: {...}" format
            if response_str.startswith("Success: "):
                json_str = response_str[9:]  # Remove "Success: " prefix
                return json.loads(json_str)

            # Handle other potential prefixes with regex
            match = re.match(r"^\w+:\s*({.*})$", response_str, re.DOTALL)
            if match:
                return json.loads(match.group(1))

            # If all else fails, try to find JSON object in the string
            json_match = re.search(r"({.*})", response_str, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Last resort: return empty dict
            workflow.logger.error(f"Could not parse MCP response: {response_str}")
            return {}

    async def _get_file_diffs(self, workflow_input: ReleaseNotesWorkflowInput) -> dict[str, str]:
        """Get and parse file diffs between two branches."""
        try:
            full_diff = await awa_activity.invoke_mcp_tool(
                mcp_config=self.mcp_config,
                tool_name="git_diff",
                parameters={
                    "commit1": workflow_input.last_released_commit,
                    "commit2": workflow_input.release_branch,
                    "path": self.project_root,
                },
                timeout_seconds=60,
                retry_policy=self.retry_policy,
            )
            return self._parse_diff(full_diff)
        except Exception as e:
            workflow.logger.error(f"Failed to get git diff: {e}")
            raise

    async def _summarize_file_diffs(self, file_diffs: dict[str, str]) -> dict[str, Any]:
        """Summarize each file's diff using controlled concurrency."""
        baml_src_path = self.workflow_paths.baml_src
        baml_file_path = str(Path(baml_src_path) / "summarize_diff.baml")

        def create_summary_task(file_path: str, diff_content: str) -> Callable[[], Awaitable[Any]]:
            """Create a summary task for a single file."""
            clean_file_path = file_path.replace("/", "_").replace(".", "_")

            async def task() -> str:
                transform_params = TransformParams(
                    baml_path=baml_file_path,
                    baml_function_name="SummarizeDiff",
                    baml_request={"file_path": file_path, "diff_content": diff_content},
                    additional_workflow_id_part=clean_file_path,
                )
                return await awa_workflow.execute_baml_transform(transform_params=transform_params)

            return task

        # Create individual tasks for each file diff
        summary_tasks = []
        file_paths = list(file_diffs.keys())

        for file_path in file_paths:
            diff_content = file_diffs[file_path]
            summary_tasks.append(create_summary_task(file_path, diff_content))

        try:
            # Execute with controlled concurrency (max 2 concurrent)
            summary_results = await awa_workflow.run_with_controlled_concurrency(
                summary_tasks,
                max_concurrency=2,
            )

            # Combine results back into dictionary format
            summaries_by_file = dict(zip(file_paths, summary_results, strict=False))
        except Exception as e:
            workflow.logger.error(f"Failed to summarize diffs with controlled concurrency: {e}")
            raise
        else:
            await self._write_summaries_to_files(summaries_by_file)
            return summaries_by_file

    async def _write_summaries_to_files(self, summaries_by_file: dict[str, Any]) -> None:
        """Write each summary to a file for inspection."""
        summaries_dir = str(Path(self.workflow_paths.output) / "summaries")
        write_tasks = []
        for file_path, summary in summaries_by_file.items():
            clean_path = file_path.removeprefix("b/").replace("/", "_")
            output_filename = f"{clean_path}.md"
            output_path = Path(summaries_dir) / output_filename
            write_tasks.append(awa_activity.write_file(str(output_path), summary))
        await asyncio.gather(*write_tasks)

    async def _generate_release_notes(self, summaries_by_file: dict[str, Any], commit_logs: str) -> str:
        """Generate the final PR summary paragraph after batching."""
        baml_src_path = self.workflow_paths.baml_src
        batch_size = 5
        summary_list = list(summaries_by_file.values())
        batched_summaries = [summary_list[i : i + batch_size] for i in range(0, len(summary_list), batch_size)]

        batch_summaries_by_key = {f"batch_{i}": {"summaries": batch} for i, batch in enumerate(batched_summaries)}

        final_summaries = await awa_workflow.execute_baml_transform_batch(
            baml_path=str(Path(baml_src_path) / "summarize_batch.baml"),
            baml_function_name="SummarizeBatch",
            baml_requests_by_key=batch_summaries_by_key,
        )

        try:
            transform_params = TransformParams(
                baml_path=str(Path(baml_src_path) / "generate_release_notes.baml"),
                baml_function_name="GenerateReleaseNotes",
                baml_request={"summaries_by_file": final_summaries, "commit_logs": commit_logs},
            )
            return await awa_workflow.execute_baml_transform(transform_params=transform_params)
        except Exception as e:
            workflow.logger.error(f"Failed to generate PR description: {e}")
            raise

    def _construct_release_notes(self, high_level_summary: str, summaries_by_file: dict[str, Any]) -> str:
        """Construct the final PR description string."""
        pr_description_parts = ["## Summary", high_level_summary, "## File-by-File Changes"]
        sorted_files = sorted(summaries_by_file.keys())

        for file_path in sorted_files:
            summary_content = summaries_by_file[file_path]
            original_file_path = file_path.removeprefix("b/")
            pr_description_parts.append(f"- `{original_file_path}`: {summary_content}")

        return "\n\n".join(pr_description_parts)

    def _parse_diff(self, diff_output: list | str) -> dict[str, str]:
        """Parse the git diff output into a dictionary of per-file diffs.

        Args:
            diff_output: The output from 'git diff', which can be a string or a list
                of dictionaries containing the diff text.

        Returns:
            A dictionary where keys are file paths and values are their diffs.

        """
        # workflow.logger.info(f"Input to _parse_diff: {diff_output}")
        full_diff: str | None = None
        if (
            diff_output
            and diff_output.get("content")
            and isinstance(diff_output.get("content"), list)
            and diff_output.get("content")[0].get("text")
        ):
            full_diff = diff_output.get("content")[0].get("text")
        elif isinstance(diff_output, str):
            full_diff = diff_output

        file_diffs = {}
        if not full_diff or not isinstance(full_diff, str):
            workflow.logger.warning("No valid diff string found in input.")
            return file_diffs

        # The first diff in the raw output may not have the "diff --git" prefix, so we add it
        # to make the splitting logic consistent.
        if not full_diff.startswith("diff --git"):
            full_diff = "diff --git " + full_diff

        # Split the full diff by the separator for each file's diff
        # Split on "diff --git " and filter out empty chunks
        all_chunks = full_diff.split("diff --git ")
        diff_chunks = [chunk for chunk in all_chunks if chunk.strip()]

        for chunk in diff_chunks:
            lines = chunk.split("\n")
            if not lines:
                continue

            # The first line contains the file paths, e.g., "a/foo.py b/foo.py"
            first_line = lines[0]
            try:
                # Extract the 'b' path, which is the "new" file path
                file_path_part = first_line.split(" b/")[1]
                # The file path is the part before the first space
                file_path = f"b/{file_path_part.split(' ')[0]}"
                # Reconstruct the diff content for this file
                diff_content = "diff --git " + chunk
                file_diffs[file_path] = diff_content
            except IndexError:
                # Skip chunks that don't have the expected format
                workflow.logger.warning(f"Could not parse file path from diff chunk line: {first_line}")
                continue

        workflow.logger.info(f"Parsed file diffs count: {len(file_diffs)}")
        return file_diffs
