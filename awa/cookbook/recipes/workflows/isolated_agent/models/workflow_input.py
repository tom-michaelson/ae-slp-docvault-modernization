"""Input models for isolated agent workflows."""

from pydantic import BaseModel, Field


class SampleIsolatedAgentActWorkflowInput(BaseModel):
    """Input for the SampleIsolatedAgentActWorkflow."""

    repo_path: str = Field(..., description="Path to the git repository")
    branch: str = Field(default="main", description="Branch to work on")


class SampleIsolatedAgentAnalyzeWorkflowInput(BaseModel):
    """Input for the SampleIsolatedAgentAnalyzeWorkflow."""

    directory_path: str = Field(..., description="Path to the directory to analyze")
    output_directory: str = Field(
        default="awa-agent-output",
        description="Directory where analysis results will be saved",
    )
