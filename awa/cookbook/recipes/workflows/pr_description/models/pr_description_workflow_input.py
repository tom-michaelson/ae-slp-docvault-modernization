from pydantic import BaseModel


class PrDescriptionWorkflowInput(BaseModel):
    branch_name: str
    repo_path: str
    base_branch: str = "main"
