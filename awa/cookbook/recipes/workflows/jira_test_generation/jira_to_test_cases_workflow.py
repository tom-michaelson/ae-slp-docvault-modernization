import csv
import io
import json
import re
from datetime import UTC, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from sdk_dist.python.awa.client import awa_activity, awa_general, awa_workflow
from sdk_dist.python.awa.client.models import JiraIssueRequest, TransformParams

if TYPE_CHECKING:
    from sdk_dist.python.awa.client.models import WorkflowPaths

with workflow.unsafe.imports_passed_through():
    pass

from .models.jira_to_test_cases_input import JiraToTestCasesInput
from .models.test_case import TestCase, TestSuite


@recipe_exposed("Generates test cases from JIRA issues")
@workflow.defn(name="jira-to-test-cases")
class JiraToTestCasesWorkflow:
    """Workflow to generate test cases from JIRA issues and output them as CSV."""

    def __init__(self) -> None:
        """Initialize the workflow with default configuration."""
        self.mcp_config: dict[str, Any] = {}
        self.workflow_paths: WorkflowPaths | None = None
        self.project_root: str = ""
        self.retry_policy: RetryPolicy | None = None

    @workflow.run
    async def run(self, workflow_input: JiraToTestCasesInput) -> str:
        """Execute the workflow to generate test cases from JIRA issues."""
        await self._initialize_workflow(workflow_input)

        # Fetch all issues to process
        issues_to_process = await self._fetch_all_issues(workflow_input)

        if not issues_to_process:
            return "No JIRA issues found or could not be fetched"

        workflow.logger.info(f"Processing {len(issues_to_process)} JIRA issues")

        # Process all issues in parallel
        base_output_dir = Path(self.workflow_paths.workflow_root) / "output" / "jira-to-test-cases"

        # Create output directories for all issues first
        for jira_issue in issues_to_process:
            issue_key = jira_issue.get("key", "UNKNOWN")
            issue_output_dir = base_output_dir / issue_key
            issue_output_dir.mkdir(parents=True, exist_ok=True)

        # Process all issues sequentially to avoid BAML client conflicts
        workflow.logger.info(f"Processing {len(issues_to_process)} issues...")
        all_test_suites = []
        for issue in issues_to_process:
            test_suite = await self._generate_test_suite_for_issue(issue, workflow_input)
            all_test_suites.append(test_suite)

        # Generate outputs for each test suite
        for test_suite in all_test_suites:
            if test_suite:
                issue_output_dir = base_output_dir / test_suite.jira_issue_key
                await self._generate_issue_outputs([test_suite], issue_output_dir, workflow_input)

        # Generate aggregate summary if multiple issues
        if len(issues_to_process) > 1:
            await self._generate_aggregate_summary(all_test_suites, base_output_dir)

        # Return summary
        total_test_cases = sum(len(suite.test_cases) for suite in all_test_suites)
        issue_list = ", ".join([suite.jira_issue_key for suite in all_test_suites])

        return (
            f"Successfully generated {total_test_cases} test cases from "
            f"{len(all_test_suites)} JIRA issue(s): {issue_list}. "
            f"Files saved in {base_output_dir}"
        )

    async def _initialize_workflow(self, workflow_input: JiraToTestCasesInput) -> None:  # noqa: ARG002
        """Initialize workflow configuration and paths."""
        workflow_dir = Path(__file__).parent

        # Create base workflow paths (output will be per-issue)
        self.workflow_paths = awa_general.get_workflow_paths_direct(
            workflow_dir,
            "jira-to-test-cases",
            workflow.info().workflow_id,
        )
        # Override output to use a custom structure for multiple issues
        self.workflow_paths.output = str(workflow_dir / "output" / "jira-to-test-cases")
        self.project_root = self.workflow_paths.project_root or str(workflow_dir.parent.parent)
        self.retry_policy = RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=1))

    async def _fetch_all_issues(self, workflow_input: JiraToTestCasesInput) -> list[dict[str, Any]]:
        """Fetch all issues specified in the input."""
        if not workflow_input.issue_keys:
            return []

        # Limit to max_issues
        issue_keys_to_fetch = workflow_input.issue_keys[: workflow_input.max_issues]
        workflow.logger.info(f"Fetching {len(issue_keys_to_fetch)} JIRA issues")

        # Fetch issues in parallel with controlled concurrency
        fetch_tasks = [
            lambda key=key: self._fetch_single_jira_issue(key, workflow_input.project_id) for key in issue_keys_to_fetch
        ]

        issues = await awa_workflow.run_with_controlled_concurrency(
            fetch_tasks,
            max_concurrency=min(5, len(fetch_tasks)),
        )

        # Filter out None values (failed fetches)
        valid_issues = [issue for issue in issues if issue is not None]

        if len(valid_issues) < len(issue_keys_to_fetch):
            failed_count = len(issue_keys_to_fetch) - len(valid_issues)
            workflow.logger.warning(f"Failed to fetch {failed_count} issue(s)")

        return valid_issues

    async def _fetch_single_jira_issue(self, issue_key: str, project_id: str) -> dict[str, Any] | None:
        """Fetch a single JIRA issue by key."""
        try:
            request = JiraIssueRequest(
                project_id=project_id,
                key=issue_key,
            )
            workflow.logger.info(f"Fetching JIRA issue: {issue_key}")

            response = await awa_activity.read_jira_issue(request)

            # Convert JiraIssueResponse to dict for backwards compatibility
            issue_dict = {
                "key": response.key,
                "summary": response.summary,
                "description": response.description or "",
                "issue_type": response.issue_type,
                "priority": "Medium",  # Default priority since not in JiraIssueResponse
            }

            return issue_dict

        except (ValueError, KeyError, TypeError, AttributeError) as e:
            workflow.logger.error(f"Failed to fetch JIRA issue {issue_key}: {e}")
            return None

    async def _generate_test_suite_for_issue(  # noqa: PLR0915
        self,
        issue: dict[str, Any],
        workflow_input: JiraToTestCasesInput,
    ) -> TestSuite:
        """Generate a test suite for a single JIRA issue."""
        issue_key = issue.get("key", "UNKNOWN")

        # Handle both nested and flat JIRA response structures
        if "fields" in issue:
            # Standard JIRA API structure
            fields = issue["fields"]
            issue_summary = fields.get("summary", "No summary")
            description = fields.get("description", "")
            issue_type = fields.get("issuetype", {}).get("name", "Story")
            priority = fields.get("priority", {}).get("name", "Medium")
        else:
            # Flat structure from custom JIRA integration
            issue_summary = issue.get("summary", "No summary")
            description = issue.get("description", "")
            issue_type = issue.get("issue_type", "Story")
            priority = issue.get("priority", "Medium")
            fields = issue  # Use the flat structure as fields

        workflow.logger.info(f"Generating test cases for {issue_key}: {issue_summary}")

        # Log what we're about to send to BAML for debugging
        workflow.logger.info("\n" + "=" * 80)
        workflow.logger.info("DATA BEING SENT TO BAML PROMPT:")
        workflow.logger.info("=" * 80)

        try:
            # Prepare BAML request

            # Try to extract acceptance criteria from various possible locations
            acceptance_criteria = []

            # Parse acceptance criteria from HTML description if present
            if description and "AcceptanceCriteria" in description:
                # Extract AC items from HTML
                # Find all AC blocks (AC1, AC2, etc.)
                ac_pattern = r"<b>(AC\d+)</b>:\s*([^<]+)"
                ac_matches = re.findall(ac_pattern, description)

                for ac_id, ac_text in ac_matches:
                    # Clean up the HTML and extract the main acceptance criteria text
                    ac_text_clean = re.sub(r"<[^>]+>", "", ac_text).strip()
                    acceptance_criteria.append(f"{ac_id}: {ac_text_clean}")

                # Also extract bullet points under each AC
                # Pattern to find list items within acceptance criteria sections
                li_pattern = r"<li>([^<]+)</li>"
                li_matches = re.findall(li_pattern, description)

                for li_text in li_matches:
                    # Skip the main AC items we already captured
                    if not li_text.startswith("AC"):
                        # Clean and add sub-items
                        clean_text = re.sub(r"<[^>]+>", "", li_text).strip()
                        if clean_text and not any(ac in clean_text for ac in ["Requires completion", "http"]):
                            acceptance_criteria.append(f"- {clean_text}")

            # If still no acceptance criteria, check for standard field
            if not acceptance_criteria and "acceptanceCriteria" in fields:
                acceptance_criteria = fields.get("acceptanceCriteria", [])

            # Check custom fields for acceptance criteria
            if not acceptance_criteria:
                for field_key, field_value in fields.items():
                    if (
                        field_key.startswith("customfield_")
                        and field_value
                        and ("acceptance" in str(field_value).lower() or "criteria" in str(field_value).lower())
                    ):
                        # Try to parse it as acceptance criteria
                        if isinstance(field_value, list):
                            acceptance_criteria.extend(field_value)
                        elif isinstance(field_value, str) and "\n" in field_value:
                            acceptance_criteria.extend(field_value.split("\n"))

            # Clean HTML from description for better AI processing
            clean_description = description
            if description:
                # Remove HTML tags but preserve structure
                clean_description = re.sub(r"<h\d[^>]*>([^<]+)</h\d>", r"\n\n### \1\n", description)
                clean_description = re.sub(r"<b>([^<]+)</b>", r"**\1**", clean_description)
                clean_description = re.sub(r"<tt>([^<]+)</tt>", r"`\1`", clean_description)
                clean_description = re.sub(r"<li>([^<]+)</li>", r"\n- \1", clean_description)
                clean_description = re.sub(r"<[^>]+>", "", clean_description)
                clean_description = re.sub(r"\n\s*\n+", "\n\n", clean_description).strip()

            baml_request = {
                "issue": {
                    "key": issue_key,
                    "summary": issue_summary,
                    "description": clean_description,
                    "issue_type": issue_type,
                    "priority": priority,
                    "acceptance_criteria": acceptance_criteria if acceptance_criteria else None,
                    "components": [c.get("name", "") for c in fields.get("components", [])]
                    if isinstance(fields.get("components"), list)
                    else None,
                    "labels": fields.get("labels", []) if "labels" in fields else None,
                    "story_points": fields.get("storyPoints")
                    or fields.get("story_points")
                    or fields.get("customfield_10002"),
                    "epic_link": fields.get("epic", {}).get("key")
                    if isinstance(fields.get("epic"), dict)
                    else fields.get("customfield_10001"),
                },
                "include_edge_cases": workflow_input.include_edge_cases,
                "include_negative_tests": workflow_input.include_negative_tests,
                "include_security_tests": workflow_input.include_security_tests,
                "test_priorities": workflow_input.test_case_priority,
            }

            # Log the BAML request
            workflow.logger.info(f"BAML Request: {json.dumps(baml_request, indent=2)}")
            workflow.logger.info("=" * 80)

            # Execute BAML transform to generate test cases
            baml_path = (
                Path(self.project_root) / "workflows" / "jira_test_generation" / "baml_src" / "generate_test_cases.baml"
            )

            # Read the BAML content
            baml_content = await awa_activity.read_file(str(baml_path))

            # Create TransformParams
            transform_params = TransformParams(
                baml_function_name="GenerateTestCases",
                baml_content=baml_content,
                request=baml_request,
            )

            result = await awa_workflow.execute_baml_transform(
                transform_params=transform_params,
                additional_workflow_id_part=issue_key,  # Add unique issue key to prevent collisions
            )

            # Parse the result and create TestSuite
            test_cases = []
            for idx, test_case_data in enumerate(result.get("test_cases", [])):
                # Handle test_data which might be a dict/object
                test_data_value = test_case_data.get("test_data", "")
                if isinstance(test_data_value, dict):
                    # Convert TestDataSet object to string format
                    test_data_parts = []
                    if test_data_value.get("input_data"):
                        test_data_parts.append(test_data_value["input_data"])
                    if test_data_value.get("expected_outputs"):
                        test_data_parts.append(f"Expected: {test_data_value['expected_outputs']}")
                    if test_data_value.get("boundary_values"):
                        test_data_parts.append(f"Boundaries: {', '.join(test_data_value['boundary_values'])}")
                    if test_data_value.get("invalid_inputs"):
                        test_data_parts.append(f"Invalid: {', '.join(test_data_value['invalid_inputs'])}")
                    test_data_str = " | ".join(test_data_parts) if test_data_parts else ""
                else:
                    test_data_str = str(test_data_value) if test_data_value else ""

                test_case = TestCase(
                    test_id=f"TC{issue_key.replace('-', '')}_{idx + 1:03d}",
                    jira_issue=issue_key,
                    test_name=test_case_data.get("name", f"Test {idx + 1}"),
                    test_type=test_case_data.get("type", "Functional"),
                    priority=test_case_data.get("priority", "P2"),
                    preconditions="|".join(test_case_data.get("preconditions", [])),
                    test_steps="|".join(test_case_data.get("test_steps", [])),
                    expected_results="|".join(test_case_data.get("expected_results", [])),
                    test_data=test_data_str,
                    tags=",".join(test_case_data.get("tags", [])),
                    automation_status=test_case_data.get("automation_status", "Ready for Automation"),
                )
                test_cases.append(test_case)

            return TestSuite(
                jira_issue_key=issue_key,
                issue_summary=issue_summary,
                test_cases=test_cases,
                coverage_summary=result.get("coverage_summary", ""),
            )

        except (ValueError, KeyError, TypeError) as e:
            workflow.logger.error(f"Failed to generate test cases for {issue_key}: {e}")
            return TestSuite(
                jira_issue_key=issue_key,
                issue_summary=issue_summary,
                test_cases=[],
                coverage_summary=f"Error generating test cases: {e!s}",
            )

    def _generate_csv(self, test_suites: list[TestSuite], csv_format: str) -> str:
        """Generate CSV content from test suites."""
        output = io.StringIO()

        # Define headers based on format
        if csv_format == "ado":
            headers = [
                "Work Item Type",
                "Title",
                "Test Type",
                "Priority",
                "Steps",
                "Expected Result",
                "Tags",
                "Automation Status",
                "Associated Work Item",
            ]
        elif csv_format == "testrail":
            headers = [
                "Title",
                "Section",
                "Type",
                "Priority",
                "Preconditions",
                "Steps",
                "Expected Result",
                "References",
            ]
        else:  # standard format
            headers = [
                "Test ID",
                "JIRA Issue",
                "Test Name",
                "Test Type",
                "Priority",
                "Preconditions",
                "Test Steps",
                "Expected Results",
                "Test Data",
                "Tags",
                "Automation Status",
            ]

        writer = csv.writer(output)
        writer.writerow(headers)

        # Write test cases
        for suite in test_suites:
            for test_case in suite.test_cases:
                if csv_format == "ado":
                    row = [
                        "Test Case",
                        test_case.test_name,
                        test_case.test_type,
                        test_case.priority,
                        test_case.test_steps,
                        test_case.expected_results,
                        test_case.tags,
                        test_case.automation_status,
                        test_case.jira_issue,
                    ]
                elif csv_format == "testrail":
                    row = [
                        test_case.test_name,
                        suite.issue_summary,
                        test_case.test_type,
                        test_case.priority,
                        test_case.preconditions,
                        test_case.test_steps,
                        test_case.expected_results,
                        test_case.jira_issue,
                    ]
                else:  # standard format
                    row = [
                        test_case.test_id,
                        test_case.jira_issue,
                        test_case.test_name,
                        test_case.test_type,
                        test_case.priority,
                        test_case.preconditions,
                        test_case.test_steps,
                        test_case.expected_results,
                        test_case.test_data or "",
                        test_case.tags,
                        test_case.automation_status,
                    ]
                writer.writerow(row)

        return output.getvalue()

    def _generate_markdown(self, test_suites: list[TestSuite]) -> str:  # noqa: PLR0915
        """Generate markdown content from test suites."""
        markdown_lines = []

        # Add header
        for suite in test_suites:
            markdown_lines.append(f"# Test Cases for {suite.jira_issue_key}: {suite.issue_summary}")
            markdown_lines.append("")

            # Add suite overview
            markdown_lines.append("## Test Suite Overview")
            markdown_lines.append(f"- **JIRA Issue**: {suite.jira_issue_key}")
            markdown_lines.append(f"- **Summary**: {suite.issue_summary}")
            markdown_lines.append(f"- **Total Test Cases**: {len(suite.test_cases)}")

            if suite.coverage_summary:
                markdown_lines.append(f"- **Coverage Summary**: {suite.coverage_summary}")

            # Count test types and priorities
            test_types = {}
            priorities = {}
            for test_case in suite.test_cases:
                test_types[test_case.test_type] = test_types.get(test_case.test_type, 0) + 1
                priorities[test_case.priority] = priorities.get(test_case.priority, 0) + 1

            markdown_lines.append(f"- **Test Types**: {', '.join([f'{k} ({v})' for k, v in test_types.items()])}")
            markdown_lines.append(
                f"- **Priorities**: {', '.join([f'{k} ({v})' for k, v in sorted(priorities.items())])}",
            )
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")

            # Add test case details
            markdown_lines.append("## Test Case Details")
            markdown_lines.append("")

            for idx, test_case in enumerate(suite.test_cases, 1):
                markdown_lines.append(f"### TC-{idx:03d}: {test_case.test_name}")
                markdown_lines.append(
                    f"**Type**: {test_case.test_type} | "
                    f"**Priority**: {test_case.priority} | "
                    f"**Status**: {test_case.automation_status}",
                )
                markdown_lines.append("")

                # Add preconditions if present
                if test_case.preconditions:
                    markdown_lines.append("**Preconditions**:")
                    markdown_lines.extend(
                        f"- {precondition.strip()}"
                        for precondition in test_case.preconditions.split("|")
                        if precondition.strip()
                    )
                    markdown_lines.append("")

                # Add test steps
                markdown_lines.append("**Test Steps**:")
                steps = test_case.test_steps.split("|")
                for step_num, step in enumerate(steps, 1):
                    if step.strip():
                        # Check if step already has numbering
                        step_text = step.strip()
                        if not step_text[0].isdigit():
                            markdown_lines.append(f"{step_num}. {step_text}")
                        else:
                            markdown_lines.append(step_text)
                markdown_lines.append("")

                # Add expected results
                markdown_lines.append("**Expected Results**:")
                results = test_case.expected_results.split("|")
                markdown_lines.extend(f"- {result.strip()}" for result in results if result.strip())
                markdown_lines.append("")

                # Add test data if present
                if test_case.test_data:
                    markdown_lines.append("**Test Data**:")
                    # Format test data nicely
                    data_parts = test_case.test_data.split(" | ")
                    for part in data_parts:
                        if part.strip():
                            # Check if it's JSON-like data
                            if part.strip().startswith("{"):
                                markdown_lines.append("```json")
                                # Try to pretty print JSON
                                try:
                                    data_dict = json.loads(part.strip())
                                    markdown_lines.append(json.dumps(data_dict, indent=2))
                                except (json.JSONDecodeError, ValueError):
                                    markdown_lines.append(part.strip())
                                markdown_lines.append("```")
                            else:
                                markdown_lines.append(f"- {part.strip()}")
                    markdown_lines.append("")

                # Add tags
                if test_case.tags:
                    markdown_lines.append(f"**Tags**: {test_case.tags}")
                    markdown_lines.append("")

                markdown_lines.append("---")
                markdown_lines.append("")

            # Add coverage analysis section
            markdown_lines.append("## Test Coverage Summary")
            markdown_lines.append("")

            # By test type
            markdown_lines.append("### By Test Type")
            for test_type, count in test_types.items():
                percentage = (count / len(suite.test_cases)) * 100 if suite.test_cases else 0
                markdown_lines.append(f"- **{test_type}**: {count} ({percentage:.1f}%)")
            markdown_lines.append("")

            # By priority
            markdown_lines.append("### By Priority")
            for priority, count in sorted(priorities.items()):
                markdown_lines.append(f"- **{priority}**: {count} test cases")
            markdown_lines.append("")

            # By automation status
            automation_status = {}
            for test_case in suite.test_cases:
                status = test_case.automation_status
                automation_status[status] = automation_status.get(status, 0) + 1

            markdown_lines.append("### Automation Status")
            for status, count in automation_status.items():
                percentage = (count / len(suite.test_cases)) * 100 if suite.test_cases else 0
                markdown_lines.append(f"- **{status}**: {count} ({percentage:.1f}%)")
            markdown_lines.append("")

            # Add notes section
            markdown_lines.append("## Notes")
            markdown_lines.append(f"- Test cases generated for JIRA issue {suite.jira_issue_key}")
            markdown_lines.append(f"- Total of {len(suite.test_cases)} test cases created")
            markdown_lines.append(f"- Generated on: {Path(self.workflow_paths.output).name}")

        return "\n".join(markdown_lines)

    async def _generate_issue_outputs(
        self,
        test_suites: list[TestSuite],
        output_dir: Path,
        workflow_input: JiraToTestCasesInput,
    ) -> None:
        """Generate all output files for a single issue."""
        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate CSV output
        csv_content = self._generate_csv(test_suites, workflow_input.csv_format)
        csv_file_path = output_dir / "test_cases.csv"
        await awa_activity.write_file(str(csv_file_path), csv_content)

        # Generate Markdown output
        markdown_content = self._generate_markdown(test_suites)
        markdown_file_path = output_dir / "test_cases.md"
        await awa_activity.write_file(str(markdown_file_path), markdown_content)

        # Generate summary report
        summary = self._generate_summary_report(test_suites)
        summary_file_path = output_dir / "test_generation_summary.md"
        await awa_activity.write_file(str(summary_file_path), summary)

        workflow.logger.info(f"Generated outputs for issue in {output_dir}")

    async def _generate_aggregate_summary(
        self,
        all_test_suites: list[TestSuite],
        base_output_dir: Path,
    ) -> None:
        """Generate an aggregate summary when processing multiple issues."""
        from datetime import datetime

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

        markdown_lines = [
            "# Batch Test Generation Summary",
            f"*Generated on: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Overview",
            f"- **Total Issues Processed**: {len(all_test_suites)}",
            f"- **Total Test Cases Generated**: {sum(len(s.test_cases) for s in all_test_suites)}",
            "",
            "## Issues Processed",
            "",
        ]

        # Add summary table
        markdown_lines.append("| Issue Key | Summary | Test Cases | Coverage |")
        markdown_lines.append("|-----------|---------|------------|----------|")

        for suite in all_test_suites:
            test_count = len(suite.test_cases)
            max_coverage_length = 50
            coverage = (
                suite.coverage_summary[:max_coverage_length] + "..."
                if len(suite.coverage_summary) > max_coverage_length
                else suite.coverage_summary
            )
            markdown_lines.append(
                f"| {suite.jira_issue_key} | {suite.issue_summary[:40]}... | {test_count} | {coverage} |",
            )

        markdown_lines.extend(
            [
                "",
                "## Test Type Distribution",
                "",
            ],
        )

        # Aggregate test type counts
        test_type_counts: dict[str, int] = {}
        for suite in all_test_suites:
            for test_case in suite.test_cases:
                test_type_counts[test_case.test_type] = test_type_counts.get(test_case.test_type, 0) + 1

        for test_type, count in sorted(test_type_counts.items()):
            markdown_lines.append(f"- **{test_type}**: {count}")

        markdown_lines.extend(
            [
                "",
                "## Priority Distribution",
                "",
            ],
        )

        # Aggregate priority counts
        priority_counts: dict[str, int] = {}
        for suite in all_test_suites:
            for test_case in suite.test_cases:
                priority_counts[test_case.priority] = priority_counts.get(test_case.priority, 0) + 1

        priority_lines = [
            f"- **{priority}**: {priority_counts[priority]}"
            for priority in ["P1", "P2", "P3"]
            if priority in priority_counts
        ]
        markdown_lines.extend(priority_lines)

        markdown_lines.extend(
            [
                "",
                "## Individual Issue Reports",
                "",
            ],
        )

        issue_report_lines = [
            f"- [{suite.jira_issue_key}](./{suite.jira_issue_key}/test_generation_summary.md)"
            for suite in all_test_suites
        ]
        markdown_lines.extend(issue_report_lines)

        # Write the aggregate summary
        summary_file = base_output_dir / f"batch_summary_{timestamp}.md"
        await awa_activity.write_file(str(summary_file), "\n".join(markdown_lines))

        workflow.logger.info(f"Generated batch summary: {summary_file}")

    def _generate_summary_report(self, test_suites: list[TestSuite]) -> str:
        """Generate a markdown summary report of test generation."""
        total_test_cases = sum(len(suite.test_cases) for suite in test_suites)

        # Count test types
        test_type_counts: dict[str, int] = {}
        priority_counts: dict[str, int] = {}
        automation_counts: dict[str, int] = {}

        for suite in test_suites:
            for test_case in suite.test_cases:
                test_type_counts[test_case.test_type] = test_type_counts.get(test_case.test_type, 0) + 1
                priority_counts[test_case.priority] = priority_counts.get(test_case.priority, 0) + 1
                automation_counts[test_case.automation_status] = (
                    automation_counts.get(test_case.automation_status, 0) + 1
                )

        report = f"""# Test Generation Summary Report

## Overview
- **Total JIRA Issues Processed**: {len(test_suites)}
- **Total Test Cases Generated**: {total_test_cases}
- **Average Test Cases per Issue**: {total_test_cases / len(test_suites) if test_suites else 0:.1f}

## Test Type Distribution
"""
        for test_type, count in sorted(test_type_counts.items()):
            report += f"- **{test_type}**: {count} test cases\n"

        report += "\n## Priority Distribution\n"
        for priority, count in sorted(priority_counts.items()):
            report += f"- **{priority}**: {count} test cases\n"

        report += "\n## Automation Readiness\n"
        for status, count in sorted(automation_counts.items()):
            report += f"- **{status}**: {count} test cases\n"

        report += "\n## Issues Processed\n"
        for suite in test_suites:
            report += f"\n### {suite.jira_issue_key}: {suite.issue_summary}\n"
            report += f"- **Test Cases Generated**: {len(suite.test_cases)}\n"
            if suite.coverage_summary:
                report += f"- **Coverage Summary**: {suite.coverage_summary}\n"

        return report
