import json
from typing import TYPE_CHECKING, Any

import httpx
from temporalio import activity

from awa.core.utils.config_loader import ConfigLoader
from awa.core.utils.markdown_to_jira_converter import convert_markdown_to_jira_wiki_format
from awa.sdk import constants as sdk_constants
from awa.sdk.models.exceptions.fatal_application_error import FatalApplicationError
from awa.sdk.models.exceptions.retryable_application_error import RetryableApplicationError
from awa.sdk.models.jira_issue_request import JiraIssueRequest
from awa.sdk.models.jira_issue_response import JiraIssueResponse

if TYPE_CHECKING:
    from awa.core.models.config.app_config import AppConfig


@activity.defn(name=sdk_constants.ACTIVITY_READ_JIRA_ISSUE)
async def read_jira_issue(
    request: JiraIssueRequest,
) -> JiraIssueResponse:
    if not request.key:
        raise FatalApplicationError("Jira issue key is required to read a Jira issue.")

    fields = "issuetype,components,key,summary,description,labels"
    response = await _execute_issue_request(
        method="GET",
        url_suffix=f"/{request.key}?fields={fields}",
        query_params={"expand": "renderedFields"},
    )

    return response


@activity.defn(name=sdk_constants.ACTIVITY_UPSERT_JIRA_ISSUE)
async def upsert_jira_issue(
    request: JiraIssueRequest,
) -> str:
    body = _build_request_body(request)
    body_json: str = json.dumps(body)
    response = await _execute_issue_request(
        method="PUT" if request.key else "POST",
        body_json=body_json,
        url_suffix=f"/{request.key}" if request.key else None,
    )

    if request.comments:
        for comment in request.comments:
            await _add_comment(request.key, comment)

    return response.key


@activity.defn(name=sdk_constants.ACTIVITY_ADD_JIRA_COMMENT)
async def add_jira_comment(
    request: JiraIssueRequest,
) -> None:
    if not request.key:
        raise FatalApplicationError("Jira issue key is required to add a comment.")

    for comment in request.comments:
        await _add_comment(request.key, comment)


async def _add_comment(key: str, comment: str) -> None:
    # Convert markdown comment to Jira wiki format for v2 API
    wiki_comment = convert_markdown_to_jira_wiki_format(comment)
    request_body = {
        "body": wiki_comment,
    }
    body_json: str = json.dumps(request_body)

    await _execute_issue_request(
        method="POST",
        body_json=body_json,
        url_suffix=f"/{key}/comment",
    )


async def _execute_issue_request(
    method: str,
    body_json: str | None = None,
    url_suffix: str | None = None,
    query_params: dict[str, Any] | None = None,
) -> JiraIssueResponse:
    app_config: AppConfig = ConfigLoader.get_config()

    restart_msg = "then restart the core AWA worker."

    if not app_config.jira:
        raise RetryableApplicationError(f"Jira is not configured. Please configure Jira in config.yaml, {restart_msg}")

    url_prefix = app_config.jira.url
    if not url_prefix or url_prefix == "":
        raise RetryableApplicationError(
            f"Jira URL is not configured. Please configure `jira.url` in config.yaml, {restart_msg}",
        )

    api_user = app_config.jira.api_user
    if not api_user or api_user == "":
        raise RetryableApplicationError(
            f"Jira API user is not configured. Please configure `jira.api_user` in config.yaml, {restart_msg}",
        )

    api_key = app_config.jira.api_key
    if not api_key or api_key == "":
        raise RetryableApplicationError(
            f"Jira API key is not configured. Please configure `JIRA_API_KEY` in .env, {restart_msg}",
        )

    url = f"{url_prefix}/rest/api/2/issue{url_suffix if url_suffix else ''}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    response: httpx.Response
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            content=body_json if body_json else None,
            headers=headers,
            auth=(api_user, api_key),
            params=query_params if query_params else None,
        )

    response_json: dict[str, Any] = response.json()
    if not response.is_success:
        short_error_msg = (
            f"Failed to create requested Jira issue: {response.status_code}."
            f"\n\nResponse:\n{json.dumps(response_json, indent=2)}"
        )
        error_msg = f"{short_error_msg}\n\nRequest:\n{body_json}"
        activity.logger.error(error_msg)

        if response.status_code >= 500:  # noqa: PLR2004
            # 500s are potentially retryable
            raise RetryableApplicationError(short_error_msg)
        # 400s are issues with the request, so retrying will not help
        raise FatalApplicationError(short_error_msg)

    key = response_json.get("key")

    typed_response = JiraIssueResponse(key=key)
    if "fields" in response_json:
        if "summary" in response_json["fields"]:
            typed_response.summary = response_json["fields"]["summary"]
        if "issuetype" in response_json["fields"]:
            typed_response.issue_type = response_json["fields"]["issuetype"]["name"]
    if "renderedFields" in response_json and "description" in response_json["renderedFields"]:
        typed_response.description = response_json["renderedFields"]["description"]

    return typed_response


def _build_request_body(request: JiraIssueRequest) -> dict[str, Any]:
    description_wiki = convert_markdown_to_jira_wiki_format(request.description)
    body = {
        "fields": {
            "summary": request.summary,
            "description": description_wiki,
            "project": {"key": request.project_id},
        },
    }

    if request.tags:
        body["fields"]["labels"] = request.tags

    body["fields"].update(
        {
            "parent": ({"key": request.parent} if request.parent else body["fields"].get("parent", {})),
        },
    )

    issue_type = _determine_issue_type(request)

    body["fields"].setdefault("issuetype", {})
    body["fields"]["issuetype"]["name"] = issue_type

    return body


def _determine_issue_type(request: JiraIssueRequest) -> str:
    issue_type: str = "Story"
    if request.issue_type:
        issue_type = request.issue_type
    elif request.parent:
        issue_type = "Subtask"
    return issue_type
