"""Models for the TestDoctor workflow."""

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class TestDoctorWorkflowInput(BaseModel):
    """Input for the TestDoctorWorkflow."""

    __test__ = False

    branch_name: str = Field(..., description="The name of the feature branch to analyze.")
    base_branch: str = Field(..., description="The name of the base branch to compare against (e.g., 'main').")
    repo_path: str = Field(..., description="The absolute path to the root of the repository.")
    working_directory: str | SkipJsonSchema[None] = Field(
        default="",
        description="The working directory relative to the repo path, where the agent will operate.",
    )
    testing_guidelines_path: str = Field(
        ...,
        description="Path to the file containing testing guidelines and mocking strategies.",
    )
    file_extensions: str = Field(
        ...,
        description="A comma-delimited string of file extensions to target for testing (e.g., 'py,cs,ts').",
    )
    tests_directory: str = Field(
        ...,
        description="The directory where generated tests should be placed, relative to the repository root.",
    )
    session_id: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Optional session ID for agent streaming integration.",
    )


class TestAndLintPipelineWorkflowInput(BaseModel):
    """Input for the TestAndLintPipelineWorkflow."""

    __test__ = False

    root_workflow_input: TestDoctorWorkflowInput
    file_path: str
    testing_guidelines_path: str
    tests_directory: str
    working_directory: str
    session_id: str | None = None
