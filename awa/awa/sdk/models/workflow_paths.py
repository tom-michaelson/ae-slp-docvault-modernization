from pydantic import BaseModel


class WorkflowPaths(BaseModel):
    input: str
    output: str
    baml_src: str
    agent_prompts: str | None = None
    project_root: str | None = None
    workflow_root: str | None = None
