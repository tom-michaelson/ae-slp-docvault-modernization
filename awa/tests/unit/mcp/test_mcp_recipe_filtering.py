"""Tests for MCP recipe workflow filtering based on configuration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from awa.core.mcp.mcp_server import discover_mcp_workflows
from awa.core.models.api import WorkflowDefinition
from awa.core.utils.workflow_metadata import WorkflowMetadata


@pytest.fixture
def mock_core_workflow() -> WorkflowMetadata:
    """Create a mock core workflow metadata."""
    return WorkflowMetadata(
        name="CoreWorkflow",
        class_name="CoreWorkflow",
        module="awa.core.workflows.core_workflow",
        parameters=[],
        parameter_info=[],
        exposed=True,
        description="Core workflow for testing",
    )


@pytest.fixture
def mock_recipe_workflow() -> WorkflowMetadata:
    """Create a mock recipe workflow metadata."""
    return WorkflowMetadata(
        name="RecipeWorkflow",
        class_name="RecipeWorkflow",
        module="cookbook.recipes.workflows.recipe_workflow",
        parameters=[],
        parameter_info=[],
        exposed=True,
        description="Recipe workflow for testing",
    )


@pytest.fixture
def mock_external_workflow() -> WorkflowDefinition:
    """Create a mock external workflow definition."""
    return WorkflowDefinition(
        name="ExternalWorkflow",
        task_queue="external-queue",
        mcp_exposed=True,
        input_schema={},
    )


class TestMcpRecipeFiltering:
    """Test MCP workflow discovery with recipe filtering."""

    @pytest.mark.asyncio
    async def test_mcp_discovery_without_recipes(
        self,
        mock_core_workflow: WorkflowMetadata,
        mock_recipe_workflow: WorkflowMetadata,
    ) -> None:
        """Test that MCP discovers only core workflows when recipes are disabled."""
        # Create mock config with recipes disabled
        mock_config = MagicMock()
        mock_config.recipes = False

        with (
            patch("awa.core.mcp.mcp_server.ConfigLoader.get_config", return_value=mock_config),
            patch(
                "awa.core.mcp.mcp_server.get_workflow_metadata",
                return_value=[mock_core_workflow, mock_recipe_workflow],
            ),
            patch("awa.core.mcp.mcp_server.get_registry_storage") as mock_storage,
        ):
            # Mock empty external workflows
            mock_storage.return_value.list_active_workers = AsyncMock(return_value=[])

            workflows = await discover_mcp_workflows()

            # Should only have core workflow, not recipe workflow
            assert len(workflows) == 1
            assert workflows[0][0].name == "CoreWorkflow"
            assert "core" in workflows[0][0].module
            assert "recipes" not in workflows[0][0].module

    @pytest.mark.asyncio
    async def test_mcp_discovery_with_recipes(
        self,
        mock_core_workflow: WorkflowMetadata,
        mock_recipe_workflow: WorkflowMetadata,
    ) -> None:
        """Test that MCP discovers both core and recipe workflows when recipes are enabled."""
        # Create mock config with recipes enabled
        mock_config = MagicMock()
        mock_config.recipes = True

        with (
            patch("awa.core.mcp.mcp_server.ConfigLoader.get_config", return_value=mock_config),
            patch(
                "awa.core.mcp.mcp_server.get_workflow_metadata",
                return_value=[mock_core_workflow, mock_recipe_workflow],
            ),
            patch("awa.core.mcp.mcp_server.get_registry_storage") as mock_storage,
        ):
            # Mock empty external workflows
            mock_storage.return_value.list_active_workers = AsyncMock(return_value=[])

            workflows = await discover_mcp_workflows()

            # Should have both core and recipe workflows
            assert len(workflows) == 2
            workflow_names = [w[0].name for w in workflows]
            assert "CoreWorkflow" in workflow_names
            assert "RecipeWorkflow" in workflow_names

    @pytest.mark.asyncio
    async def test_mcp_discovery_external_workflows_not_filtered(
        self,
        mock_external_workflow: WorkflowDefinition,
    ) -> None:
        """Test that external workflows are not filtered by recipe flag."""
        # Create mock config with recipes disabled
        mock_config = MagicMock()
        mock_config.recipes = False

        # Create mock worker with external workflow
        mock_worker = MagicMock()
        mock_worker.worker_name = "external-worker"
        mock_worker.workflows = [mock_external_workflow]

        with (
            patch("awa.core.mcp.mcp_server.ConfigLoader.get_config", return_value=mock_config),
            patch("awa.core.mcp.mcp_server.get_workflow_metadata", return_value=[]),
            patch("awa.core.mcp.mcp_server.get_registry_storage") as mock_storage,
        ):
            # Mock external workflows
            mock_storage.return_value.list_active_workers = AsyncMock(return_value=[mock_worker])

            workflows = await discover_mcp_workflows()

            # Should have external workflow even with recipes disabled
            assert len(workflows) == 1
            assert workflows[0][0].name == "ExternalWorkflow"
            assert workflows[0][0].module == "external.external-worker"

    @pytest.mark.asyncio
    async def test_mcp_discovery_exposed_flag(self, mock_core_workflow: WorkflowMetadata) -> None:
        """Test that only workflows with exposed flag set are discovered."""
        # Create workflow without exposed flag
        non_exposed_workflow = WorkflowMetadata(
            name="NonExposedWorkflow",
            class_name="NonExposedWorkflow",
            module="awa.core.workflows.non_exposed",
            parameters=[],
            parameter_info=[],
            exposed=False,
            description=None,
        )

        # Create mock config
        mock_config = MagicMock()
        mock_config.recipes = True

        with (
            patch("awa.core.mcp.mcp_server.ConfigLoader.get_config", return_value=mock_config),
            patch(
                "awa.core.mcp.mcp_server.get_workflow_metadata",
                return_value=[mock_core_workflow, non_exposed_workflow],
            ),
            patch("awa.core.mcp.mcp_server.get_registry_storage") as mock_storage,
        ):
            # Mock empty external workflows
            mock_storage.return_value.list_active_workers = AsyncMock(return_value=[])

            workflows = await discover_mcp_workflows()

            # Should only have the exposed workflow
            assert len(workflows) == 1
            assert workflows[0][0].name == "CoreWorkflow"
            assert workflows[0][0].exposed is True

    @pytest.mark.asyncio
    async def test_mcp_discovery_mixed_workflows(
        self,
        mock_core_workflow: WorkflowMetadata,
        mock_recipe_workflow: WorkflowMetadata,
    ) -> None:
        """Test MCP discovery with mix of core and recipe workflows when recipes disabled."""
        # Create additional core and recipe workflows
        core_workflow_2 = WorkflowMetadata(
            name="CoreWorkflow2",
            class_name="CoreWorkflow2",
            module="awa.core.workflows.another_core",
            parameters=[],
            parameter_info=[],
            exposed=True,
            description="Another core workflow",
        )

        recipe_workflow_2 = WorkflowMetadata(
            name="RecipeWorkflow2",
            class_name="RecipeWorkflow2",
            module="cookbook.recipes.workflows.another_recipe",
            parameters=[],
            parameter_info=[],
            exposed=True,
            description="Another recipe workflow",
        )

        # Create mock config with recipes disabled
        mock_config = MagicMock()
        mock_config.recipes = False

        workflows_list = [mock_core_workflow, mock_recipe_workflow, core_workflow_2, recipe_workflow_2]

        with (
            patch("awa.core.mcp.mcp_server.ConfigLoader.get_config", return_value=mock_config),
            patch("awa.core.mcp.mcp_server.get_workflow_metadata", return_value=workflows_list),
            patch("awa.core.mcp.mcp_server.get_registry_storage") as mock_storage,
        ):
            # Mock empty external workflows
            mock_storage.return_value.list_active_workers = AsyncMock(return_value=[])

            workflows = await discover_mcp_workflows()

            # Should only have core workflows
            assert len(workflows) == 2
            workflow_names = [w[0].name for w in workflows]
            assert "CoreWorkflow" in workflow_names
            assert "CoreWorkflow2" in workflow_names
            assert "RecipeWorkflow" not in workflow_names
            assert "RecipeWorkflow2" not in workflow_names

    @pytest.mark.asyncio
    async def test_mcp_discovery_error_handling(self) -> None:
        """Test that MCP discovery handles errors gracefully."""
        # Create mock config
        mock_config = MagicMock()
        mock_config.recipes = False

        with (
            patch("awa.core.mcp.mcp_server.ConfigLoader.get_config", return_value=mock_config),
            patch("awa.core.mcp.mcp_server.get_workflow_metadata", side_effect=Exception("Discovery error")),
            patch("awa.core.mcp.mcp_server.get_registry_storage") as mock_storage,
        ):
            # Mock empty external workflows
            mock_storage.return_value.list_active_workers = AsyncMock(return_value=[])

            # Should not raise exception, but return empty list due to error
            workflows = await discover_mcp_workflows()

            # No workflows due to error, but should not crash
            assert len(workflows) == 0
