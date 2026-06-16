"""Unit tests for TemporalWorker recipe functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from temporalio import activity, workflow

from awa.core.engine.temporal_client import TemporalClient
from awa.core.engine.temporal_worker import TemporalWorker


# Test recipe workflow for testing
@workflow.defn(name="test-recipe-workflow")
class TestRecipeWorkflow:
    @workflow.run
    async def run(self, param: str) -> str:
        return f"Recipe: {param}"


# Test recipe activity for testing
@activity.defn(name="test-recipe-activity")
async def sample_recipe_activity(param: str) -> str:
    return f"Recipe Activity: {param}"


# Test core workflow for testing
@workflow.defn(name="test-core-workflow")
class TestCoreWorkflow:
    @workflow.run
    async def run(self, param: str) -> str:
        return f"Core: {param}"


# Test core activity for testing
@activity.defn(name="test-core-activity")
async def sample_core_activity(param: str) -> str:
    return f"Core Activity: {param}"


@pytest.mark.asyncio
@patch("awa.core.engine.temporal_client.TemporalClient.create")
class TestTemporalWorkerRecipes:
    """Test suite for worker recipe functionality."""

    async def test_construct_worker_with_recipes_disabled(self, mock_create: AsyncMock) -> None:
        """Test that worker construction respects recipes=False configuration."""
        # Arrange
        mock_temporal_client = AsyncMock()
        mock_internal_client = Mock()
        mock_internal_client.config.return_value = {"plugins": [], "interceptors": []}
        mock_temporal_client.get_client.return_value = mock_internal_client
        mock_create.return_value = mock_temporal_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Mock config with recipes disabled
        mock_config = Mock()
        mock_config.recipes = False

        # Only return core workflows/activities (no recipes)
        mock_workflows = [TestCoreWorkflow]
        mock_activities = [sample_core_activity]

        with (
            patch("awa.core.engine.temporal_worker.ConfigLoader") as mock_config_loader_class,
            patch("awa.core.engine.temporal_worker.TemporalDiscovery") as mock_discovery_class,
            patch("awa.core.engine.temporal_worker.Worker") as mock_worker_class,
            patch.object(worker, "logger") as mock_logger,
        ):
            # Setup ConfigLoader mock
            mock_config_loader_class.get_config.return_value = mock_config

            # Setup TemporalDiscovery mock
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            mock_discovery.discover_workflows_and_activities.return_value = (mock_workflows, mock_activities)

            # Mock the Worker class
            mock_worker_instance = Mock()
            mock_worker_class.return_value = mock_worker_instance

            # Act
            await worker._construct_temporal_worker()

            # Assert - Verify TemporalDiscovery was created with include_recipes=False
            mock_discovery_class.assert_called_once_with(include_recipes=False)

            # Verify logger logged recipe status
            logged_calls = mock_logger.info.call_args_list
            recipe_status_log = None
            for call in logged_calls:
                call_message = str(call[0][0])
                if "Recipe workflows DISABLED in configuration" in call_message:
                    recipe_status_log = call
                    break

            assert recipe_status_log is not None, "Recipe disabled log message not found"

    async def test_construct_worker_with_recipes_enabled(self, mock_create: AsyncMock) -> None:
        """Test that worker construction respects recipes=True configuration."""
        # Arrange
        mock_temporal_client = AsyncMock()
        mock_internal_client = Mock()
        mock_internal_client.config.return_value = {"plugins": [], "interceptors": []}
        mock_temporal_client.get_client.return_value = mock_internal_client
        mock_create.return_value = mock_temporal_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Mock config with recipes enabled
        mock_config = Mock()
        mock_config.recipes = True

        # Modify workflow classes to have proper module names for detection
        TestRecipeWorkflow.__module__ = "recipes.workflows.test_workflow"
        TestCoreWorkflow.__module__ = "awa.core.workflows.test_workflow"

        # Return both core and recipe workflows/activities
        mock_workflows = [TestCoreWorkflow, TestRecipeWorkflow]
        mock_activities = [sample_core_activity, sample_recipe_activity]

        with (
            patch("awa.core.engine.temporal_worker.ConfigLoader") as mock_config_loader_class,
            patch("awa.core.engine.temporal_worker.TemporalDiscovery") as mock_discovery_class,
            patch("awa.core.engine.temporal_worker.Worker") as mock_worker_class,
            patch.object(worker, "logger") as mock_logger,
        ):
            # Setup ConfigLoader mock
            mock_config_loader_class.get_config.return_value = mock_config

            # Setup TemporalDiscovery mock
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            mock_discovery.discover_workflows_and_activities.return_value = (mock_workflows, mock_activities)

            # Mock the Worker class
            mock_worker_instance = Mock()
            mock_worker_class.return_value = mock_worker_instance

            # Act
            await worker._construct_temporal_worker()

            # Assert - Verify TemporalDiscovery was created with include_recipes=True
            mock_discovery_class.assert_called_once_with(include_recipes=True)

            # Verify logger logged recipe status
            logged_calls = mock_logger.info.call_args_list
            recipe_status_log = None
            for call in logged_calls:
                call_message = str(call[0][0])
                if "Recipe workflows ENABLED in configuration" in call_message:
                    recipe_status_log = call
                    break

            assert recipe_status_log is not None, "Recipe enabled log message not found"

    async def test_worker_categorizes_workflows_correctly(self, mock_create: AsyncMock) -> None:
        """Test that worker correctly categorizes core vs recipe workflows in logging."""
        # Arrange
        mock_temporal_client = AsyncMock()
        mock_internal_client = Mock()
        mock_internal_client.config.return_value = {"plugins": [], "interceptors": []}
        mock_temporal_client.get_client.return_value = mock_internal_client
        mock_create.return_value = mock_temporal_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Mock config with recipes enabled
        mock_config = Mock()
        mock_config.recipes = True

        # Set up module names to distinguish core from recipe
        TestRecipeWorkflow.__module__ = "recipes.workflows.test_workflow"
        TestCoreWorkflow.__module__ = "awa.core.workflows.test_workflow"

        # Set up module names for activities
        sample_recipe_activity.__module__ = "recipes.activities.test_activity"
        sample_core_activity.__module__ = "awa.core.activities.test_activity"

        # Return both core and recipe workflows/activities
        mock_workflows = [TestCoreWorkflow, TestRecipeWorkflow]
        mock_activities = [sample_core_activity, sample_recipe_activity]

        with (
            patch("awa.core.engine.temporal_worker.ConfigLoader") as mock_config_loader_class,
            patch("awa.core.engine.temporal_worker.TemporalDiscovery") as mock_discovery_class,
            patch("awa.core.engine.temporal_worker.Worker") as mock_worker_class,
            patch.object(worker, "logger") as mock_logger,
        ):
            # Setup ConfigLoader mock
            mock_config_loader_class.get_config.return_value = mock_config

            # Setup TemporalDiscovery mock
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            mock_discovery.discover_workflows_and_activities.return_value = (mock_workflows, mock_activities)

            # Mock the Worker class
            mock_worker_instance = Mock()
            mock_worker_class.return_value = mock_worker_instance

            # Act
            await worker._construct_temporal_worker()

            # Assert - Check that logger logged the categorization
            logged_calls = mock_logger.info.call_args_list

            # Find log about core/recipe workflow counts
            workflow_count_log = None
            for call in logged_calls:
                call_message = str(call[0][0])
                if "core workflow(s)" in call_message and "recipe workflow(s)" in call_message:
                    workflow_count_log = call_message
                    break

            assert workflow_count_log is not None, "Workflow categorization log not found"

            # Verify counts in the log (should be 1 core and 1 recipe)
            assert "1 core workflow(s)" in workflow_count_log
            assert "1 recipe workflow(s)" in workflow_count_log

    async def test_get_workflow_name_method(self, mock_create: AsyncMock) -> None:
        """Test the _get_workflow_name helper method."""
        # Arrange
        mock_temporal_client = AsyncMock()
        mock_create.return_value = mock_temporal_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Act
        workflow_name = worker._get_workflow_name(TestRecipeWorkflow)

        # Assert
        assert workflow_name == "test-recipe-workflow"

    async def test_get_activity_name_method(self, mock_create: AsyncMock) -> None:
        """Test the _get_activity_name helper method."""
        # Arrange
        mock_temporal_client = AsyncMock()
        mock_create.return_value = mock_temporal_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Act
        activity_name = worker._get_activity_name(sample_recipe_activity)

        # Assert
        assert activity_name == "test-recipe-activity"

    async def test_worker_handles_mixed_workflows(self, mock_create: AsyncMock) -> None:
        """Test that worker correctly handles both core and recipe workflows together."""
        # Arrange
        mock_temporal_client = AsyncMock()
        mock_internal_client = Mock()
        mock_internal_client.config.return_value = {"plugins": [], "interceptors": []}
        mock_temporal_client.get_client.return_value = mock_internal_client
        mock_create.return_value = mock_temporal_client
        client = await TemporalClient.create()
        worker = TemporalWorker(client)

        # Mock config with recipes enabled
        mock_config = Mock()
        mock_config.recipes = True

        # Set up module names
        TestRecipeWorkflow.__module__ = "recipes.workflows.test_workflow"
        TestCoreWorkflow.__module__ = "awa.core.workflows.test_workflow"

        # Return both core and recipe workflows
        mock_workflows = [TestCoreWorkflow, TestRecipeWorkflow]
        mock_activities: list[object] = []

        with (
            patch("awa.core.engine.temporal_worker.ConfigLoader") as mock_config_loader_class,
            patch("awa.core.engine.temporal_worker.TemporalDiscovery") as mock_discovery_class,
            patch("awa.core.engine.temporal_worker.Worker") as mock_worker_class,
        ):
            # Setup ConfigLoader mock
            mock_config_loader_class.get_config.return_value = mock_config

            # Setup TemporalDiscovery mock
            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery
            mock_discovery.discover_workflows_and_activities.return_value = (mock_workflows, mock_activities)

            # Mock the Worker class
            mock_worker_instance = Mock()
            mock_worker_class.return_value = mock_worker_instance

            # Act
            await worker._construct_temporal_worker()

            # Assert - Verify Worker was instantiated with both workflow types
            mock_worker_class.assert_called_once()
            call_kwargs = mock_worker_class.call_args[1]
            assert call_kwargs["workflows"] == mock_workflows
            assert len(call_kwargs["workflows"]) == 2
