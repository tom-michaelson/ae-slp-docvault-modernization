from datetime import timedelta

from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models.jira_issue_request import JiraIssueRequest
from awa.sdk.models.jira_issue_response import JiraIssueResponse


async def read_jira_issue_activity(request: JiraIssueRequest) -> JiraIssueResponse:
    """Read a Jira issue using the provided request parameters.

    Args:
        request: JiraIssueRequest containing the issue details to read.

    Returns:
        JiraIssueResponse: The response containing the Jira issue information.

    """
    return JiraIssueResponse.model_validate(
        await workflow.execute_activity(
            constants.ACTIVITY_READ_JIRA_ISSUE,
            arg=request,
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=constants.MCP_TIMEOUT_SECONDS),
        ),
    )
