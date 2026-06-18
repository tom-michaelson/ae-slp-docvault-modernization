"""Sample workflow demonstrating NPX-based MCP server usage with stdio transport."""

from typing import Any

from temporalio import workflow

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed

with workflow.unsafe.imports_passed_through():
    from sdk_dist.python.awa.client import awa_activity

from .models.workflow_input import NPXStdioFilesystemInput


@recipe_exposed("Demonstrates NPX-based MCP server usage")
@workflow.defn(name="sample-mcp-tool-npx-stdio")
class SampleMCPToolNPXStdioWorkflow:
    """A workflow that demonstrates using NPX-based MCP servers with stdio transport.

    This workflow showcases how to integrate NPX-based MCP servers with AWA
    workflows using stdio transport. It automatically starts a filesystem MCP
    server as a subprocess using NPX and performs various filesystem operations.
    """

    @workflow.run
    async def run(self, workflow_input: NPXStdioFilesystemInput | None = None) -> dict[str, Any]:
        """Sample workflow that demonstrates using NPX MCP servers with stdio transport.

        This is an example workflow that uses the filesystem MCP server
        over stdio transport to demonstrate how to integrate NPX-based MCP servers with AWA workflows.
        The MCP server will be started automatically as a subprocess using stdio transport.

        Args:
            workflow_input: Input containing the directory path to explore (defaults to current directory)

        Returns:
            Dictionary containing the results of filesystem operations

        """
        if workflow_input is None:
            workflow_input = NPXStdioFilesystemInput()

        # Use Temporal's built-in logger
        workflow.logger.info("Starting SampleMCPToolNPXStdioWorkflow")
        workflow.logger.info(f"Workflow ID: {workflow.info().workflow_id}")
        workflow.logger.info(f"Task queue: {workflow.info().task_queue}")
        workflow.logger.info(f"Run ID: {workflow.info().run_id}")
        workflow.logger.info(f"Directory to explore: {workflow_input.directory_path}")

        try:
            # MCP configuration for a local NPX filesystem server
            # This will automatically start the NPX server as a subprocess
            mcp_config = {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": [
                            "-y",
                            "@modelcontextprotocol/server-filesystem",
                            ".",  # path that the server is allowed to explore
                        ],
                        "transport": "stdio",
                        "env": {"EXAMPLE_ENV_VAR": "example_value"},
                    },
                },
            }

            workflow.logger.info(f"Listing files in directory: {workflow_input.directory_path}")
            # List files in the specified directory
            list_directory_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="list_directory",
                parameters={"path": workflow_input.directory_path},
                timeout_seconds=30,
            )

            workflow.logger.info("Reading README.md file")
            # Read a sample file (if it exists)
            read_file_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="read_file",
                parameters={"path": "README.md"},
                timeout_seconds=30,
            )
            workflow.logger.info("README.md file read successfully")

            workflow.logger.info("Getting file info for README.md")
            # Get file info for README.md
            file_info_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="get_file_info",
                parameters={"path": "README.md"},
                timeout_seconds=30,
            )
            workflow.logger.info("File info retrieved successfully")

            result = {
                "list_directory": list_directory_result,
                "read_file": read_file_result,
                "file_info": file_info_result,
                "explored_directory": workflow_input.directory_path,
            }

            workflow.logger.info("All filesystem operations completed successfully")

        except Exception:
            workflow.logger.exception("Error in SampleMCPToolNPXStdioWorkflow")
            raise
        else:
            return result
        finally:
            workflow.logger.info("SampleMCPToolNPXStdioWorkflow execution completed")
