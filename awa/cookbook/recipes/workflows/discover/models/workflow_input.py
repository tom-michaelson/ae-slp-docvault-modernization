from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class DiscoverWorkflowInput(BaseModel):
    """Input for the generic discover workflow.

    The workflow inventories UI pages from a legacy codebase and captures a screenshot
    of each one for downstream modernization analysis.
    """

    target_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Filesystem path to the legacy code directory. Typically a sibling of this repo "
            'such as "../eShopOnWeb". If omitted, falls back to "../eShopOnWeb".'
        ),
    )
    app_url: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Base URL of the running legacy application used for screenshots. "
            'If omitted, falls back to "http://localhost:5106" (the eShopOnWeb '
            "`docker compose up` default)."
        ),
    )
    target_stack: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Optional target modernization stack (e.g. 'react', 'blazor', 'spring-boot'). "
            "Forwarded to the planning slash commands so they can shape technical plans "
            "appropriately. Has no effect on the discovery phases."
        ),
    )
    docs_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Directory where discovery artifacts are written. Defaults to "
            "'/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc/docs' so that "
            "outputs live alongside this repo rather than the legacy codebase."
        ),
    )
    target_repo_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Directory housing the modernization target (Java/Angular) codebase. "
            "Passed as a slash-command argument so commands can write source files "
            "with absolute paths. Defaults to "
            "'/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc/target_repo'."
        ),
    )
    project_root_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Project root where .claude/commands/ lives; used as the agent cwd for "
            "every phase so slash commands resolve. Defaults to "
            "'/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc'."
        ),
    )
    agent_provider: str = Field(
        default="claude",
        description=(
            "Agent provider used to execute slash commands in each phase. "
            "Supported values: 'claude', 'github_copilot', 'goose', 'codex', "
            "'opencode', 'gemini', 'q'. Defaults to 'claude'."
        ),
    )
    max_concurrency: int = Field(
        default=5,
        description="Maximum number of concurrent child workflows within a phase.",
    )
    skip_screenshots: bool = Field(
        default=False,
        description=(
            "When True, the screenshot phase in Phase 2 is skipped entirely. "
            "Useful when the legacy application is not running."
        ),
    )
