from __future__ import annotations

from datetime import timedelta
from typing import LiteralString

from pydantic import BaseModel
from temporalio import workflow

from awa.sdk import constants as sdk_constants

with workflow.unsafe.imports_passed_through():
    from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration, McpServer, McpTool
    from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
    from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum
    from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel


class FigmaWorkflowParams(BaseModel):
    """Parameters for the FigmaWorkflow."""

    output_path: str


@workflow.defn(name=sdk_constants.WORKFLOW_CREATE_PROTOTYPE_FROM_FIGMA)
class CreatePrototypeFromFigmaWorkflow:
    """Workflow for interacting with Figma."""

    @workflow.run
    async def run(self, params: FigmaWorkflowParams) -> None:
        """Execute a Figma-related task using an agent."""
        task_prompt: LiteralString = """
                        Make a prototype set of working html pages. There are the figma nodes.
            Create the pages, I want working links from the pages. We can simulate register, login,
            and any other functionality,
            to create this clickaable prototype.

            fileKey: VfA2sCerXY9c1r4V6bumnp
            name: To-do List Web App Design (Community)
            pages:
              - id: "16:34"
                name: "Main Design"
                type: "CANVAS"
                children:
                  - id: "351:775"
                    name: "Thumbnail"
                    type: "FRAME"
                  - id: "16:35"
                    name: "Dashboard"
                    type: "FRAME"
                  - id: "442:891"
                    name: "Dashboard"
                    type: "FRAME"
                  - id: "449:1440"
                    name: "Register"
                    type: "FRAME"
                  - id: "449:1406"
                    name: "Login"
                    type: "FRAME"
                  - id: "398:376"
                    name: "My Task"
                    type: "FRAME"
                  - id: "351:284"
                    name: "Vitals"
                    type: "FRAME"
                  - id: "464:1256"
                    name: "Change Password"
                    type: "FRAME"
                  - id: "371:365"
                    name: "Account Info"
                    type: "FRAME"
                  - id: "464:1361"
                    name: "Account Info"
                    type: "FRAME"
                  - id: "399:637"
                    name: "Task Categories"
                    type: "FRAME"
                  - id: "414:953"
                    name: "Add Task Priority"
                    type: "FRAME"
                  - id: "429:867"
                    name: "Edit Task Priority"
                    type: "FRAME"
                  - id: "324:2449"
                    name: "Add task"
                    type: "FRAME"
                  - id: "398:516"
                    name: "Create Categories"
                    type: "FRAME"
                  - id: "324:3155"
                    name: "View Task"
                    type: "FRAME"
                  - id: "429:705"
                    name: "Edit Task Status"
                    type: "FRAME"


              Use material ui to help make the layout. You should be able to use your get_figma_data tool
              from figma mcp server
              As you have limited context window, utilize your knowledge graph tool to help
              you remember information.
              When using the figma tool you should use the depth parameter (depth=2) to help you reduce
              the amount of data you are pulling in.
              Then process the data and store it in your knowledge graph to save space in your working context.
              If you can not use the figma tool then exit.
        """

        mcp_json_content = await workflow.execute_activity(
            sdk_constants.ACTIVITY_READ_FILE,
            args=[".mcp.json"],
            start_to_close_timeout=timedelta(minutes=1),
        )

        figma_allowed_tools = [
            "get_data",
            "download_images",
        ]

        memory_allowed_tools = [
            "create_entities",
            "create_relations",
            "add_observations",
            "delete_entities",
            "delete_observations",
        ]

        agent_config = AgentConfiguration(
            provider=AgentProviderEnum.CLAUDE,
            mode=AgentModeEnum.ANALYZE,
            prompt=task_prompt,
            working_directory=params.output_path,
            initialize=False,
            mcp=McpServer(
                mcp_json=mcp_json_content,
                allowed=[
                    McpTool(server="figma", tools=figma_allowed_tools),
                    McpTool(server="memory", tools=memory_allowed_tools),
                ],
            ),
        )

        task_response_dict = await workflow.execute_activity(
            sdk_constants.ACTIVITY_EXECUTE_AGENT,
            args=[agent_config],
            start_to_close_timeout=timedelta(minutes=30),
        )

        # Convert the dictionary response to a TaskResponseModel
        task_response = TaskResponseModel(**task_response_dict)

        if not (task_response.status == "completed" and task_response.output):
            workflow.logger.error(
                f"Figma task failed: {task_response.reason}",
            )
            return

        # Workflow completed successfully
        workflow.logger.info("Figma task completed successfully")
        return
