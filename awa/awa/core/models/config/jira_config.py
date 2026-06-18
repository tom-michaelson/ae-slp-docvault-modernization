from pydantic import BaseModel, Field

from awa.core.models.config.env_config import EnvConfig


class JiraConfig(BaseModel):
    url: str | None = Field(default="https://slalom.atlassian.net", description="The URL of the Jira instance.")
    api_user: str | None = Field(
        default=None,
        description=(
            "The API user (email address) to use for Jira API authentication. "
            "Must be the owner of the API key in JIRA_API_KEY environment variable."
        ),
    )

    @property
    def api_key(self) -> str:
        return EnvConfig.get_env_config().jira_api_key
