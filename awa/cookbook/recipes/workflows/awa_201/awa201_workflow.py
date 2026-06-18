import json
import os
from pathlib import Path

from pydantic.json_schema import SkipJsonSchema
from temporalio import workflow
from temporalio.exceptions import ApplicationError

from cookbook.recipes import constants
from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from cookbook.recipes.models.chunking import ChunkAndSummarizeInput, ChunkingStrategy
from cookbook.recipes.workflows.awa_201.create_documentation_page_workflow import CreateDocumentationPageWorkflow
from cookbook.recipes.workflows.awa_201.describe_directories_workflow import (
    DescribeDirectoriesWorkflow,
    DescribeDirectoriesWorkflowInput,
)
from cookbook.recipes.workflows.awa_201.models.documentation_site_outline import DocumentationSiteOutline
from cookbook.recipes.workflows.awa_201.models.workflow_input import Awa201WorkflowInput
from cookbook.recipes.workflows.awa_201.truncate_files_workflow import TruncateFilesWorkflow
from cookbook.recipes.workflows.common.chunk_and_summarize_workflow import ChunkAndSummarizeWorkflow
from sdk_dist.python.awa.client import awa_activity, awa_general, awa_workflow
from sdk_dist.python.awa.client.models import (
    AgentConfiguration,
    BuildPromptParams,
    InputParams,
    McpServer,
    TaskResponseModel,
    TransformParams,
    WorkflowPaths,
)

MAX_CONCURRENT_TRANSFORMS = os.environ.get("MAX_CONCURRENT_TRANSFORMS", constants.DEFAULT_MAX_CONCURRENT_TRANSFORMS)
MAX_CONCURRENT_AGENTS = os.environ.get("MAX_CONCURRENT_AGENTS", constants.DEFAULT_MAX_CONCURRENT_AGENTS)


class DocumentationValidationError(Exception):
    """Raised when documentation validation fails."""


# Possible future enhancements to this workflow:
# - Use single file diff to apply source-based doc edits
# - Utilize agent isolation workflow (git worktrees) for all agent act steps

# Examples
# - uv run -m awa.main run -w "awa-201-generate-documentation-site" -i '{"target_dir": "/Users/ryan.henderson/src/agentic-workflow-accelerator-cookbook/recipes/assets/aws-cards/src_to_analyze"}'  # noqa: E501
# - uv run -m awa.main run -w "awa-201-generate-documentation-site" -i '{"git_url": "https://github.com/example/repo.git", "git_branch": "main"}'  # noqa: E501


@recipe_exposed("Generates a documentation website for a given codebase")
@workflow.defn(name="awa-201-generate-documentation-site")
class Awa201Workflow:
    agent_provider: str = "claude"
    assets_dir: str = str(Path(__file__).parent.parent.parent.parent.parent / "assets")
    default_target_dir: str = str(Path(assets_dir) / "hello-world-csharp")
    # default_target_dir: str = str(Path(assets_dir) / "aws-cards" / "src_to_analyze")

    workflow_input: Awa201WorkflowInput | None = None
    workflow_paths: WorkflowPaths | None = None
    source_files: list[str] | None = None
    file_classifications_by_file: dict[str, dict] | None = None
    tech_stack: str | None = None
    application_summary_result: str | None = None
    source_files_in_docs: list[str] | None = None
    docs_site_outline: DocumentationSiteOutline | None = None
    cloned_repo_path: str | None = None

    @workflow.run
    async def run(self, workflow_input: Awa201WorkflowInput | SkipJsonSchema[None] = None) -> str:
        self.workflow_input = workflow_input
        self.agent_provider = (
            workflow_input.agent_provider if workflow_input and workflow_input.agent_provider else self.agent_provider
        )

        await self.step_01_define_paths(workflow_input)
        self.source_files = await self.step_02_copy_source_files()
        self.file_classifications_by_file = await self.step_03_classify_files()
        await self.step_04_describe_files()
        self.tech_stack = await self.step_05_describe_tech_stack()
        await self.step_06_describe_directories()
        self.application_summary_result = await self.step_07_create_application_summary()
        await self.step_08_copy_starter_docs()
        self.source_files_in_docs = await self.step_09_copy_source_files_into_docs_site()
        self.docs_site_outline = await self.step_10_create_documentation_site_outline()
        await self.step_11_create_all_docs_pages()
        await self.step_12_validate_docs_site()
        await self.step_13_build_documentation_site()
        await self.step_14_publish_documentation_site()

        return "Done."

    async def step_01_define_paths(self, workflow_input: Awa201WorkflowInput | None = None) -> None:
        self.workflow_paths: WorkflowPaths = awa_general.get_workflow_paths(
            Path(__file__).parent,
            workflow.info(),
        )

        if not workflow_input:
            workflow_input = Awa201WorkflowInput(
                target_dir=self.default_target_dir,
            )
        self.workflow_input = workflow_input

        # Validate that either target_dir or git_url is provided
        if not self.workflow_input.target_dir and not self.workflow_input.git_url:
            raise ApplicationError("Either target_dir or git_url must be provided", non_retryable=True)

        self.gitignore_path = str(Path(self.workflow_paths.input) / "target.gitignore")
        self.docs_starter_path = str(Path(self.workflow_paths.project_root) / "assets" / "vitepress-starter")
        self.source_dir = str(Path(self.workflow_paths.output) / "source")
        self.descriptions_dir = str(Path(self.workflow_paths.output) / "descriptions")
        self.short_descriptions_dir = str(Path(self.workflow_paths.output) / "short_descriptions")
        self.directory_descriptions_dir = str(Path(self.workflow_paths.output) / "directory_descriptions")

    async def step_02_copy_source_files(self) -> list[str]:
        # Determine the source path based on input type
        source_path = None

        if self.workflow_input.git_url:
            # Clone the Git repository to a temporary location
            workflow.logger.info(f"Cloning Git repository: {self.workflow_input.git_url}")

            # Use the AWA SDK git clone function
            self.cloned_repo_path = await awa_activity.git_clone(
                git_url=self.workflow_input.git_url,
                destination_path=None,  # Let the activity create a temp directory
                branch=self.workflow_input.git_branch,
            )

            workflow.logger.info(f"Repository cloned to: {self.cloned_repo_path}")
            source_path = self.cloned_repo_path
        else:
            # Use the provided target directory
            source_path = self.workflow_input.target_dir

        # Copy the source files to our working directory
        return await awa_activity.copy_directory(
            source_path=source_path,
            destination_path=self.source_dir,
            ignore_file_path=self.gitignore_path,
        )

    async def step_03_classify_files(self) -> None:
        # Create truncated copies of files for classification using child workflow
        truncated_files_dir = str(Path(self.workflow_paths.output) / "truncated_for_classification")
        truncated_files = await workflow.execute_child_workflow(
            TruncateFilesWorkflow,
            args=[self.source_files, truncated_files_dir, 5000],
            id=f"TruncateFiles-{workflow.uuid4()}",
            static_summary="TruncateFiles",
        )

        # Build the classification transform params using truncated files
        classify_files_transform_params_by_key: dict[str, TransformParams] = {}
        for original_file, truncated_file in zip(self.source_files, truncated_files, strict=False):
            # Use original file path as key but truncated file for content
            relative_file_path = Path(original_file).relative_to(self.source_dir)
            classify_files_transform_params_by_key[str(original_file)] = TransformParams(
                baml_function_name="ClassifyFile",
                request={"file_name": str(relative_file_path)},
                inputs=[InputParams(name="file_content", path=str(truncated_file))],
            )

        return await awa_workflow.execute_baml_transform_batch(
            baml_path=str(Path(self.workflow_paths.baml_src) / "classify_file.baml"),
            baml_requests_by_key=classify_files_transform_params_by_key,
        )

    async def step_04_describe_files(self) -> None:
        await workflow.execute_child_workflow(
            "describe-files",
            args=[
                self.workflow_paths,
                self.file_classifications_by_file,
                self.descriptions_dir,
                self.short_descriptions_dir,
                self.source_dir,
            ],
            id=f"DescribeFiles-{workflow.uuid4()}",
            static_summary="DescribeFiles",
        )

    async def step_05_describe_tech_stack(self) -> str:
        tech_stack: str = ""
        for file in self.source_files:
            file_category = self.file_classifications_by_file[file].get("file_category", "UNKNOWN")
            if file_category == "DEPENDENCY_MANIFEST":
                # Deliberately not done in parallel -- we're iteratively building the tech stack artifact
                transform_params = TransformParams(
                    baml_function_name="DescribeTechStack",
                    request={
                        "file_name": file,
                        "tech_stack": tech_stack,
                    },
                    inputs=[InputParams(name="file_content", path=str(file))],
                    output_path=str(Path(self.workflow_paths.output) / "tech_stack.md"),
                )
                tech_stack = await awa_workflow.execute_baml_transform(
                    transform_params=transform_params,
                    baml_path=str(Path(self.workflow_paths.baml_src) / "describe_tech_stack.baml"),
                )
        return tech_stack

    async def step_06_describe_directories(self) -> None:
        await workflow.execute_child_workflow(
            DescribeDirectoriesWorkflow,
            arg=DescribeDirectoriesWorkflowInput(
                workflow_paths=self.workflow_paths,
                source_dir=self.source_dir,
                directory_descriptions_dir=self.directory_descriptions_dir,
                short_descriptions_dir=self.short_descriptions_dir,
                max_content_length=self.workflow_input.max_content_length if self.workflow_input else 50000,
                max_chunk_length=self.workflow_input.max_chunk_length if self.workflow_input else 20000,
            ),
            id=f"DescribeDirectories-{workflow.uuid4()}",
            static_summary="DescribeDirectories",
        )

    async def step_07_create_application_summary(self) -> None:
        # Read directory descriptions
        directory_description_results = await awa_activity.read_directory(
            source_path=self.directory_descriptions_dir,
        )
        directory_descriptions = {result.file: result.content for result in directory_description_results}

        # Read file descriptions
        file_description_results = await awa_activity.read_directory(
            source_path=self.descriptions_dir,
        )
        file_descriptions = {result.file: result.content for result in file_description_results}

        # Combine all descriptions into a list
        all_descriptions = []

        # Add directory descriptions
        for file_path, content in directory_descriptions.items():
            if content.strip():
                relative_path = Path(file_path).relative_to(self.directory_descriptions_dir)
                dir_name = str(relative_path.parent) if relative_path.parent != Path() else "root"
                all_descriptions.append(f"Directory {dir_name}: {content.strip()}")

        # Add file descriptions
        for file_path, content in file_descriptions.items():
            if content.strip():
                relative_path = Path(file_path).relative_to(self.descriptions_dir)
                all_descriptions.append(f"File {relative_path}: {content.strip()}")

        # Calculate total content length
        total_length = sum(len(desc) for desc in all_descriptions)
        total_length += len(self.tech_stack) if self.tech_stack else 0

        # Get max content and chunk lengths from workflow input or use defaults
        max_content_length = self.workflow_input.max_content_length if self.workflow_input else 50000
        max_chunk_length = self.workflow_input.max_chunk_length if self.workflow_input else 20000

        # Check if we need to chunk and summarize
        if total_length > max_content_length:
            workflow.logger.info(
                f"Application summary has {total_length} chars of content, using chunking",
            )

            # Use the chunk and summarize workflow
            chunk_result = await workflow.execute_child_workflow(
                ChunkAndSummarizeWorkflow,
                ChunkAndSummarizeInput(
                    content_items=all_descriptions,
                    max_content_length=max_content_length,
                    max_chunk_length=max_chunk_length,
                    chunking_strategy=ChunkingStrategy.LIST_ITEMS,
                    context_data={
                        "tech_stack": self.tech_stack,
                        "application_type": "application_summary",
                    },
                    baml_path=str(
                        Path(self.workflow_paths.baml_src)
                        / ".."
                        / ".."
                        / "common"
                        / "baml_src"
                        / "chunking_summarization.baml",
                    ),
                    chunk_summary_function="SummarizeApplicationChunk",
                    final_summary_function="SummarizeApplicationFinal",
                ),
                id=f"ChunkAndSummarize-AppSummary-{workflow.uuid4()}",
                static_summary="ChunkAndSummarize-AppSummary",
            )

            application_summary = chunk_result.final_summary
        else:
            # Use regular BAML to create the application summary
            transform_params = TransformParams(
                baml_function_name="SummarizeApplication",
                request={
                    "tech_stack": self.tech_stack,
                },
                inputs=[
                    InputParams(name="directory_descriptions", path=self.directory_descriptions_dir),
                    InputParams(name="file_descriptions", path=self.descriptions_dir),
                ],
            )
            application_summary = await awa_workflow.execute_baml_transform(
                transform_params=transform_params,
                baml_path=str(Path(self.workflow_paths.baml_src) / "summarize_application.baml"),
            )

        # Save the application summary
        await awa_activity.write_file(
            file_path=str(Path(self.workflow_paths.output) / "application_summary.md"),
            content=application_summary,
        )

    async def step_08_copy_starter_docs(self) -> None:
        await awa_activity.copy_directory(
            source_path=self.docs_starter_path,
            destination_path=str(Path(self.workflow_paths.output) / "docs-site"),
            ignore_file_path=str(Path(self.workflow_paths.input) / "target.gitignore"),
        )

    async def step_09_copy_source_files_into_docs_site(self) -> None:
        return await awa_activity.copy_directory(
            source_path=self.source_dir,
            destination_path=str(Path(self.workflow_paths.output) / "docs-site" / "source"),
        )

    async def step_10_create_documentation_site_outline(self) -> DocumentationSiteOutline:
        working_dir = str(Path(self.workflow_paths.output) / "docs-site")
        analysis_dir = Path(working_dir) / "analysis"

        # Copy directory and file descriptions to analysis folder
        directory_descriptions_path = str(analysis_dir / "directory_descriptions")
        await awa_activity.copy_directory(
            source_path=self.directory_descriptions_dir,
            destination_path=directory_descriptions_path,
        )
        file_descriptions_path = str(analysis_dir / "file_descriptions")
        await awa_activity.copy_directory(
            source_path=self.descriptions_dir,
            destination_path=file_descriptions_path,
        )

        output_schema = json.dumps(DocumentationSiteOutline.model_json_schema())
        agent_config = AgentConfiguration(
            provider=self.agent_provider,
            mode="analyze",
            build_prompt_params=BuildPromptParams(
                template_input={
                    "path": str(Path(self.workflow_paths.agent_prompts) / "create_docs_site_outline.jinja"),
                },
                variables={
                    "application_summary": self.application_summary_result,
                    "tech_stack": self.tech_stack,
                    "source_files_list": self.source_files_in_docs,
                    "output_schema": output_schema,
                    "directory_descriptions_path": directory_descriptions_path,
                    "file_descriptions_path": file_descriptions_path,
                },
            ),
            working_directory=str(working_dir),
            initialize=False,
            # output_schema=output_schema,
            stream_enabled=True,
        )
        docs_site_outline_agent_result: TaskResponseModel = await awa_workflow.execute_agent(
            name="CreateDocsSiteOutline",
            agent_config=agent_config,
        )
        if docs_site_outline_agent_result.status != "completed":
            raise ApplicationError("Failed to create documentation site outline", non_retryable=True)

        outline_content = await awa_activity.read_file(str(Path(working_dir) / "outline.json"))

        docs_site_outline: DocumentationSiteOutline = DocumentationSiteOutline.model_validate_json(
            outline_content,
        )
        return docs_site_outline

    async def step_11_create_all_docs_pages(self) -> None:
        create_docs_page_coroutine_funcs = [
            lambda the_page=page: workflow.execute_child_workflow(
                CreateDocumentationPageWorkflow,
                args=[
                    self.workflow_paths,
                    the_page,
                    self.tech_stack,
                    self.application_summary_result,
                    self.agent_provider,
                ],
                id=f"CreateDocumentationPage-{the_page.path}-{workflow.uuid4()}",
                static_summary=f"CreateDocumentationPage-{the_page.path}"[:200],
                static_details=(
                    f"Title: {the_page.title}\n"
                    f"Path: {the_page.path}\n"
                    f"Sources:\n"
                    + (
                        "\n".join(f"  - {source}" for source in the_page.source_files)
                        if the_page.source_files
                        else "  None"
                    )
                    + "\n"
                    "Links:\n"
                    + (
                        "\n".join(f"  - {link}" for link in the_page.linked_pages)
                        if the_page.linked_pages
                        else "  None"
                    )
                ),
            )
            for section in self.docs_site_outline.sections
            for page in section.pages
        ]
        await awa_workflow.run_with_controlled_concurrency(
            coroutine_funcs=create_docs_page_coroutine_funcs,
            max_concurrency=MAX_CONCURRENT_AGENTS,
        )

    async def step_12_validate_docs_site(self) -> None:
        agent_config = AgentConfiguration(
            provider=self.agent_provider,
            mode="act",
            build_prompt_params=BuildPromptParams(
                template_input={
                    "path": str(Path(self.workflow_paths.agent_prompts) / "validate_documentation.jinja"),
                },
                variables={
                    "tech_stack": self.tech_stack,
                },
            ),
            working_directory=str(Path(self.workflow_paths.output) / "docs-site"),
            initialize=False,
            stream_enabled=True,
        )
        validate_docs_agent_result: TaskResponseModel = await awa_workflow.execute_agent(
            name="ValidateDocsSite",
            agent_config=agent_config,
        )
        if validate_docs_agent_result.status != "completed":
            raise DocumentationValidationError("Failed to validate documentation")

    async def step_13_build_documentation_site(self) -> None:
        mcp_json = json.dumps(
            {
                "command": "npx",
                "args": ["-y", "@upstash/context7-mcp"],
            },
        )
        agent_config = AgentConfiguration(
            provider=self.agent_provider,
            mode="act",
            build_prompt_params=BuildPromptParams(
                template_input={
                    "path": str(Path(self.workflow_paths.agent_prompts) / "build_documentation_site.jinja"),
                },
                variables={},
            ),
            working_directory=str(Path(self.workflow_paths.output) / "docs-site"),
            initialize=False,
            mcp=McpServer(mcp_json=mcp_json),
            stream_enabled=True,
        )
        build_docs_agent_result: TaskResponseModel = await awa_workflow.execute_agent(
            name="BuildDocsSite",
            agent_config=agent_config,
        )
        if build_docs_agent_result.status != "completed":
            raise ApplicationError("Failed to build documentation", non_retryable=True)

    async def step_14_publish_documentation_site(self) -> None:
        """Publish the documentation site using the provided publish command."""
        if not self.workflow_input.publish_command:
            return

        workflow.logger.info(f"Publishing documentation with command: {self.workflow_input.publish_command}")

        output = await awa_activity.run_command(
            command=self.workflow_input.publish_command,
            working_directory=self.workflow_paths.output,
        )
        workflow.logger.info(f"Publish command completed successfully: {output}")
