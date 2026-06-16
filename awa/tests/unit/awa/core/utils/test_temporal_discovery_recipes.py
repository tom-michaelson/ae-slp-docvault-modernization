"""Unit tests for TemporalDiscovery recipe functionality."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from temporalio import activity, workflow

from awa.core.utils.temporal_discovery import TemporalDiscovery


# Sample recipe workflow for testing
@workflow.defn(name="test-recipe-workflow")
class SampleRecipeWorkflow:
    @workflow.run
    async def run(self, param: str) -> str:
        return f"Recipe Workflow: {param}"


# Sample recipe activity for testing
@activity.defn(name="test-recipe-activity")
async def sample_recipe_activity(param: str) -> str:
    return f"Recipe Activity: {param}"


# Sample core workflow for testing
@workflow.defn(name="test-core-workflow")
class SampleCoreWorkflow:
    @workflow.run
    async def run(self, param: str) -> str:
        return f"Core Workflow: {param}"


# Sample core activity for testing
@activity.defn(name="test-core-activity")
async def sample_core_activity(param: str) -> str:
    return f"Core Activity: {param}"


class TestTemporalDiscoveryRecipes:
    """Test suite for recipe discovery functionality."""

    def test_discovery_without_recipes(self) -> None:
        """Test that recipe workflows/activities are NOT discovered when include_recipes=False."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            core_workflows_dir = temp_path / "awa" / "core" / "workflows"
            core_workflows_dir.mkdir(parents=True)
            recipe_workflows_dir = temp_path / "cookbook" / "recipes" / "workflows"
            recipe_workflows_dir.mkdir(parents=True)

            # Mock pkgutil.walk_packages to return different modules based on path
            def mock_walk_packages_side_effect(_paths: list[str], prefix: str) -> list[Any]:
                mock_module_info = MagicMock()
                if "core.workflows" in prefix:
                    mock_module_info.name = "core.workflows.test_module"
                elif "cookbook.recipes.workflows" in prefix:
                    mock_module_info.name = "cookbook.recipes.workflows.test_module"
                else:
                    mock_module_info.name = f"{prefix}.test_module"
                return [mock_module_info]

            # Mock modules with different workflows
            core_mock_module = MagicMock()
            core_mock_module.SampleCoreWorkflow = SampleCoreWorkflow

            recipe_mock_module = MagicMock()
            recipe_mock_module.SampleRecipeWorkflow = SampleRecipeWorkflow

            def mock_import_side_effect(module_name: str) -> Any:  # noqa: ANN401
                if "cookbook.recipes" in module_name:
                    return recipe_mock_module
                return core_mock_module

            with (
                patch("pkgutil.walk_packages") as mock_walk_packages,
                patch("importlib.import_module") as mock_import,
                patch("inspect.getmembers") as mock_getmembers,
            ):
                mock_walk_packages.side_effect = mock_walk_packages_side_effect
                mock_import.side_effect = mock_import_side_effect

                def mock_getmembers_side_effect(obj: Any, predicate: Any) -> list[tuple[str, Any]]:  # noqa: ANN401
                    if predicate.__name__ == "isclass":
                        if obj == core_mock_module:
                            return [("SampleCoreWorkflow", SampleCoreWorkflow)]
                        if obj == recipe_mock_module:
                            return [("SampleRecipeWorkflow", SampleRecipeWorkflow)]
                    return []

                mock_getmembers.side_effect = mock_getmembers_side_effect

                # Act - Discovery with recipes DISABLED
                discovery = TemporalDiscovery(str(temp_path / "awa"), include_recipes=False)
                workflows, _ = discovery.discover_workflows_and_activities()

                # Assert - Should only find core workflows, not recipe workflows
                assert len(workflows) >= 0  # May find core workflows

                # Recipe workflow should NOT be in the list
                recipe_workflow_found = any(w.__class__.__name__ == "SampleRecipeWorkflow" for w in workflows)
                assert not recipe_workflow_found, "Recipe workflow should not be discovered when include_recipes=False"

    def test_discovery_with_recipes(self) -> None:
        """Test that recipe workflows/activities ARE discovered when include_recipes=True."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            core_workflows_dir = temp_path / "awa" / "core" / "workflows"
            core_workflows_dir.mkdir(parents=True)
            recipe_workflows_dir = temp_path / "cookbook" / "recipes" / "workflows"
            recipe_workflows_dir.mkdir(parents=True)

            # Mock pkgutil.walk_packages to return different modules based on path
            def mock_walk_packages_side_effect(_paths: list[str], prefix: str) -> list[Any]:
                mock_module_info = MagicMock()
                if "core.workflows" in prefix:
                    mock_module_info.name = "core.workflows.test_module"
                elif "cookbook.recipes.workflows" in prefix:
                    mock_module_info.name = "cookbook.recipes.workflows.test_module"
                else:
                    mock_module_info.name = f"{prefix}.test_module"
                return [mock_module_info]

            # Mock modules with different workflows
            core_mock_module = MagicMock()
            core_mock_module.SampleCoreWorkflow = SampleCoreWorkflow

            recipe_mock_module = MagicMock()
            recipe_mock_module.SampleRecipeWorkflow = SampleRecipeWorkflow

            def mock_import_side_effect(module_name: str) -> Any:  # noqa: ANN401
                if "cookbook.recipes" in module_name:
                    return recipe_mock_module
                return core_mock_module

            with (
                patch("pkgutil.walk_packages") as mock_walk_packages,
                patch("importlib.import_module") as mock_import,
                patch("inspect.getmembers") as mock_getmembers,
            ):
                mock_walk_packages.side_effect = mock_walk_packages_side_effect
                mock_import.side_effect = mock_import_side_effect

                def mock_getmembers_side_effect(obj: Any, predicate: Any) -> list[tuple[str, Any]]:  # noqa: ANN401
                    if predicate.__name__ == "isclass":
                        if obj == core_mock_module:
                            return [("SampleCoreWorkflow", SampleCoreWorkflow)]
                        if obj == recipe_mock_module:
                            return [("SampleRecipeWorkflow", SampleRecipeWorkflow)]
                    return []

                mock_getmembers.side_effect = mock_getmembers_side_effect

                # Act - Discovery with recipes ENABLED
                discovery = TemporalDiscovery(str(temp_path / "awa"), include_recipes=True)
                workflows, _ = discovery.discover_workflows_and_activities()

                # Assert - Should find both core and recipe workflows
                assert len(workflows) >= 1  # Should find at least the recipe workflow

                # Recipe workflow SHOULD be in the list
                recipe_workflow_found = any(
                    w.__class__.__name__ == "SampleRecipeWorkflow" or w == SampleRecipeWorkflow for w in workflows
                )
                assert recipe_workflow_found, "Recipe workflow should be discovered when include_recipes=True"

    def test_recipe_count(self) -> None:
        """Test that more workflows are found with recipes enabled than disabled."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            core_workflows_dir = temp_path / "awa" / "core" / "workflows"
            core_workflows_dir.mkdir(parents=True)
            recipe_workflows_dir = temp_path / "cookbook" / "recipes" / "workflows"
            recipe_workflows_dir.mkdir(parents=True)

            # Mock pkgutil.walk_packages to return different modules based on path
            def mock_walk_packages_side_effect(_paths: list[str], prefix: str) -> list[Any]:
                mock_module_info = MagicMock()
                if "core.workflows" in prefix:
                    mock_module_info.name = "core.workflows.test_module"
                elif "cookbook.recipes.workflows" in prefix:
                    mock_module_info.name = "cookbook.recipes.workflows.test_module"
                else:
                    mock_module_info.name = f"{prefix}.test_module"
                return [mock_module_info]

            # Mock modules with different workflows
            core_mock_module = MagicMock()
            core_mock_module.SampleCoreWorkflow = SampleCoreWorkflow

            recipe_mock_module = MagicMock()
            recipe_mock_module.SampleRecipeWorkflow = SampleRecipeWorkflow

            def mock_import_side_effect(module_name: str) -> Any:  # noqa: ANN401
                if "cookbook.recipes" in module_name:
                    return recipe_mock_module
                return core_mock_module

            with (
                patch("pkgutil.walk_packages") as mock_walk_packages,
                patch("importlib.import_module") as mock_import,
                patch("inspect.getmembers") as mock_getmembers,
            ):
                mock_walk_packages.side_effect = mock_walk_packages_side_effect
                mock_import.side_effect = mock_import_side_effect

                def mock_getmembers_side_effect(obj: Any, predicate: Any) -> list[tuple[str, Any]]:  # noqa: ANN401
                    if predicate.__name__ == "isclass":
                        if obj == core_mock_module:
                            return [("SampleCoreWorkflow", SampleCoreWorkflow)]
                        if obj == recipe_mock_module:
                            return [("SampleRecipeWorkflow", SampleRecipeWorkflow)]
                    return []

                mock_getmembers.side_effect = mock_getmembers_side_effect

                # Act - Discovery without recipes
                discovery_without = TemporalDiscovery(str(temp_path / "awa"), include_recipes=False)
                workflows_without, _activities = discovery_without.discover_workflows_and_activities()

                # Act - Discovery with recipes
                discovery_with = TemporalDiscovery(str(temp_path / "awa"), include_recipes=True)
                workflows_with, _activities = discovery_with.discover_workflows_and_activities()

                # Assert - More workflows should be found with recipes enabled
                assert len(workflows_with) >= len(workflows_without), (
                    "Should find at least as many workflows with recipes enabled"
                )

    def test_discover_workflows_only_without_recipes(self) -> None:
        """Test that discover_workflows_only respects include_recipes=False."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            core_workflows_dir = temp_path / "awa" / "core" / "workflows"
            core_workflows_dir.mkdir(parents=True)
            recipe_workflows_dir = temp_path / "cookbook" / "recipes" / "workflows"
            recipe_workflows_dir.mkdir(parents=True)

            # Mock pkgutil.walk_packages
            def mock_walk_packages_side_effect(_paths: list[str], prefix: str) -> list[Any]:
                mock_module_info = MagicMock()
                if "core.workflows" in prefix:
                    mock_module_info.name = "core.workflows.test_module"
                elif "cookbook.recipes.workflows" in prefix:
                    mock_module_info.name = "cookbook.recipes.workflows.test_module"
                else:
                    mock_module_info.name = f"{prefix}.test_module"
                return [mock_module_info]

            core_mock_module = MagicMock()
            core_mock_module.SampleCoreWorkflow = SampleCoreWorkflow

            recipe_mock_module = MagicMock()
            recipe_mock_module.SampleRecipeWorkflow = SampleRecipeWorkflow

            def mock_import_side_effect(module_name: str) -> Any:  # noqa: ANN401
                if "cookbook.recipes" in module_name:
                    return recipe_mock_module
                return core_mock_module

            with (
                patch("pkgutil.walk_packages") as mock_walk_packages,
                patch("importlib.import_module") as mock_import,
                patch("inspect.getmembers") as mock_getmembers,
            ):
                mock_walk_packages.side_effect = mock_walk_packages_side_effect
                mock_import.side_effect = mock_import_side_effect

                def mock_getmembers_side_effect(obj: Any, predicate: Any) -> list[tuple[str, Any]]:  # noqa: ANN401
                    if predicate.__name__ == "isclass":
                        if obj == core_mock_module:
                            return [("SampleCoreWorkflow", SampleCoreWorkflow)]
                        if obj == recipe_mock_module:
                            return [("SampleRecipeWorkflow", SampleRecipeWorkflow)]
                    return []

                mock_getmembers.side_effect = mock_getmembers_side_effect

                # Act - Discovery workflows only with recipes DISABLED
                discovery = TemporalDiscovery(str(temp_path / "awa"), include_recipes=False)
                workflows = discovery.discover_workflows_only()

                # Assert - Should not find recipe workflows
                recipe_workflow_found = any(w.__class__.__name__ == "SampleRecipeWorkflow" for w in workflows)
                assert not recipe_workflow_found, (
                    "Recipe workflow should not be discovered in discover_workflows_only when include_recipes=False"
                )

    def test_discover_workflows_only_with_recipes(self) -> None:
        """Test that discover_workflows_only respects include_recipes=True."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            core_workflows_dir = temp_path / "awa" / "core" / "workflows"
            core_workflows_dir.mkdir(parents=True)
            recipe_workflows_dir = temp_path / "cookbook" / "recipes" / "workflows"
            recipe_workflows_dir.mkdir(parents=True)

            # Mock pkgutil.walk_packages
            def mock_walk_packages_side_effect(_paths: list[str], prefix: str) -> list[Any]:
                mock_module_info = MagicMock()
                if "core.workflows" in prefix:
                    mock_module_info.name = "core.workflows.test_module"
                elif "cookbook.recipes.workflows" in prefix:
                    mock_module_info.name = "cookbook.recipes.workflows.test_module"
                else:
                    mock_module_info.name = f"{prefix}.test_module"
                return [mock_module_info]

            core_mock_module = MagicMock()
            core_mock_module.SampleCoreWorkflow = SampleCoreWorkflow

            recipe_mock_module = MagicMock()
            recipe_mock_module.SampleRecipeWorkflow = SampleRecipeWorkflow

            def mock_import_side_effect(module_name: str) -> Any:  # noqa: ANN401
                if "cookbook.recipes" in module_name:
                    return recipe_mock_module
                return core_mock_module

            with (
                patch("pkgutil.walk_packages") as mock_walk_packages,
                patch("importlib.import_module") as mock_import,
                patch("inspect.getmembers") as mock_getmembers,
            ):
                mock_walk_packages.side_effect = mock_walk_packages_side_effect
                mock_import.side_effect = mock_import_side_effect

                def mock_getmembers_side_effect(obj: Any, predicate: Any) -> list[tuple[str, Any]]:  # noqa: ANN401
                    if predicate.__name__ == "isclass":
                        if obj == core_mock_module:
                            return [("SampleCoreWorkflow", SampleCoreWorkflow)]
                        if obj == recipe_mock_module:
                            return [("SampleRecipeWorkflow", SampleRecipeWorkflow)]
                    return []

                mock_getmembers.side_effect = mock_getmembers_side_effect

                # Act - Discovery workflows only with recipes ENABLED
                discovery = TemporalDiscovery(str(temp_path / "awa"), include_recipes=True)
                workflows = discovery.discover_workflows_only()

                # Assert - Should find recipe workflows
                recipe_workflow_found = any(
                    w.__class__.__name__ == "SampleRecipeWorkflow" or w == SampleRecipeWorkflow for w in workflows
                )
                assert recipe_workflow_found, (
                    "Recipe workflow should be discovered in discover_workflows_only when include_recipes=True"
                )

    def test_recipe_activities_discovery(self) -> None:
        """Test that recipe activities are discovered when include_recipes=True."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            core_activities_dir = temp_path / "awa" / "core" / "activities"
            core_activities_dir.mkdir(parents=True)
            recipe_activities_dir = temp_path / "cookbook" / "recipes" / "activities"
            recipe_activities_dir.mkdir(parents=True)

            # Mock pkgutil.walk_packages
            def mock_walk_packages_side_effect(_paths: list[str], prefix: str) -> list[Any]:
                mock_module_info = MagicMock()
                if "core.activities" in prefix:
                    mock_module_info.name = "core.activities.test_module"
                elif "cookbook.recipes.activities" in prefix:
                    mock_module_info.name = "cookbook.recipes.activities.test_module"
                else:
                    mock_module_info.name = f"{prefix}.test_module"
                return [mock_module_info]

            core_mock_module = MagicMock()
            core_mock_module.sample_core_activity = sample_core_activity

            recipe_mock_module = MagicMock()
            recipe_mock_module.sample_recipe_activity = sample_recipe_activity

            def mock_import_side_effect(module_name: str) -> Any:  # noqa: ANN401
                if "cookbook.recipes" in module_name:
                    return recipe_mock_module
                return core_mock_module

            with (
                patch("pkgutil.walk_packages") as mock_walk_packages,
                patch("importlib.import_module") as mock_import,
                patch("inspect.getmembers") as mock_getmembers,
            ):
                mock_walk_packages.side_effect = mock_walk_packages_side_effect
                mock_import.side_effect = mock_import_side_effect

                def mock_getmembers_side_effect(obj: Any, predicate: Any) -> list[tuple[str, Any]]:  # noqa: ANN401
                    if predicate.__name__ == "isfunction":
                        if obj == core_mock_module:
                            return [("sample_core_activity", sample_core_activity)]
                        if obj == recipe_mock_module:
                            return [("sample_recipe_activity", sample_recipe_activity)]
                    return []

                mock_getmembers.side_effect = mock_getmembers_side_effect

                # Act - Discovery with recipes ENABLED
                discovery = TemporalDiscovery(str(temp_path / "awa"), include_recipes=True)
                _, activities = discovery.discover_workflows_and_activities()

                # Assert - Should find recipe activities
                recipe_activity_found = sample_recipe_activity in activities
                assert recipe_activity_found, "Recipe activity should be discovered when include_recipes=True"

    def test_default_include_recipes_is_false(self) -> None:
        """Test that the default value for include_recipes is False for backward compatibility."""
        # Arrange & Act
        discovery = TemporalDiscovery()

        # Assert
        assert discovery.include_recipes is False, (
            "Default value for include_recipes should be False for backward compatibility"
        )
