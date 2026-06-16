"""Sample workflow demonstrating MCP tool usage with HTTP transport."""

from typing import Any

from temporalio import workflow

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed

with workflow.unsafe.imports_passed_through():
    from sdk_dist.python.awa.client import awa_activity

from .models.workflow_input import CalculatorInput


@recipe_exposed("Demonstrates MCP tool usage with HTTP transport")
@workflow.defn(name="sample-mcp-tool-http")
class SampleMCPToolHTTPWorkflow:
    """A workflow that demonstrates using MCP tools with HTTP transport.

    This workflow showcases how to integrate MCP servers with AWA workflows
    using HTTP transport. It connects to a calculator MCP server running
    over HTTP and performs mathematical operations using the server's tools.
    """

    @workflow.run
    async def run(self, workflow_input: CalculatorInput) -> dict[str, Any]:
        """Sample workflow that demonstrates using MCP tools with HTTP transport.

        This is an example workflow that uses the sample calculator MCP tools
        over HTTP transport to demonstrate how to integrate MCP servers with AWA workflows.
        The MCP server must be running as an HTTP server before executing this workflow.

        Args:
            workflow_input: Input containing 'a' and 'b' values

        Returns:
            Dictionary containing the results of add and multiply operations

        """
        # Use Temporal's built-in logger
        workflow.logger.info("Starting SampleMCPToolHTTPWorkflow")
        workflow.logger.info(f"Workflow ID: {workflow.info().workflow_id}")
        workflow.logger.info(f"Task queue: {workflow.info().task_queue}")
        workflow.logger.info(f"Run ID: {workflow.info().run_id}")
        workflow.logger.info(f"Calculator input: a={workflow_input.a}, b={workflow_input.b}")

        try:
            # MCP configuration for an http calculator server (assumes that this is already running)
            mcp_config = {
                "mcpServers": {
                    "calculator": {
                        "url": "http://127.0.0.1:9000/mcp",
                        "transport": "streamable-http",
                    },
                },
            }

            workflow.logger.info("Performing addition operation via HTTP MCP server")
            # Add the numbers
            sum_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="add",
                parameters={"a": workflow_input.a, "b": workflow_input.b},
                timeout_seconds=10,
            )
            workflow.logger.info(f"Addition result: {sum_result}")

            workflow.logger.info("Performing multiplication operation via HTTP MCP server")
            # Multiply the numbers
            product_result = await awa_activity.invoke_mcp_tool(
                mcp_config=mcp_config,
                tool_name="multiply",
                parameters={"a": workflow_input.a, "b": workflow_input.b},
                timeout_seconds=10,
            )
            workflow.logger.info(f"Multiplication result: {product_result}")

            result = {"sum": sum_result, "product": product_result}
            workflow.logger.info("All calculator operations completed successfully")

        except Exception:
            workflow.logger.exception("Error in SampleMCPToolHTTPWorkflow")
            raise
        else:
            return result
        finally:
            workflow.logger.info("SampleMCPToolHTTPWorkflow execution completed")
