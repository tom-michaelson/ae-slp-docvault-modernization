from pydantic import BaseModel, Field


class TestDoctorWorkflowInput(BaseModel):
    """Input for the TestDoctorWorkflow."""

    __test__ = False

    branch_name: str = Field(..., description="The name of the feature branch to analyze.")
    base_branch: str = Field(..., description="The name of the base branch to compare against (e.g., 'main').")
    repo_path: str = Field(..., description="The absolute path to the root of the repository.")
    working_directory: str = Field(
        ...,
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
