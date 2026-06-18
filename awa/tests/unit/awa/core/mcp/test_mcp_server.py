from unittest.mock import AsyncMock, patch

import pytest

from awa.core.mcp.mcp_server import create_mcp_app, discover_mcp_workflows, health
from awa.core.utils.workflow_metadata import WorkflowMetadata


def test_health() -> None:
    """Test the health function directly."""
    assert health() == "OK"


@pytest.mark.asyncio
async def test_create_mcp_app() -> None:
    """Test that the create_mcp_app function returns a FastMCP instance with registered tools."""
    from fastmcp import FastMCP

    mcp_app = create_mcp_app()
    assert isinstance(mcp_app, FastMCP)
    assert mcp_app.name == "AWA MCP"

    # Check that core tools are registered
    tools = await mcp_app.get_tools()
    assert "health" in tools
    assert "start_workflow" in tools
    assert "get_workflow_result" in tools
    assert "list_workflows" in tools
    assert "list_available_workflows" in tools


class TestMcpWorkflowFunctionality:
    """Test MCP workflow discovery and execution."""

    @pytest.mark.asyncio
    async def test_discover_mcp_workflows_core_only(self) -> None:
        """Test discovering core workflows with MCP decorator."""
        # Mock workflow metadata with MCP exposure
        mock_metadata = WorkflowMetadata(
            name="awa-test-workflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=[],
            parameter_info=[],
            exposed=True,
            description="Test workflow",
        )

        with (
            patch("awa.core.mcp.mcp_server.get_workflow_metadata", return_value=[mock_metadata]),
            patch("awa.core.mcp.mcp_server.get_registry_storage") as mock_storage,
        ):
            # Mock empty external workflows
            mock_storage.return_value.list_active_workers = AsyncMock(return_value=[])

            workflows = await discover_mcp_workflows()

            assert len(workflows) == 1
            assert workflows[0][0].name == "awa-test-workflow"
            assert workflows[0][1] is None  # No external definition
