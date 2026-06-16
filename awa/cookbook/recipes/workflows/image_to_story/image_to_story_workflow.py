from pathlib import Path
from typing import Any

from temporalio import workflow

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from cookbook.recipes.workflows.image_to_story.models.generated_story import GeneratedStory

with workflow.unsafe.imports_passed_through():
    import json

from sdk_dist.python.awa.client import awa_activity, awa_general, awa_workflow
from sdk_dist.python.awa.client.models import (
    InputParams,
    JiraIssueRequest,
    JiraIssueResponse,
    TransformParams,
    WorkflowPaths,
)

from .models.workflow_input import ImageToStoryWorkflowInput

# Possible future enhancements to this workflow:
# - Retrieve image from Figma using MCP tool
# - Use project context (short descriptions of all files, tech stack, etc.) to enhance quality of story
# - Determine existing source files relevant to the story, use them to quality-check the story


@recipe_exposed("Creates a Jira story based on a screenshot")
@workflow.defn(name="image-to-story")
class ImageToStoryWorkflow:
    mcp_config: dict[str, Any] | None = None
    workflow_paths: WorkflowPaths | None = None
    jira_url: str = "https://slalom.atlassian.net"
    jira_key: str | None = None

    @workflow.run
    async def execute(self, workflow_input: ImageToStoryWorkflowInput | None = None) -> str:
        r"""Create a Jira story based on an image.

        Example command:
        uv run -m awa.main run -w image-to-story
        """
        jira_project_id = (
            workflow_input.jira_project_id if workflow_input and workflow_input.jira_project_id else "TSKSTRM"
        )

        await self._initialize_workflow()
        screenshot_path = await self._step01_get_image_path(workflow_input)
        story = await self._step02_generate_and_save_story(screenshot_path)
        self.jira_key = await self._step03_write_story_to_jira(story, jira_project_id)
        await self._step04_generate_questions_and_add_jira_comment(jira_project_id)
        return f"{self.jira_url}/jira/software/projects/{jira_project_id}/issues/{self.jira_key}"

    async def _initialize_workflow(self) -> None:
        self.workflow_paths = awa_general.get_workflow_paths(Path(__file__).parent, workflow.info())

    async def _step01_get_image_path(self, workflow_input: ImageToStoryWorkflowInput) -> str:
        return (
            str(workflow_input.image_path)
            if workflow_input and workflow_input.image_path
            else str(Path(self.workflow_paths.input) / "login.png")
        )

    async def _step02_generate_and_save_story(self, screenshot_path: str) -> GeneratedStory:
        """Generate story from screenshot and save to output file."""
        transform_params = TransformParams(
            baml_function_name="GenerateStory",
            request={},
            inputs=[
                InputParams(
                    name="screenshot",
                    path=screenshot_path,
                    image_mime_type="image/png",
                ),
            ],
        )
        result: dict[str, Any] = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(self.workflow_paths.baml_src) / "generate_story.baml"),
        )
        story = GeneratedStory(**result)

        await awa_activity.write_file(Path(self.workflow_paths.output) / "story.json", story.model_dump_json(indent=2))

        return story

    async def _step03_write_story_to_jira(self, story: GeneratedStory, jira_project_id: str) -> str:
        """Write the generated story to Jira and save the issue key."""
        jira_key = await awa_activity.upsert_jira_issue(
            JiraIssueRequest(
                summary=story.title,
                description=story.description,
                project_id=jira_project_id,
            ),
        )

        await awa_activity.write_file(Path(self.workflow_paths.output) / "jira_key.txt", jira_key)
        return jira_key

    async def _step04_generate_questions_and_add_jira_comment(self, jira_project_id: str) -> None:
        """Generate questions for the story and add them as a Jira comment."""
        jira_issue: JiraIssueResponse = await awa_activity.read_jira_issue(
            JiraIssueRequest(key=self.jira_key, project_id=jira_project_id),
        )

        summary = jira_issue.summary
        description = jira_issue.description
        transform_params = TransformParams(
            baml_function_name="ReviewStory",
            request={
                "summary": summary,
                "description": description,
            },
        )
        questions_container: dict[str, Any] = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(self.workflow_paths.baml_src) / "review_story.baml"),
        )
        questions = questions_container.get("questions", [])

        await awa_activity.write_file(
            Path(self.workflow_paths.output) / "questions.json",
            json.dumps(questions, indent=2),
        )

        if questions:
            questions_content = "\n- ".join(questions)
            await awa_activity.add_jira_comment(
                JiraIssueRequest(
                    key=self.jira_key,
                    project_id=jira_project_id,
                    comments=[f"Questions for review:\n- {questions_content}"],
                ),
            )
