from pydantic import BaseModel, Field


class GitHubPrDescriptionWorkflowInput(BaseModel):
    # Required GitHub PR information
    owner: str = Field(..., description="GitHub org/username")
    repo: str = Field(..., description="Repository name")
    pull_number: int = Field(..., description="PR number")

    # Optional - fetched from PR if not provided (use empty string as default instead of None)
    base_branch: str = Field("", description="Base branch (will be fetched from PR if not provided)")
    branch_name: str = Field("", description="Head branch (will be fetched from PR if not provided)")
