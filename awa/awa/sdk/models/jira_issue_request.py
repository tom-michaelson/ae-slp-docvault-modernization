from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class JiraIssueRequest(BaseModel):
    project_id: str = Field()

    key: str | SkipJsonSchema[None] = Field(default=None)

    summary: str | SkipJsonSchema[None] = Field(default=None)
    description: str | SkipJsonSchema[None] = Field(default=None)
    issue_type: str | SkipJsonSchema[None] = Field(default=None)
    parent: str | SkipJsonSchema[None] = Field(default=None)
    tags: list[str] | SkipJsonSchema[None] = Field(default=None)
    comments: list[str] | SkipJsonSchema[None] = Field(default=None)
