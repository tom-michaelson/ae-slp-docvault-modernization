from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed

with workflow.unsafe.imports_passed_through():
    import json
    import os
    import re

from cookbook.recipes import constants
from sdk_dist.python.awa.client import awa_activity, awa_general, awa_workflow
from sdk_dist.python.awa.client.models import TransformParams, WorkflowPaths

from .models.github_pr_description_workflow_input import GitHubPrDescriptionWorkflowInput

# Move environment variable access to a safe location
with workflow.unsafe.imports_passed_through():
    MAX_CONCURRENT_TRANSFORMS = os.environ.get("MAX_CONCURRENT_TRANSFORMS", constants.DEFAULT_MAX_CONCURRENT_TRANSFORMS)

# Constants
CONTENT_PREVIEW_LENGTH = 50
EXPECTED_PARTS_COUNT = 2


class PullRequestDescriptionError(Exception):
    """Raised when PR description construction fails."""


@recipe_exposed("Generates a pull request description from a branch, for running in a GitHub Actions workflow")
@workflow.defn(name="github-pr-description")
class GitHubPrDescriptionWorkflow:
    """Workflow to generate a pull request description from a git branch."""

    def __init__(self) -> None:
        """Initialize the workflow with default configuration values.

        Sets up instance variables for MCP configuration, workflow paths,
        project root directory, and retry policy that will be populated
        during workflow execution.
        """
        self.mcp_config: dict[str, Any] = {}
        self.workflow_paths: WorkflowPaths = None
        self.retry_policy: RetryPolicy | None = None

    def _parse_mcp_response(self, response: dict[str, Any] | list[Any] | str) -> dict[str, Any] | list[Any] | str:
        """Parse MCP tool response to extract actual data.

        AWA MCP tools may return data in different formats:
        - Direct data (list/dict)
        - {"content": [{"text": "json_string"}]} format
        - {"data": actual_data} format
        """
        if not response:
            return response

        if isinstance(response, dict):
            # Handle content wrapper format (from AWA MCP activity)
            if "content" in response and isinstance(response["content"], list) and response["content"]:
                content_item = response["content"][0]
                if isinstance(content_item, dict) and "text" in content_item:
                    # Parse JSON string from text field
                    try:
                        return json.loads(content_item["text"])
                    except (json.JSONDecodeError, TypeError):
                        return content_item["text"]
            # Handle data wrapper format
            elif "data" in response:
                return response["data"]

        # Return as-is if already in correct format (list/dict)
        return response

    @workflow.run
    async def run(self, workflow_input: GitHubPrDescriptionWorkflowInput) -> str:  # noqa: PLR0915
        """Execute the workflow to generate a PR description."""
        await self._initialize_workflow(workflow_input)

        # Fetch PR details and populate optional fields if not provided
        pr_details = await self._fetch_pr_details(workflow_input)
        if isinstance(pr_details, dict):
            if not workflow_input.base_branch:  # Empty string is falsy
                workflow_input.base_branch = pr_details.get("base", {}).get("ref", "main")
            if not workflow_input.branch_name:  # Empty string is falsy
                workflow_input.branch_name = pr_details.get("head", {}).get("ref", "")

        # Determine processing scope (full vs incremental) using already fetched PR details
        processing_scope = await self._determine_processing_scope(pr_details)
        mode = processing_scope["mode"]
        last_processed_commit = processing_scope["last_processed_commit"]
        existing_content = processing_scope["existing_content"]
        full_existing_description = processing_scope.get("full_existing_description", existing_content)

        workflow.logger.info(f"Processing mode: {mode} (workflow_id: {workflow.info().workflow_id})")

        if mode == "incremental" and last_processed_commit:
            # First, check if the current HEAD commit is the same as last processed
            # to avoid unnecessary work
            current_head_sha = await self._get_current_head_commit(workflow_input)
            if current_head_sha and current_head_sha.startswith(last_processed_commit):
                workflow.logger.debug(
                    f"Current HEAD commit ({current_head_sha[:7]}) matches last processed commit "
                    f"({last_processed_commit[:7]}). Updating timestamp only.",
                )

                # Verify we actually have existing metadata before doing timestamp-only update
                # Use full description to check for metadata (existing_content excludes metadata by design)
                has_metadata = full_existing_description.find("### 🤖 AWA Generation Info") != -1
                workflow.logger.debug(
                    f"Checking for metadata table: found={has_metadata}, "
                    f"full_description_length={len(full_existing_description)}",
                )
                if has_metadata:
                    # Update just the timestamp in the existing description
                    updated_description = await self._update_metadata_timestamp(
                        full_existing_description,
                        current_head_sha,
                    )
                    workflow.logger.debug(f"About to update PR with description of length: {len(updated_description)}")
                    workflow.logger.debug(
                        f"Updated description preview (last 500 chars): ...{updated_description[-500:]}",
                    )
                    await self._update_github_pr(workflow_input, updated_description)
                    return "No new changes detected since last update. Timestamp updated."
                workflow.logger.debug("No existing metadata found, falling back to full processing")
                # Fall through to full processing

            # Get only NEW commits since last processed
            commit_logs, latest_commit_sha = await self._get_commit_logs(workflow_input, last_processed_commit)

            if not commit_logs or commit_logs == "No new commits found.":
                workflow.logger.info("No new commits since last update.")
                return "No new changes detected since last update."

            # Log the incremental processing details
            commit_count = len(commit_logs.split("\n")) if commit_logs else 0
            workflow.logger.debug(
                f"Incremental processing: found {commit_count} new commits since {last_processed_commit[:7]}",
            )

            # Get files changed in new commits only
            file_diffs = await self._get_files_for_commit_range(
                workflow_input,
                last_processed_commit,
                latest_commit_sha,
            )

            workflow.logger.debug(f"Incremental processing: processing {len(file_diffs)} files from new commits")

            if not file_diffs:
                workflow.logger.info("No file changes in new commits.")
                return "No new file changes detected since last update."

            # Generate summaries for changed files only
            workflow.logger.debug(f"Starting file summarization for {len(file_diffs)} files: {list(file_diffs.keys())}")
            summaries_by_file = await self._summarize_file_diffs(file_diffs)
            workflow.logger.debug(f"Completed file summarization for {len(summaries_by_file)} files")
            workflow.logger.debug("Starting PR summary generation with BAML")
            new_commit_summary = await self._generate_pr_summary(summaries_by_file, commit_logs)
            workflow.logger.debug("Completed PR summary generation")

            # Update existing description with new changes
            pr_description_content = await self._update_existing_description(
                existing_content,
                new_commit_summary,
                summaries_by_file,
            )
        else:
            # Full processing - get all commits and files
            commit_logs, latest_commit_sha = await self._get_commit_logs(workflow_input, None)
            file_diffs = await self._get_file_diffs(workflow_input)

            if not commit_logs and not file_diffs:
                workflow.logger.info("No changes detected in this PR.")
                return "No changes detected in this PR."

            # Generate complete description
            summaries_by_file = await self._summarize_file_diffs(file_diffs)
            high_level_summary = await self._generate_pr_summary(summaries_by_file, commit_logs)
            pr_description_content = self._construct_pr_description(high_level_summary, summaries_by_file)

        # Add metadata table with latest commit info
        if latest_commit_sha:
            final_pr_description = self._construct_pr_description_with_metadata(
                pr_description_content,
                latest_commit_sha,
                workflow_input,
            )
        else:
            final_pr_description = pr_description_content

        # Update GitHub PR description
        await self._update_github_pr(workflow_input, final_pr_description)

        workflow.logger.info(f"Generated and updated PR Description ({mode} mode)")
        return final_pr_description

    async def _initialize_workflow(self, _workflow_input: GitHubPrDescriptionWorkflowInput) -> None:
        """Initialize shared workflow properties."""
        mcp_config_path = str(Path(__file__).parent / "input" / "mcp.json")
        mcp_config_str = await awa_activity.read_file(mcp_config_path)
        resolved_config_str = await awa_activity.resolve_config_variables(mcp_config_str)
        self.mcp_config = json.loads(resolved_config_str)

        self.workflow_paths = awa_general.get_workflow_paths(Path(__file__).parent, workflow.info())
        self.retry_policy = RetryPolicy(maximum_attempts=3)

    async def _fetch_pr_details(self, workflow_input: GitHubPrDescriptionWorkflowInput) -> dict[str, Any]:
        """Fetch PR details from GitHub API."""
        try:
            pr_response = await awa_activity.invoke_mcp_tool(
                mcp_config=self.mcp_config,
                tool_name="get_pull_request",
                parameters={
                    "owner": workflow_input.owner,
                    "repo": workflow_input.repo,
                    "pull_number": workflow_input.pull_number,
                },
                timeout_seconds=30,
                retry_policy=self.retry_policy,
            )

            # Parse the MCP response format
            pr_details = self._parse_mcp_response(pr_response)

            workflow.logger.debug(
                f"Parsed PR details: head={pr_details.get('head', {}).get('ref')}, "
                f"base={pr_details.get('base', {}).get('ref')}",
            )
            return pr_details
        except Exception as e:
            workflow.logger.error(f"Failed to fetch PR details: {e}")
            raise

    async def _update_github_pr(
        self,
        workflow_input: GitHubPrDescriptionWorkflowInput,
        pr_description: str,
    ) -> dict[str, Any]:
        """Update GitHub PR description using issue API."""
        try:
            update_result = await awa_activity.invoke_mcp_tool(
                mcp_config=self.mcp_config,
                tool_name="update_issue",
                parameters={
                    "owner": workflow_input.owner,
                    "repo": workflow_input.repo,
                    "issue_number": workflow_input.pull_number,
                    "body": pr_description,
                },
                timeout_seconds=30,
                retry_policy=self.retry_policy,
            )
            workflow.logger.debug(f"Updated GitHub PR description: {update_result}")
            return update_result
        except Exception as e:
            workflow.logger.error(f"Failed to update GitHub PR: {e}")
            raise

    def _create_metadata_table(self, commit_sha: str, commit_link: str, timestamp: str) -> str:
        """Create the metadata table for AWA generation info."""
        return f"""| Metric | Value |
|--------|-------|
| Last Processed Commit | [`{commit_sha}`]({commit_link}) |
| Last Updated | {timestamp} |"""

    def _extract_metadata_from_table(self, pr_description: str) -> dict[str, str | None]:
        """Extract metadata from AWA generation info table in PR description."""
        try:
            # Look for the metadata table pattern - simplified approach
            # First find the table section
            table_start = pr_description.find("### 🤖 AWA Generation Info")
            if table_start == -1:
                workflow.logger.debug("No metadata table found in PR description")
                return {"last_processed_commit": None, "last_updated": None}

            # Extract the table section
            table_section = pr_description[table_start:]

            # Extract commit SHA from the commit link pattern
            commit_pattern = r"\| Last Processed Commit \| \[`([^`]+)`\]\([^)]+\)"
            commit_match = re.search(commit_pattern, table_section)

            # Extract timestamp
            timestamp_pattern = r"\| Last Updated \| ([^|]+) \|"
            timestamp_match = re.search(timestamp_pattern, table_section)

            last_processed_commit = commit_match.group(1).strip() if commit_match else None
            last_updated = timestamp_match.group(1).strip() if timestamp_match else None

            workflow.logger.debug(f"Extracted commit: {last_processed_commit}, timestamp: {last_updated}")

            return {
                "last_processed_commit": last_processed_commit,
                "last_updated": last_updated,
            }

        except (ValueError, KeyError, IndexError, AttributeError) as e:
            workflow.logger.error(f"Failed to parse metadata table: {e}")
            return {"last_processed_commit": None, "last_updated": None}

    def _extract_content_before_table(self, pr_description: str) -> str:
        """Extract the PR description content before the metadata table."""
        try:
            # Split on the metadata table header
            table_marker = "### 🤖 AWA Generation Info"
            parts = pr_description.split(table_marker)
            if len(parts) > 1:
                return parts[0].rstrip()
            return pr_description
        except Exception as e:
            workflow.logger.error(f"Failed to extract content before metadata table: {e}")
            raise

    async def _update_metadata_timestamp(self, existing_content: str, commit_sha: str) -> str:
        """Update only the timestamp in the metadata table, keeping everything else the same."""
        try:
            # Extract content before metadata table
            content_before_table = self._extract_content_before_table(existing_content)

            # Extract existing metadata to preserve the commit info
            existing_metadata = self._extract_metadata_from_table(existing_content)
            last_processed_commit = existing_metadata.get("last_processed_commit", commit_sha)

            workflow.logger.debug(f"Extracted metadata: {existing_metadata}")
            workflow.logger.debug(f"Content before table length: {len(content_before_table)}")
            workflow.logger.debug(
                f"Content before table ends with: '{content_before_table[-CONTENT_PREVIEW_LENGTH:]}'"
                if len(content_before_table) > CONTENT_PREVIEW_LENGTH
                else f"Content before table: '{content_before_table}'",
            )

            # Create metadata table with updated timestamp using same format as _construct_pr_description_with_metadata
            timestamp = workflow.now().strftime("%Y-%m-%d %H:%M:%S UTC")

            # Parse owner/repo from existing commit link in content
            commit_link_pattern = r"https://github\.com/([^/]+)/([^/]+)/commit/([a-f0-9]+)"
            match = re.search(commit_link_pattern, existing_content)

            if match and last_processed_commit:
                owner, repo, _ = match.groups()
                commit_link = f"https://github.com/{owner}/{repo}/commit/{last_processed_commit}"
            elif last_processed_commit:
                # Fallback - keep existing link pattern but this shouldn't happen
                commit_link = f"#{last_processed_commit[:7]}"
            else:
                # Handle case where last_processed_commit is None
                commit_link = f"#{commit_sha[:7]}"

            # Use same format as _construct_pr_description_with_metadata
            # Check if content already ends with --- to avoid duplication
            separator = "" if content_before_table.rstrip().endswith("---") else "\n---"

            # Use the appropriate commit SHA for metadata display
            display_commit = last_processed_commit or commit_sha

            # Create metadata table using utility function
            table_content = self._create_metadata_table(display_commit, commit_link, timestamp)
            metadata_table = f"""{separator}
### 🤖 AWA Generation Info
{table_content}"""

            result = content_before_table + metadata_table
            workflow.logger.debug(f"Final result length: {len(result)}")

            return result

        except Exception as e:  # noqa: BLE001
            workflow.logger.error(f"Failed to update metadata timestamp: {e}")
            # Fallback to returning existing content
            return existing_content

    def _construct_pr_description_with_metadata(
        self,
        content: str,
        last_commit_sha: str,
        workflow_input: GitHubPrDescriptionWorkflowInput,
    ) -> str:
        """Construct PR description with metadata table."""
        try:
            timestamp = workflow.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            commit_link = f"https://github.com/{workflow_input.owner}/{workflow_input.repo}/commit/{last_commit_sha}"

            # Create metadata table using utility function
            table_content = self._create_metadata_table(last_commit_sha, commit_link, timestamp)
            metadata_table = f"""
---
### 🤖 AWA Generation Info
{table_content}"""

            return content + metadata_table
        except Exception as e:
            workflow.logger.error(f"Failed to construct PR description with metadata: {e}")
            raise PullRequestDescriptionError("Failed to construct PR description with metadata") from e

    async def _determine_processing_scope(self, pr_details: dict[str, Any] | list | None) -> dict[str, Any]:
        """Determine if we need full or incremental processing based on existing PR description."""
        try:
            # Extract existing description from PR details
            existing_description = ""

            if isinstance(pr_details, list) and pr_details:
                existing_description = pr_details[0].get("body", "") or ""
            elif isinstance(pr_details, dict):
                existing_description = pr_details.get("body", "") or ""
            elif pr_details is not None:
                # Invalid input type - this should trigger an error for testing
                raise ValueError(f"Invalid pr_details type: {type(pr_details)}")  # noqa: TRY301

            # Parse metadata from existing description
            metadata = self._extract_metadata_from_table(existing_description)
            last_processed_commit = metadata.get("last_processed_commit")

            # Determine processing mode
            if not last_processed_commit:
                workflow.logger.debug("No metadata found - performing full processing")
                return {
                    "mode": "full",
                    "last_processed_commit": None,
                    "existing_content": "",
                }
            workflow.logger.debug(
                f"Found metadata - checking for incremental update from commit: {last_processed_commit}",
            )
            existing_content = self._extract_content_before_table(existing_description)
            return {
                "mode": "incremental",
                "last_processed_commit": last_processed_commit,
                "existing_content": existing_content,
                # Include full description for timestamp-only updates
                "full_existing_description": existing_description,
            }

        except Exception as e:  # noqa: BLE001
            workflow.logger.error(f"Failed to determine processing scope: {e}")
            # Default to full processing on error
            return {
                "mode": "full",
                "last_processed_commit": None,
                "existing_content": "",
            }

    async def _get_commit_logs(
        self,
        workflow_input: GitHubPrDescriptionWorkflowInput,
        last_processed_commit: str | None = None,
    ) -> tuple[str, str]:
        """Get commit logs from GitHub API with pagination. Returns (commit_logs, latest_commit_sha)."""
        try:
            all_commits = []
            page = 1
            per_page = 10  # Small page size to avoid token limits
            max_commits = 50

            while len(all_commits) < max_commits:
                commits_response = await awa_activity.invoke_mcp_tool(
                    mcp_config=self.mcp_config,
                    tool_name="list_commits",
                    parameters={
                        "owner": workflow_input.owner,
                        "repo": workflow_input.repo,
                        "sha": workflow_input.branch_name,
                        "perPage": per_page,
                        "page": page,
                    },
                    timeout_seconds=30,
                    retry_policy=self.retry_policy,
                )

                # Parse MCP response
                commits_result = self._parse_mcp_response(commits_response)

                if not commits_result or not isinstance(commits_result, list):
                    break

                page_commits = []
                found_last_processed = False

                for commit in commits_result:
                    if not isinstance(commit, dict):
                        continue

                    commit_sha = commit.get("sha", "")
                    commit_message = commit.get("commit", {}).get("message", "")

                    # Stop if we've reached the last processed commit (for incremental updates)
                    if last_processed_commit and commit_sha.startswith(last_processed_commit):
                        workflow.logger.debug(f"Reached last processed commit: {last_processed_commit}")
                        found_last_processed = True
                        break

                    # Stop if we've reached the base branch commit
                    if workflow_input.base_branch and commit_sha == workflow_input.base_branch:
                        break

                    page_commits.append(
                        {
                            "sha": commit_sha,
                            "message": commit_message.split("\n")[0],  # First line only
                        },
                    )

                # Only add commits that are NEW (before we hit the last processed commit)
                all_commits.extend(page_commits)

                # Break if we found last processed commit or no more commits
                if found_last_processed:
                    break

                if len(commits_result) < per_page:
                    break

                page += 1

            # Format commit logs for BAML
            if not all_commits:
                return "No new commits found.", ""

            latest_commit_sha = all_commits[0]["sha"] if all_commits else ""
            commit_logs = "\n".join([f"- {c['message']} ({c['sha'][:7]})" for c in all_commits])

            workflow.logger.debug(f"Fetched {len(all_commits)} commits, latest: {latest_commit_sha[:7]}")
            return commit_logs, latest_commit_sha

        except Exception as e:
            workflow.logger.error(f"Failed to get commit logs from GitHub: {e}")
            raise

    async def _get_current_head_commit(self, workflow_input: GitHubPrDescriptionWorkflowInput) -> str:
        """Get the current HEAD commit SHA for the branch."""
        try:
            # Get just the first commit (HEAD) from the branch
            commits_response = await awa_activity.invoke_mcp_tool(
                mcp_config=self.mcp_config,
                tool_name="list_commits",
                parameters={
                    "owner": workflow_input.owner,
                    "repo": workflow_input.repo,
                    "sha": workflow_input.branch_name,
                    "perPage": 1,
                    "page": 1,
                },
                timeout_seconds=30,
                retry_policy=self.retry_policy,
            )

            # Parse MCP response
            commits_result = self._parse_mcp_response(commits_response)

            if commits_result and isinstance(commits_result, list) and len(commits_result) > 0:
                head_commit = commits_result[0]
                if isinstance(head_commit, dict):
                    head_sha = head_commit.get("sha", "")
                    workflow.logger.debug(f"Current HEAD commit: {head_sha[:7]}")
                    return head_sha

            workflow.logger.warning("Could not retrieve current HEAD commit")
            return ""

        except Exception as e:  # noqa: BLE001
            workflow.logger.error(f"Failed to get current HEAD commit: {e}")
            return ""

    async def _get_file_diffs(self, workflow_input: GitHubPrDescriptionWorkflowInput) -> dict[str, str]:
        """Get and parse file diffs from GitHub PR files API with pagination."""
        try:
            all_files = []
            page = 1
            per_page = 30  # Reasonable page size for files
            max_files = 100

            while len(all_files) < max_files:
                files_response = await awa_activity.invoke_mcp_tool(
                    mcp_config=self.mcp_config,
                    tool_name="get_pull_request_files",
                    parameters={
                        "owner": workflow_input.owner,
                        "repo": workflow_input.repo,
                        "pull_number": workflow_input.pull_number,
                        "per_page": per_page,
                        "page": page,
                    },
                    timeout_seconds=60,
                    retry_policy=self.retry_policy,
                )

                # Parse MCP response
                files_result = self._parse_mcp_response(files_response)

                if not files_result or not isinstance(files_result, list):
                    break

                page_files = []
                for file_info in files_result:
                    if not isinstance(file_info, dict):
                        continue

                    filename = file_info.get("filename", "")
                    patch = file_info.get("patch", "")
                    status = file_info.get("status", "")

                    if filename and patch:
                        page_files.append(
                            {
                                "filename": filename,
                                "patch": patch,
                                "status": status,
                            },
                        )

                all_files.extend(page_files)

                if len(files_result) < per_page:
                    break

                page += 1

            # Convert GitHub patch format to git diff format for BAML compatibility
            file_diffs = {}
            for file_info in all_files:
                filename = file_info["filename"]
                patch = file_info["patch"]

                # Convert GitHub patch to git diff format
                git_diff = self._convert_github_patch_to_git_diff(filename, patch)
                file_diffs[f"b/{filename}"] = git_diff

            workflow.logger.debug(f"Fetched {len(file_diffs)} file diffs from GitHub PR")
            return file_diffs

        except Exception as e:
            workflow.logger.error(f"Failed to get file diffs from GitHub: {e}")
            raise

    def _convert_github_patch_to_git_diff(self, filename: str, patch: str) -> str:
        """Convert GitHub patch format to git diff format for BAML compatibility."""
        try:
            # GitHub patches are already in unified diff format, just need proper header
            git_diff_header = f"diff --git a/{filename} b/{filename}\n"

            # Truncate large patches to prevent token overflow
            max_lines = 1000
            patch_lines = patch.split("\n")
            if len(patch_lines) > max_lines:
                truncated_patch = "\n".join(patch_lines[:max_lines])
                truncated_patch += f"\n... (truncated {len(patch_lines) - max_lines} lines)"
                patch = truncated_patch

            return git_diff_header + patch

        except (ValueError, IndexError) as e:
            workflow.logger.error(f"Failed to convert GitHub patch for {filename}: {e}")
            return f"diff --git a/{filename} b/{filename}\n{patch}"

    async def _summarize_file_diffs(self, file_diffs: dict[str, str]) -> dict[str, Any]:
        """Summarize each file's diff using controlled concurrency."""
        baml_src_path = self.workflow_paths.baml_src
        baml_file_path = str(Path(baml_src_path) / "summarize_diff.baml")
        summaries_dir = str(Path(self.workflow_paths.output) / "summaries")

        def create_summary_task(file_path: str, diff_content: str) -> Callable[[], Awaitable[Any]]:
            """Create a summary task for a single file."""
            clean_file_path = file_path.replace("/", "_").replace(".", "_")

            async def task() -> str:
                clean_path = file_path.removeprefix("b/").replace("/", "_")
                output_filename = f"{clean_path}.md"
                transform_params = TransformParams(
                    baml_function_name="SummarizeDiff",
                    request={"file_path": file_path, "diff_content": diff_content},
                    output_path=str(Path(summaries_dir) / output_filename),
                )
                return await awa_workflow.execute_baml_transform(
                    transform_params=transform_params,
                    baml_path=baml_file_path,
                    additional_workflow_id_part=clean_file_path,
                )

            return task

        # Create individual tasks for each file diff
        summary_tasks = []
        file_paths = list(file_diffs.keys())

        for file_path in file_paths:
            diff_content = file_diffs[file_path]
            summary_tasks.append(create_summary_task(file_path, diff_content))

        try:
            # Execute with controlled concurrency (max 3 concurrent)
            summary_results = await awa_workflow.run_with_controlled_concurrency(
                summary_tasks,
                max_concurrency=int(MAX_CONCURRENT_TRANSFORMS),
            )

            # Combine results back into dictionary format
            summaries_by_file = dict(zip(file_paths, summary_results, strict=False))
        except Exception as e:
            workflow.logger.error(f"Failed to summarize diffs with controlled concurrency: {e}")
            raise
        else:
            # await self._write_summaries_to_files(summaries_by_file) # TODO RH: Clean up
            return summaries_by_file

    async def _generate_pr_summary(self, summaries_by_file: dict[str, Any], commit_logs: str) -> str:
        """Generate the final PR summary paragraph after batching."""
        baml_src_path = self.workflow_paths.baml_src
        batch_size = 5
        summary_list = list(summaries_by_file.values())
        batched_summaries = [summary_list[i : i + batch_size] for i in range(0, len(summary_list), batch_size)]

        # Create TransformParams objects for batch processing
        transform_params_by_key: dict[str, TransformParams] = {}
        for i, batch in enumerate(batched_summaries):
            transform_params_by_key[f"batch_{i}"] = TransformParams(
                baml_function_name="SummarizeBatch",
                request={"summaries": batch},
            )

        final_summaries = await awa_workflow.execute_baml_transform_batch(
            baml_path=str(Path(baml_src_path) / "summarize_batch.baml"),
            baml_requests_by_key=transform_params_by_key,
        )
        output_file_path = str(Path(self.workflow_paths.output) / "pr_description.md")

        baml_content = await awa_activity.read_file(str(Path(baml_src_path) / "generate_pr_description.baml"))

        try:
            transform_params = TransformParams(
                baml_function_name="GeneratePrDescription",
                request={"summaries_by_file": final_summaries, "commit_logs": commit_logs},
                output_path=output_file_path,
                baml_content=baml_content,
            )
            return await awa_workflow.execute_baml_transform(
                transform_params=transform_params,
            )
        except Exception as e:
            workflow.logger.error(f"Failed to generate PR description: {e}")
            raise

    async def _get_files_for_commit_range(
        self,
        workflow_input: GitHubPrDescriptionWorkflowInput,
        last_commit: str,
        latest_commit: str,
    ) -> dict[str, str]:
        """Get files that changed in new commits only."""
        try:
            workflow.logger.debug(f"Getting files changed from {last_commit[:7]} to {latest_commit[:7]}")

            # Try to use GitHub's compare API to get only files that changed between commits
            try:
                # Try get_commit for the latest commit to get only files from that commit
                workflow.logger.debug(f"Trying to get files from latest commit: {latest_commit[:7]}")
                compare_response = await awa_activity.invoke_mcp_tool(
                    mcp_config=self.mcp_config,
                    tool_name="get_commit",
                    parameters={
                        "owner": workflow_input.owner,
                        "repo": workflow_input.repo,
                        "ref": latest_commit,
                    },
                    timeout_seconds=30,
                    retry_policy=self.retry_policy,
                )

                compare_data = self._parse_mcp_response(compare_response)
                if isinstance(compare_data, dict) and "files" in compare_data:
                    files = compare_data["files"]
                    changed_files = {}

                    for file_info in files:
                        if isinstance(file_info, dict):
                            filename = file_info.get("filename", "")
                            patch = file_info.get("patch", "")
                            if filename and patch:
                                changed_files[filename] = patch

                    workflow.logger.debug(
                        f"Get commit API: found {len(changed_files)} files changed in latest commit "
                        f"{latest_commit[:7]}",
                    )
                    return changed_files

            except Exception as e:  # noqa: BLE001
                workflow.logger.warning(f"Get commit API not available or failed: {e}")

            # Fallback: Use all PR files but log the limitation
            all_pr_files = await self._get_file_diffs(workflow_input)
            workflow.logger.warning(
                f"Fallback: using all {len(all_pr_files)} PR files (could not filter to new commits only)",
            )

            return all_pr_files

        except Exception as e:
            workflow.logger.error(f"Failed to get files for commit range: {e}")
            raise

    async def _update_existing_description(
        self,
        existing_content: str,
        new_summary: str,
        new_files: dict[str, Any],
    ) -> str:
        """Update existing PR description with new changes, avoiding duplication."""
        try:
            # For incremental updates, we want to regenerate the complete description
            # using only files that still exist in the PR. This prevents stale files
            # from remaining in the description after being reverted.

            # Extract existing file information from the current description
            existing_files = {}
            lines = existing_content.split("\n")

            # Look for file entries in any section (they start with "- `")
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith("- `") and "`: " in stripped_line:
                    try:
                        parts = stripped_line.split("`: ", 1)
                        if len(parts) == EXPECTED_PARTS_COUNT:
                            filename = parts[0].replace("- `", "").strip()
                            description = parts[1].strip()
                            existing_files[filename] = description
                    except ValueError:
                        continue

            # Create a set of current PR file paths for quick lookup
            current_pr_files = set()
            for file_path in new_files:
                original_file_path = file_path.removeprefix("b/")
                current_pr_files.add(original_file_path)

            # Only keep existing files that are still present in the current PR
            preserved_files = {}
            for filename, description in existing_files.items():
                if filename in current_pr_files:
                    preserved_files[filename] = description
                else:
                    workflow.logger.debug(f"Removing file from description (no longer in PR): {filename}")

            # Update with new/changed files (this will overwrite preserved files if they changed)
            for file_path, summary in new_files.items():
                original_file_path = file_path.removeprefix("b/")
                preserved_files[original_file_path] = summary

            # Create a complete new description with only current PR files
            updated_files_dict = {}
            for filename, description in preserved_files.items():
                # Convert back to the format expected by _construct_pr_description
                updated_files_dict[f"b/{filename}"] = description

            # Generate complete new description
            return self._construct_pr_description(new_summary, updated_files_dict)

        except (ValueError, KeyError) as e:
            workflow.logger.error(f"Failed to update existing description: {e}")
            # Fall back to constructing new description
            return self._construct_pr_description(new_summary, new_files)

    def _construct_pr_description(self, high_level_summary: str, summaries_by_file: dict[str, Any]) -> str:
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
        workflow.logger.debug(f"Input to _parse_diff: {diff_output}")
        full_diff: str | None = None
        if isinstance(diff_output, list) and diff_output:
            # The actual diff string is in the 'text' key of the first dictionary
            full_diff = diff_output[0].get("text")
        elif isinstance(diff_output, str):
            full_diff = diff_output
        elif isinstance(diff_output, dict):
            full_diff = diff_output.get("data", {}).get("diff")

        file_diffs = {}
        if not full_diff or not isinstance(full_diff, str):
            workflow.logger.warn("No valid diff string found in input.")
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
                workflow.logger.warn(f"Could not parse file path from diff chunk line: {first_line}")
                continue

        workflow.logger.debug(f"Parsed file diffs count: {len(file_diffs)}")
        return file_diffs
