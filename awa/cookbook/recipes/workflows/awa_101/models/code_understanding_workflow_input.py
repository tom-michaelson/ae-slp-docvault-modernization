from pathlib import Path

from pydantic import BaseModel, Field

from sdk_dist.python.awa.client.models import WorkflowPaths


class CodeUnderstandingWorkflowInput(BaseModel):
    code_file_path: str | Path | None = Field(default=None)
    workflow_paths: WorkflowPaths | None = Field(default=None)
