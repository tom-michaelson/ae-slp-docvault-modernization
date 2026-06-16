from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class DevelopWorkflowInput(BaseModel):
    """Input for the generic develop workflow.

    Runs page planning + implementation over a set of pages identified by the
    upstream ``awa-discover`` workflow.
    """

    pages: list[str] = Field(
        ...,
        description="Page keys to implement. Each must have a Discover entry under docs_dir.",
    )
    target_stack: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Target modernization stack. Defaults to 'angular-java'. Forwarded to the "
            "planning, implementation, and test-generation slash commands."
        ),
    )
    target_repo_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Directory housing the modernization target (Java/Angular) codebase. "
            "Passed as a slash-command argument so commands can write source files "
            "with absolute paths. Defaults to .../new-modernization-sdlc/target_repo."
        ),
    )
    project_root_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Project root where .claude/commands/ lives; used as the agent cwd for "
            "every phase AND as the working dir for git operations. Defaults to "
            "'/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc'."
        ),
    )
    docs_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Directory where Discover artifacts live and where develop artifacts are written. "
            "Defaults to .../new-modernization-sdlc/docs."
        ),
    )
    legacy_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Legacy source directory. Defaults to '../eShopOnWeb'.",
    )
    starting_branch: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Base branch to stack work on. Defaults to 'main'.",
    )
    max_concurrency: int = Field(
        default=5,
        description="Maximum number of concurrent child workflows within a phase.",
    )
