from datetime import timedelta

from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models.jira_issue_request import JiraIssueRequest


async def add_jira_comment_activity(request: JiraIssueRequest) -> str:
    """Add a comment to a Jira issue using the provided request parameters.

    Args:
        request: JiraIssueRequest containing the issue and comment details.

    Returns:
        str: The result of the comment addition, typically the comment ID.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_ADD_JIRA_COMMENT,
        arg=request,
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.MCP_TIMEOUT_SECONDS),
    )
