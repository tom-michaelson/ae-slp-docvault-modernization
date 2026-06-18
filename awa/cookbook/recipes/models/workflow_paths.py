from pydantic import BaseModel
from pydantic.json_schema import SkipJsonSchema


class WorkflowPaths(BaseModel):
    input: str
    output: str
    baml_src: str
    agent_prompts: str | SkipJsonSchema[None] = None
    project_root: str | SkipJsonSchema[None] = None
    workflow_root: str | SkipJsonSchema[None] = None
