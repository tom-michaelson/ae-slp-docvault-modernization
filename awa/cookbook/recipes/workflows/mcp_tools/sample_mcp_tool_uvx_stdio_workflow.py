"""Sample workflow demonstrating UVX-based MCP server usage with stdio transport."""

from typing import Any

from temporalio import workflow

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed

with workflow.unsafe.imports_passed_through():
    from sdk_dist.python.awa.client import awa_activity

from .models.workflow_input import UVXStdioTimeInput


@recipe_exposed("Demonstrates UVX-based MCP server usage")
@workflow.defn(name="sample-mcp-tool-uvx-stdio")
class SampleMCPToolUVXStdioWorkflow:
    """A workflow that demonstrates using UVX-based MCP servers with stdio transport.

    This workflow showcases how to integrate UVX-based MCP servers with AWA
    workflows using stdio transport. It automatically starts a time MCP server
    as a subprocess using UVX and performs various time-related operations.
    """

    @workflow.run
    async def run(self, workflow_input: UVXStdioTimeInput) -> dict[str, Any]:
        """Sample workflow that demonstrates using UVX MCP servers with stdio transport.

        This is an example workflow that uses the time MCP server over stdio transport
        to demonstrate how to integrate UVX-based MCP servers with AWA workflows.
        The MCP server will be started automatically as a subprocess using stdio transport.

        Args:
            workflow_input: Input containing timezone and time information for conversion

        Returns:
            Dictionary containing the results of time operations

        """
        # Use Temporal's built-in logger
        workflow.logger.info("Starting SampleMCPToolUVXStdioWorkflow")
        workflow.logger.info(f"Workflow ID: {workflow.info().workflow_id}")
        workflow.logger.info(f"Task queue: {workflow.info().task_queue}")
        workflow.logger.info(f"Run ID: {workflow.info().run_id}")
        workflow.logger.info(
            f"Source timezone: {workflow_input.source_timezone}, Target timezone: {workflow_input.target_timezone}",
        )
        workflow.logger.info(f"Time to convert: {workflow_input.time}")

        try:
            # MCP configuration for a local UVX time server
            # This will automatically start the UVX server as a subprocess
            mcp_config = {
                "mcpServers": {
                    "time": {
                        "command": "uvx",
                        "args": [
                            "mcp-server-time",
                            "--local-timezone=America/Los_Angeles",
                        ],
                        "transport": "stdio",
                        "env": {"EXAMPLE_ENV_VAR": "example_value"},
                    },
                },
            }

            workflow.logger.info("Getting current time in source timezone")
            # Get current time in the source timezone
            current_time_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="get_current_time",
                parameters={"timezone": workflow_input.source_timezone},
                timeout_seconds=30,
            )
            workflow.logger.info(f"Current time in {workflow_input.source_timezone}: {current_time_result}")

            workflow.logger.info("Converting time between timezones")
            # Convert time between timezones
            convert_time_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="convert_time",
                parameters={
                    "source_timezone": workflow_input.source_timezone,
                    "time": workflow_input.time,
                    "target_timezone": workflow_input.target_timezone,
                },
                timeout_seconds=30,
            )
            workflow.logger.info(f"Time conversion result: {convert_time_result}")

            workflow.logger.info("Getting current time in target timezone")
            # Get current time in the target timezone
            target_current_time_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="get_current_time",
                parameters={"timezone": workflow_input.target_timezone},
                timeout_seconds=30,
            )
            workflow.logger.info(f"Current time in {workflow_input.target_timezone}: {target_current_time_result}")

            result = {
                "source_current_time": current_time_result,
                "time_conversion": convert_time_result,
                "target_current_time": target_current_time_result,
                "source_timezone": workflow_input.source_timezone,
                "target_timezone": workflow_input.target_timezone,
                "converted_time": workflow_input.time,
            }

            workflow.logger.info("All time operations completed successfully")

        except Exception:
            workflow.logger.exception("Error in SampleMCPToolUVXStdioWorkflow")
            raise
        else:
            return result
        finally:
            workflow.logger.info("SampleMCPToolUVXStdioWorkflow execution completed")
