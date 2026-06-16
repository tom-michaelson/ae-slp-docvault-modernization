from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class JiraIssueResponse(BaseModel):
    key: str | SkipJsonSchema[None] = Field(default=None)
    summary: str | SkipJsonSchema[None] = Field(default=None)
    description: str | SkipJsonSchema[None] = Field(default=None)
    issue_type: str | SkipJsonSchema[None] = Field(default=None)
