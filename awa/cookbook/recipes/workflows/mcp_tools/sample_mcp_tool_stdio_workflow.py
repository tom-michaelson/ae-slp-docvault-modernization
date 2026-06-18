"""Sample workflow demonstrating MCP tool usage with stdio transport."""

from typing import Any

from temporalio import workflow

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed

with workflow.unsafe.imports_passed_through():
    from sdk_dist.python.awa.client import awa_activity

# Path to cookbook recipes directory (relative from main AWA repo)
COOKBOOK_RECIPES_PATH = "../agentic-workflow-accelerator-cookbook/recipes"


@recipe_exposed("Demonstrates MCP tool usage with stdio transport")
@workflow.defn(name="sample-mcp-tool-stdio")
class SampleMCPToolStdioWorkflow:
    """A workflow that demonstrates using MCP tools with stdio transport.

    This workflow showcases how to use MCP tools within a Temporal workflow
    using stdio transport. It starts an MCP server as a subprocess via stdio
    transport, performs calculator operations, and ensures proper cleanup.
    """

    @workflow.run
    async def run(self, workflow_input: dict[str, Any]) -> dict[str, Any]:
        """Sample workflow that demonstrates using MCP tools with stdio transport.

        This workflow showcases how to use MCP (Model Context Protocol) tools
        within a Temporal workflow. It starts an MCP server via stdio transport,
        performs operations, and ensures proper cleanup.

        Args:
            workflow_input: Input parameters for the workflow

        Returns:
            Dict containing the results of the MCP tool operations

        """
        # Use Temporal's built-in logger
        workflow.logger.info("Starting SampleMCPToolStdioWorkflow")
        workflow.logger.info(f"Workflow ID: {workflow.info().workflow_id}")
        workflow.logger.info(f"Task queue: {workflow.info().task_queue}")
        workflow.logger.info(f"Run ID: {workflow.info().run_id}")
        workflow.logger.info(f"Workflow input: {workflow_input}")

        try:
            # MCP configuration for stdio transport
            # Note: This assumes cookbook repo is a sibling directory to main AWA repo
            mcp_config = {
                "mcpServers": {
                    "calculator": {
                        "command": "uv",
                        "args": [
                            "run",
                            "--directory",
                            COOKBOOK_RECIPES_PATH,
                            "-m",
                            "mcp_servers.sample_calculator_server",
                            "--transport",
                            "stdio",
                        ],
                        "transport": "stdio",
                        "env": {"EXAMPLE_ENV_VAR": "example_value"},
                    },
                },
            }

            workflow.logger.info("Performing addition operation via stdio MCP server")
            # Add the numbers
            sum_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="add",
                parameters=workflow_input,
                timeout_seconds=30,
            )
            workflow.logger.info(f"Addition result: {sum_result}")

            workflow.logger.info("Performing multiplication operation via stdio MCP server")
            # Multiply the numbers
            product_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="multiply",
                parameters=workflow_input,
                timeout_seconds=30,
            )
            workflow.logger.info(f"Multiplication result: {product_result}")

            result = {"sum": sum_result, "product": product_result}
            workflow.logger.info("All calculator operations completed successfully")

        except Exception:
            workflow.logger.exception("Error in SampleMCPToolStdioWorkflow")
            raise
        else:
            return result
        finally:
            workflow.logger.info("SampleMCPToolStdioWorkflow execution completed")
