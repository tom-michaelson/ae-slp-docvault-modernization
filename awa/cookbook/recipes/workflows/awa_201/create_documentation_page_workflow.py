from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.awa_201.models.documentation_site_outline import DocumentationPage
from sdk_dist.python.awa.client import awa_activity, awa_workflow
from sdk_dist.python.awa.client.models import (
    AgentConfiguration,
    BuildPromptParams,
    TaskResponseModel,
    TransformParams,
    WorkflowPaths,
)


class DocumentationPageEditError(Exception):
    """Raised when editing a documentation page fails."""


@workflow.defn(name="create-documentation-page")
class CreateDocumentationPageWorkflow:
    @workflow.run
    async def run(
        self,
        workflow_paths: WorkflowPaths,
        page: DocumentationPage,
        tech_stack: str,
        application_summary: str,
        agent_provider: str,
    ) -> None:
        linked_documentation_pages = page.linked_pages
        relevant_source_file_descriptions: dict[str, str] = {}
        # TODO RH: Parallelize this loop
        for source_file in page.source_files:
            source_file_path = str(Path(workflow_paths.output) / "docs-site" / "source" / source_file.lstrip("/"))
            source_file_description = await awa_activity.read_file(source_file_path, "[FILE NOT FOUND]")
            relevant_source_file_descriptions[source_file] = source_file_description

        page_path = str(Path(workflow_paths.output) / "docs-site" / "docs" / page.path.lstrip("/"))
        transform_params = TransformParams(
            baml_function_name="CreateDocsPage",
            request={
                "tech_stack": tech_stack,
                "title": page.title,
                "summary": page.summary,
                "linked_documentation_pages": linked_documentation_pages,
                "relevant_source_file_descriptions": relevant_source_file_descriptions,
            },
            output_path=page_path,
        )
        await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(workflow_paths.baml_src) / "create_docs_page.baml"),
        )

        # We do NOT want to parallelize these edits, as each will iteratively edit the same page
        for source_file in page.source_files:
            # TODO RH: Use diff edit flow for these, instead of another agent
            # diff_prompt = await WorkflowUtils.build_prompt(
            #     template_input={},
            #     variables={
            #         "application_summary": application_summary,
            #         "tech_stack": tech_stack,
            #         "relevant_source_file_name": source_file,
            #         "relevant_source_file_content": relevant_source_file_descriptions[source_file],
            #     },
            # )
            # await WorkflowUtils.apply_single_file_diff(page_path, diff_prompt)

            agent_config = AgentConfiguration(
                provider=agent_provider,
                mode="act",
                build_prompt_params=BuildPromptParams(
                    template_input={
                        "path": str(Path(workflow_paths.agent_prompts) / "edit_docs_page.jinja"),
                    },
                    variables={
                        "documentation_page_path": page_path,
                        "application_summary": application_summary,
                        "tech_stack": tech_stack,
                        "relevant_source_file_name": source_file,
                        "relevant_source_file_content": relevant_source_file_descriptions[source_file],
                    },
                ),
                working_directory=str(Path(workflow_paths.output) / "docs-site"),
                initialize=False,
                stream_enabled=True,
            )
            success = False
            while not success:
                edit_docs_page_agent_result: TaskResponseModel = await awa_workflow.execute_agent(
                    name="EditDocsPage",
                    agent_config=agent_config,
                )
                success = edit_docs_page_agent_result.status == "completed"
                if not success:
                    workflow.logger.warning(
                        f"Failed to edit docs page (retrying): {edit_docs_page_agent_result.model_dump_json(indent=2)}",
                    )
