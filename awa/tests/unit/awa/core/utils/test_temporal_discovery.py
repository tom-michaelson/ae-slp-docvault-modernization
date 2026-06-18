import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from temporalio import activity, workflow
from temporalio.client import Client

from awa.core.activities.transform import TransformActivity
from awa.core.utils.temporal_discovery import TemporalDiscovery


# Sample function-based activity for testing
@activity.defn(name="test-sample-activity")
async def sample_function_activity(param: str) -> str:
    return f"Hello {param}"


# Sample activity without decorator name for testing fallback
@activity.defn
async def sample_activity_no_name(param: str) -> str:
    return f"Hello {param}"


# Sample workflow for testing
@workflow.defn(name="test-sample-workflow")
class SampleWorkflow:
    @workflow.run
    async def run(self, param: str) -> str:
        return f"Workflow: {param}"


# Sample workflow without decorator name for testing fallback
@workflow.defn
class SampleWorkflowNoName:
    @workflow.run
    async def run(self, param: str) -> str:
        return f"Workflow: {param}"


# Sample class-based activity for testing
class SampleClassActivity:
    def __init__(self, client: Client) -> None:
        self._client = client

    @activity.defn(name="test-class-activity")
    async def sample_class_activity_method(self, param: str) -> str:
        return f"Hello from class {param}"


class TestTemporalDiscovery:
    def test_discover_function_based_activities(self) -> None:
        """Test that function-based activities are discovered correctly."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            activities_dir = temp_path / "activities"
            activities_dir.mkdir()

            # Mock pkgutil.walk_packages to return a fake module info
            mock_module_info = MagicMock()
            mock_module_info.name = "activities.test_module"

            # Mock the module with the function activity
            mock_module = MagicMock()
            mock_module.sample_function_activity = sample_function_activity

            with patch("pkgutil.walk_packages") as mock_walk_packages, patch("importlib.import_module") as mock_import:
                mock_walk_packages.return_value = [mock_module_info]
                mock_import.return_value = mock_module

                discovery = TemporalDiscovery(str(temp_path))

                # Act
                _, activities = discovery.discover_workflows_and_activities()

                # Assert
                assert len(activities) > 0
                assert sample_function_activity in activities

    def test_discover_class_based_activities_with_dependencies(self) -> None:
        """Test that class-based activities are discovered and instantiated with dependencies."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            activities_dir = temp_path / "core" / "activities"
            activities_dir.mkdir(parents=True)

            # Create a mock client dependency
            mock_client = MagicMock(spec=Client)
            dependencies = [mock_client]

            # Mock pkgutil.walk_packages to return a fake module info
            mock_module_info = MagicMock()
            mock_module_info.name = "core.activities.test_module"

            # Mock the module with the class activity
            mock_module = MagicMock()
            mock_module.SampleClassActivity = SampleClassActivity

            with (
                patch("pkgutil.walk_packages") as mock_walk_packages,
                patch("importlib.import_module") as mock_import,
                patch("inspect.getmembers") as mock_getmembers,
            ):
                mock_walk_packages.return_value = [mock_module_info]
                mock_import.return_value = mock_module

                # Mock inspect.getmembers to return classes and methods properly
                def mock_getmembers_side_effect(obj: Any, predicate: Any) -> list[tuple[str, Any]]:  # noqa: ANN401
                    if predicate.__name__ == "isclass":
                        return [("SampleClassActivity", SampleClassActivity)]
                    if predicate.__name__ == "isfunction":
                        # Return activity methods when checking class methods
                        if hasattr(obj, "sample_class_activity_method"):
                            return [("sample_class_activity_method", obj.sample_class_activity_method)]
                        return []
                    if predicate.__name__ == "ismethod":
                        # Return bound methods from instantiated class
                        if hasattr(obj, "sample_class_activity_method"):
                            return [("sample_class_activity_method", obj.sample_class_activity_method)]
                        return []
                    return []

                mock_getmembers.side_effect = mock_getmembers_side_effect

                discovery = TemporalDiscovery(str(temp_path))

                # Act
                _, activities = discovery.discover_workflows_and_activities(dependencies)

                # Assert
                assert len(activities) > 0
                # Check if any activity methods were found
                activity_found = any(
                    hasattr(activity, "__self__") and isinstance(activity.__self__, SampleClassActivity)
                    for activity in activities
                )
                assert activity_found

    def test_discover_mixed_activities(self) -> None:
        """Test that both function and class-based activities are discovered together."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            activities_dir = temp_path / "core" / "activities"
            activities_dir.mkdir(parents=True)

            # Create a mock client dependency
            mock_client = MagicMock(spec=Client)
            dependencies = [mock_client]

            # Mock pkgutil.walk_packages to return fake module infos
            mock_module_info = MagicMock()
            mock_module_info.name = "core.activities.test_module"

            # Mock the module with both function and class activities
            mock_module = MagicMock()
            mock_module.sample_function_activity = sample_function_activity
            mock_module.SampleClassActivity = SampleClassActivity

            with (
                patch("pkgutil.walk_packages") as mock_walk_packages,
                patch("importlib.import_module") as mock_import,
                patch("inspect.getmembers") as mock_getmembers,
            ):
                mock_walk_packages.return_value = [mock_module_info]
                mock_import.return_value = mock_module

                # Mock inspect.getmembers to return both functions and classes
                def mock_getmembers_side_effect(obj: Any, predicate: Any) -> list[tuple[str, Any]]:  # noqa: ANN401
                    if predicate.__name__ == "isfunction":
                        if obj == mock_module:
                            return [("sample_function_activity", sample_function_activity)]
                        if hasattr(obj, "sample_class_activity_method"):
                            return [("sample_class_activity_method", obj.sample_class_activity_method)]
                        return []
                    if predicate.__name__ == "isclass":
                        return [("SampleClassActivity", SampleClassActivity)]
                    if predicate.__name__ == "ismethod":
                        if hasattr(obj, "sample_class_activity_method"):
                            return [("sample_class_activity_method", obj.sample_class_activity_method)]
                        return []
                    return []

                mock_getmembers.side_effect = mock_getmembers_side_effect

                discovery = TemporalDiscovery(str(temp_path))

                # Act
                _, activities = discovery.discover_workflows_and_activities(dependencies)

                # Assert
                assert len(activities) >= 2

                # Check for function activity
                assert sample_function_activity in activities

                # Check for class activity method
                class_activity_found = any(
                    hasattr(activity, "__self__") and isinstance(activity.__self__, SampleClassActivity)
                    for activity in activities
                )
                assert class_activity_found

    def test_class_activity_without_matching_dependency(self) -> None:
        """Test that class activities without matching dependencies are skipped."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            activities_dir = temp_path / "core" / "activities"
            activities_dir.mkdir(parents=True)

            # No dependencies provided
            dependencies = []

            # Mock pkgutil.walk_packages to return a fake module info
            mock_module_info = MagicMock()
            mock_module_info.name = "core.activities.test_module"

            # Mock the module with the class activity
            mock_module = MagicMock()
            mock_module.SampleClassActivity = SampleClassActivity

            with (
                patch("pkgutil.walk_packages") as mock_walk_packages,
                patch("importlib.import_module") as mock_import,
                patch("inspect.getmembers") as mock_getmembers,
            ):
                mock_walk_packages.return_value = [mock_module_info]
                mock_import.return_value = mock_module

                # Mock inspect.getmembers to return classes
                def mock_getmembers_side_effect(obj: Any, predicate: Any) -> list[tuple[str, Any]]:  # noqa: ANN401
                    if predicate.__name__ == "isclass":
                        return [("SampleClassActivity", SampleClassActivity)]
                    if predicate.__name__ == "isfunction":
                        if hasattr(obj, "sample_class_activity_method"):
                            return [("sample_class_activity_method", obj.sample_class_activity_method)]
                        return []
                    return []

                mock_getmembers.side_effect = mock_getmembers_side_effect

                discovery = TemporalDiscovery(str(temp_path))

                # Act
                _, activities = discovery.discover_workflows_and_activities(dependencies)

                # Assert
                # Should not find any class activities since no matching dependencies
                class_activity_found = any(
                    hasattr(activity, "__self__") and isinstance(activity.__self__, SampleClassActivity)
                    for activity in activities
                )
                assert not class_activity_found

    def test_instantiate_activity_class_with_correct_dependency_matching(self) -> None:
        """Test that dependencies are matched correctly by type."""
        # Arrange
        mock_client = MagicMock(spec=Client)
        dependencies = [mock_client]

        discovery = TemporalDiscovery()

        # Act
        activity_methods = discovery._instantiate_activity_class(SampleClassActivity, dependencies)

        # Assert
        assert len(activity_methods) > 0

        # Verify the instance was created with the correct dependency
        for method in activity_methods:
            if hasattr(method, "__self__"):
                assert isinstance(method.__self__, SampleClassActivity)
                assert method.__self__._client is mock_client

    def test_integration_with_transform_activity(self) -> None:
        """Integration test that demonstrates the system works with TransformActivity."""
        # Arrange
        mock_client = MagicMock(spec=Client)
        dependencies = [mock_client]

        discovery = TemporalDiscovery()

        # Act
        activity_methods = discovery._instantiate_activity_class(TransformActivity, dependencies)

        # Assert
        assert len(activity_methods) > 0

        # Verify the instance was created with the correct dependency
        for method in activity_methods:
            if hasattr(method, "__self__") and hasattr(method.__self__, "_temporal_client"):
                assert isinstance(method.__self__, TransformActivity)
                assert method.__self__._temporal_client is mock_client

    def test_get_workflow_name_with_decorator_name(self) -> None:
        """Test that _get_workflow_name returns decorator-defined name when available."""
        # Arrange
        discovery = TemporalDiscovery()

        # Act
        result = discovery._get_workflow_name(SampleWorkflow)

        # Assert
        assert result == "test-sample-workflow"

    def test_get_workflow_name_fallback_to_class_name(self) -> None:
        """Test that _get_workflow_name falls back to class name when decorator name is not available."""
        # Arrange
        discovery = TemporalDiscovery()

        # Act
        result = discovery._get_workflow_name(SampleWorkflowNoName)

        # Assert
        assert result == "SampleWorkflowNoName"

    def test_get_workflow_name_with_invalid_object(self) -> None:
        """Test that _get_workflow_name handles invalid objects gracefully."""
        # Arrange
        discovery = TemporalDiscovery()

        # Create an object without temporal definition
        class InvalidObject:
            __name__ = "InvalidObject"

        # Act
        result = discovery._get_workflow_name(InvalidObject)

        # Assert
        assert result == "InvalidObject"

    def test_get_activity_name_with_decorator_name(self) -> None:
        """Test that _get_activity_name returns decorator-defined name when available."""
        # Arrange
        discovery = TemporalDiscovery()

        # Act
        result = discovery._get_activity_name(sample_function_activity)

        # Assert
        assert result == "test-sample-activity"

    def test_get_activity_name_fallback_to_function_name(self) -> None:
        """Test that _get_activity_name falls back to function name when decorator name is not available."""
        # Arrange
        discovery = TemporalDiscovery()

        # Act
        result = discovery._get_activity_name(sample_activity_no_name)

        # Assert
        assert result == "sample_activity_no_name"

    def test_get_activity_name_with_class_method(self) -> None:
        """Test that _get_activity_name works with class-based activity methods."""
        # Arrange
        discovery = TemporalDiscovery()
        mock_client = MagicMock(spec=Client)

        # Create an instance and get the bound method
        instance = SampleClassActivity(mock_client)
        method = instance.sample_class_activity_method

        # Act
        result = discovery._get_activity_name(method)

        # Assert
        assert result == "test-class-activity"

    def test_get_activity_name_with_invalid_object(self) -> None:
        """Test that _get_activity_name handles invalid objects gracefully."""
        # Arrange
        discovery = TemporalDiscovery()

        # Create an object without temporal definition
        def invalid_function() -> str:
            return "test"

        # Act
        result = discovery._get_activity_name(invalid_function)

        # Assert
        assert result == "invalid_function"
