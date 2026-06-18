from datetime import timedelta

from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models.jira_issue_request import JiraIssueRequest


async def upsert_jira_issue_activity(request: JiraIssueRequest) -> str:
    """Create or update a Jira issue using the provided request parameters.

    Args:
        request: JiraIssueRequest containing the issue details to create or update.

    Returns:
        str: The result of the upsert operation, typically the issue key or ID.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_UPSERT_JIRA_ISSUE,
        arg=request,
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.MCP_TIMEOUT_SECONDS),
    )
