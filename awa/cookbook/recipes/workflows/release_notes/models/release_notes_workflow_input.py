from pydantic import BaseModel


class ReleaseNotesWorkflowInput(BaseModel):
    last_released_commit: str
    repo_path: str
    release_branch: str = "main"
