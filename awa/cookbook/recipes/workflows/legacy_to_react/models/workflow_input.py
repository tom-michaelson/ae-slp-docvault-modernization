from pathlib import Path

from pydantic import BaseModel, Field

from sdk_dist.python.awa.client.models import WorkflowPaths


class LegacyToReactWorkflowInput(BaseModel):
    cobol_file_path: str | Path = Field(
        default="input/legacy_code.cbl",
        description="Path to COBOL file to convert",
    )
    jira_project_key: str = Field(
        description="JIRA project key for story creation",
    )
    jira_instance_url: str = Field(
        description="JIRA instance URL",
    )
    react_app_path: str | Path = Field(
        default="input/react-baseline-app",
        description="Path to baseline React app",
    )
    workflow_paths: WorkflowPaths | None = Field(default=None)
