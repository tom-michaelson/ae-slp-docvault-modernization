"""Tests for workflow metadata utility functions."""

import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel
from temporalio import workflow

from awa.core.utils.workflow_metadata import (
    ParameterInfo,
    WorkflowMetadata,
    _extract_run_method_parameter_info,
    _extract_run_method_parameters,
    _extract_workflow_metadata,
    _format_type_annotation,
    format_workflow_parameters,
    get_workflow_metadata,
    get_workflow_queue,
)


# Sample workflow for testing
@workflow.defn
class SampleWorkflow:
    @workflow.run
    async def run(self, name: str, count: int) -> str:
        return f"Hello {name}, count: {count}"


@workflow.defn
class SampleWorkflowNoParams:
    @workflow.run
    async def run(self) -> str:
        return "Hello World"


class SampleWorkflowNoRunMethod:
    pass


# Pydantic model for testing


class SampleInput(BaseModel):
    name: str
    value: int


@workflow.defn
class SampleWorkflowWithPydantic:
    @workflow.run
    async def run(self, workflow_input: SampleInput) -> str:
        return f"Hello {workflow_input.name}"


class TestWorkflowMetadata:
    def test_parameter_info_init(self) -> None:
        """Test ParameterInfo initialization."""
        param_info = ParameterInfo(name="test_param", type_str="str")
        assert param_info.name == "test_param"
        assert param_info.type_str == "str"

        # Test with defaults
        param_info_defaults = ParameterInfo(name="test_param")
        assert param_info_defaults.name == "test_param"
        assert param_info_defaults.type_str is None

    def test_workflow_metadata_init(self) -> None:
        """Test WorkflowMetadata initialization."""
        param_info = [ParameterInfo(name="param1", type_str="str")]
        metadata = WorkflowMetadata(
            name="TestWorkflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=["param1", "param2"],
            parameter_info=param_info,
        )

        assert metadata.name == "TestWorkflow"
        assert metadata.class_name == "TestWorkflow"
        assert metadata.module == "test.module"
        assert metadata.parameters == ["param1", "param2"]
        assert len(metadata.parameter_info) == 1
        assert metadata.parameter_info[0].name == "param1"

    @patch("awa.core.utils.workflow_metadata.TemporalDiscovery")
    def test_get_workflow_metadata_success(self, mock_discovery_class: MagicMock) -> None:
        """Test successful retrieval of workflow metadata."""
        # Arrange
        mock_discovery = MagicMock()
        mock_discovery_class.return_value = mock_discovery

        # Mock workflow discovery to return sample workflows
        mock_workflows = [SampleWorkflow, SampleWorkflowNoParams]
        mock_discovery.discover_workflows_only.return_value = mock_workflows

        # Act
        result = get_workflow_metadata()

        # Assert
        assert len(result) == 2
        assert all(isinstance(metadata, WorkflowMetadata) for metadata in result)

        # Check first workflow
        first_workflow = next(m for m in result if m.name == "SampleWorkflow")
        assert first_workflow.class_name == "SampleWorkflow"
        assert first_workflow.module == "test_workflow_metadata"
        assert first_workflow.parameters == ["name", "count"]
        assert len(first_workflow.parameter_info) == 2
        assert first_workflow.parameter_info[0].name == "name"
        assert first_workflow.parameter_info[0].type_str == "str"
        assert first_workflow.parameter_info[1].name == "count"
        assert first_workflow.parameter_info[1].type_str == "int"

        # Check second workflow
        second_workflow = next(m for m in result if m.name == "SampleWorkflowNoParams")
        assert second_workflow.class_name == "SampleWorkflowNoParams"
        assert second_workflow.module == "test_workflow_metadata"
        assert second_workflow.parameters == []
        assert second_workflow.parameter_info == []

    @patch("awa.core.utils.workflow_metadata.TemporalDiscovery")
    def test_get_workflow_metadata_discovery_failure(self, mock_discovery_class: MagicMock) -> None:
        """Test handling of discovery failures."""
        # Arrange
        mock_discovery = MagicMock()
        mock_discovery_class.return_value = mock_discovery

        # Mock discovery to raise an exception
        mock_discovery.discover_workflows_only.side_effect = Exception("Discovery failed")

        # Act & Assert
        with pytest.raises(Exception, match="Discovery failed"):
            get_workflow_metadata()

    def test_extract_workflow_metadata(self) -> None:
        """Test extracting metadata from a workflow class."""
        # Act
        metadata = _extract_workflow_metadata(SampleWorkflow)

        # Assert
        assert metadata.name == "SampleWorkflow"
        assert metadata.class_name == "SampleWorkflow"
        assert metadata.module == "test_workflow_metadata"
        assert metadata.parameters == ["name", "count"]
        assert len(metadata.parameter_info) == 2
        assert metadata.parameter_info[0].name == "name"
        assert metadata.parameter_info[0].type_str == "str"
        assert metadata.parameter_info[1].name == "count"
        assert metadata.parameter_info[1].type_str == "int"

    def test_extract_workflow_metadata_no_params(self) -> None:
        """Test extracting metadata from a workflow with no parameters."""
        # Act
        metadata = _extract_workflow_metadata(SampleWorkflowNoParams)

        # Assert
        assert metadata.name == "SampleWorkflowNoParams"
        assert metadata.class_name == "SampleWorkflowNoParams"
        assert metadata.module == "test_workflow_metadata"
        assert metadata.parameters == []
        assert metadata.parameter_info == []

    def test_extract_run_method_parameters(self) -> None:
        """Test extracting parameters from workflow run method."""
        # Act
        parameters = _extract_run_method_parameters(SampleWorkflow)

        # Assert
        assert parameters == ["name", "count"]

    def test_extract_run_method_parameters_no_params(self) -> None:
        """Test extracting parameters from workflow run method with no parameters."""
        # Act
        parameters = _extract_run_method_parameters(SampleWorkflowNoParams)

        # Assert
        assert parameters == []

    def test_extract_run_method_parameters_no_run_method(self) -> None:
        """Test extracting parameters from workflow class without run method."""
        # Act
        parameters = _extract_run_method_parameters(SampleWorkflowNoRunMethod)

        # Assert
        assert parameters == []

    def test_extract_run_method_parameters_with_exception(self) -> None:
        """Test handling of exceptions during parameter extraction."""
        # Arrange
        mock_workflow = MagicMock()
        mock_workflow.run = MagicMock()

        # Mock inspect.signature to raise a ValueError exception (one of the caught exceptions)
        with patch("awa.core.utils.workflow_metadata.inspect.signature", side_effect=ValueError("Signature error")):
            # Act
            parameters = _extract_run_method_parameters(mock_workflow)

            # Assert
            assert parameters == []

    @patch("awa.core.utils.workflow_metadata.TemporalDiscovery")
    def test_get_workflow_metadata_empty_list(self, mock_discovery_class: MagicMock) -> None:
        """Test handling of empty workflow discovery results."""
        # Arrange
        mock_discovery = MagicMock()
        mock_discovery_class.return_value = mock_discovery

        # Mock discovery to return empty list
        mock_discovery.discover_workflows_and_activities.return_value = ([], [])

        # Act
        result = get_workflow_metadata()

        # Assert
        assert result == []

    def test_extract_workflow_metadata_with_complex_module_path(self) -> None:
        """Test extracting metadata from workflow with complex module path."""
        # Arrange
        mock_workflow = MagicMock()
        mock_definition = MagicMock()
        mock_definition.name = "ComplexWorkflow"
        setattr(mock_workflow, "__temporal_workflow_definition", mock_definition)
        mock_workflow.__module__ = "some.very.deep.module.path"
        mock_workflow.run = MagicMock()

        with patch("awa.core.utils.workflow_metadata.inspect.signature") as mock_signature:
            mock_signature.return_value.parameters = {}

            # Act
            metadata = _extract_workflow_metadata(mock_workflow)

            # Assert
            assert metadata.name == "ComplexWorkflow"
            assert metadata.class_name == "ComplexWorkflow"
            assert metadata.module == "some.very.deep.module.path"
            assert metadata.parameters == []

    def test_extract_run_method_parameter_info(self) -> None:
        """Test extracting detailed parameter information from workflow run method."""
        # Act
        parameter_info = _extract_run_method_parameter_info(SampleWorkflow)

        # Assert
        assert len(parameter_info) == 2
        assert parameter_info[0].name == "name"
        assert parameter_info[0].type_str == "str"

    def test_format_workflow_parameters_with_type_info(self) -> None:
        """Test formatting parameters with type information."""

        # Arrange
        class MockModule:
            pass

        mock_import = MockModule()
        with patch.object(importlib, "import_module", return_value=mock_import):
            metadata = WorkflowMetadata(
                name="TestWorkflow",
                class_name="TestWorkflow",
                module="test.module",
                parameters=["param1", "param2", "param3"],
                parameter_info=[
                    ParameterInfo(name="param1", type_str="str"),
                    ParameterInfo(name="param2", type_str="BuildPromptParams"),
                    ParameterInfo(name="param3", type_str=None),  # No type info
                ],
            )

            # Act
            formatted = format_workflow_parameters(metadata)
            # Assert
            assert formatted == {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter param1",
                    },
                    "param2": {
                        "type": "string",
                        "description": "Parameter param2",
                    },
                    "param3": {
                        "type": "string",
                        "description": "Parameter param3",
                    },
                },
            }

    def test_format_workflow_parameters_no_type_info(self) -> None:
        """Test formatting parameters without type information (fallback to basic names)."""
        # Arrange
        metadata = WorkflowMetadata(
            name="TestWorkflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=["param1", "param2"],
            parameter_info=[],  # No parameter info
        )

        # Act
        formatted = format_workflow_parameters(metadata)

        # Assert
        expected = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "string"},
            },
        }
        assert formatted == expected

    def test_format_workflow_parameters_empty_parameters(self) -> None:
        """Test formatting workflow with no parameters."""
        # Arrange
        metadata = WorkflowMetadata(
            name="TestWorkflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=[],
            parameter_info=[],
        )

        # Act
        formatted = format_workflow_parameters(metadata)

        # Assert
        assert formatted == {}

    def test_format_workflow_parameters_none_parameter_info(self) -> None:
        """Test formatting parameters when parameter_info is None."""
        # Arrange
        metadata = WorkflowMetadata(
            name="TestWorkflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=["param1", "param2"],
            parameter_info=None,  # None parameter info
        )

        # Act
        formatted = format_workflow_parameters(metadata)

        # Assert
        expected = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "string"},
            },
        }
        assert formatted == expected

    def test_extract_run_method_parameter_info_no_params(self) -> None:
        """Test extracting parameter info from workflow with no parameters."""
        # Act
        parameter_info = _extract_run_method_parameter_info(SampleWorkflowNoParams)

        # Assert
        assert parameter_info == []

    def test_extract_run_method_parameter_info_no_run_method(self) -> None:
        """Test extracting parameter info from workflow without run method."""
        # Act
        parameter_info = _extract_run_method_parameter_info(SampleWorkflowNoRunMethod)

        # Assert
        assert parameter_info == []

    def test_format_type_annotation_basic_types(self) -> None:
        """Test formatting basic type annotations."""
        assert _format_type_annotation(str) == "str"
        assert _format_type_annotation(int) == "int"
        assert _format_type_annotation(bool) == "bool"
        assert _format_type_annotation(float) == "float"

    def test_format_type_annotation_none_type(self) -> None:
        """Test formatting None type annotation."""
        assert _format_type_annotation(type(None)) == "None"

    def test_format_type_annotation_generic_types(self) -> None:
        """Test formatting generic type annotations."""
        from typing import Any

        # Test list[str] from modern Python syntax
        list_str_type = list[str]
        formatted = _format_type_annotation(list_str_type)
        assert formatted == "list[str]"

        # Test dict[str, Any] from modern Python syntax
        dict_type = dict[str, Any]
        formatted = _format_type_annotation(dict_type)
        assert formatted == "dict[str, Any]"

    def test_extract_workflow_metadata_with_pydantic(self) -> None:
        """Test extracting metadata from workflow with Pydantic model parameter."""
        # Act
        metadata = _extract_workflow_metadata(SampleWorkflowWithPydantic)

        # Assert
        assert metadata.name == "SampleWorkflowWithPydantic"
        assert metadata.class_name == "SampleWorkflowWithPydantic"
        assert metadata.module == "test_workflow_metadata"
        assert metadata.parameters == ["workflow_input"]
        assert len(metadata.parameter_info) == 1
        assert metadata.parameter_info[0].name == "workflow_input"
        assert metadata.parameter_info[0].type_str == "SampleInput"

    @patch("awa.core.api.registry.storage.FileSystemRegistryStorage")
    @pytest.mark.asyncio
    async def test_get_workflow_queue_core_workflow_found(
        self,
        mock_storage_class: MagicMock,
    ) -> None:
        """Test successful lookup of core workflow queue from registry."""
        # Arrange
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock workflow definition from core worker
        mock_workflow_def = MagicMock()
        mock_workflow_def.name = "TestWorkflow"
        mock_workflow_def.task_queue = "awa_default"

        # Mock worker registration
        mock_worker = MagicMock()
        mock_worker.worker_name = "core-worker"
        mock_worker.workflows = [mock_workflow_def]

        mock_storage.list_active_workers = AsyncMock(return_value=[mock_worker])

        # Act
        result = await get_workflow_queue("TestWorkflow")

        # Assert
        assert result == "awa_default"
        mock_storage.list_active_workers.assert_called_once()

    @patch("awa.core.api.registry.storage.FileSystemRegistryStorage")
    @pytest.mark.asyncio
    async def test_get_workflow_queue_external_workflow_found(
        self,
        mock_storage_class: MagicMock,
    ) -> None:
        """Test successful lookup of external workflow queue from registry."""
        # Arrange
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock workflow definition from external worker
        mock_workflow_def = MagicMock()
        mock_workflow_def.name = "ExternalWorkflow"
        mock_workflow_def.task_queue = "external-queue"

        # Mock worker registration
        mock_worker = MagicMock()
        mock_worker.worker_name = "recipes-worker"
        mock_worker.workflows = [mock_workflow_def]

        mock_storage.list_active_workers = AsyncMock(return_value=[mock_worker])

        # Act
        result = await get_workflow_queue("ExternalWorkflow")

        # Assert
        assert result == "external-queue"
        mock_storage.list_active_workers.assert_called_once()

    @patch("awa.core.api.registry.storage.FileSystemRegistryStorage")
    @pytest.mark.asyncio
    async def test_get_workflow_queue_workflow_not_found(
        self,
        mock_storage_class: MagicMock,
    ) -> None:
        """Test lookup when workflow is not found in registry."""
        # Arrange
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        mock_storage.list_active_workers = AsyncMock(return_value=[])  # No workers registered

        # Act
        result = await get_workflow_queue("NonExistentWorkflow")

        # Assert
        assert result is None
        mock_storage.list_active_workers.assert_called_once()

    @patch("awa.core.api.registry.storage.FileSystemRegistryStorage")
    @pytest.mark.asyncio
    async def test_get_workflow_queue_multiple_workers(
        self,
        mock_storage_class: MagicMock,
    ) -> None:
        """Test that workflow lookup works with multiple registered workers."""
        # Arrange
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock core worker with core workflow
        core_workflow_def = MagicMock()
        core_workflow_def.name = "awa-hello-world"
        core_workflow_def.task_queue = "awa_default"

        core_worker = MagicMock()
        core_worker.worker_name = "core-worker"
        core_worker.workflows = [core_workflow_def]

        # Mock external worker with external workflow
        external_workflow_def = MagicMock()
        external_workflow_def.name = "ExternalWorkflow"
        external_workflow_def.task_queue = "external-queue"

        external_worker = MagicMock()
        external_worker.worker_name = "recipes-worker"
        external_worker.workflows = [external_workflow_def]

        mock_storage.list_active_workers = AsyncMock(return_value=[core_worker, external_worker])

        # Act
        result = await get_workflow_queue("ExternalWorkflow")

        # Assert
        assert result == "external-queue"
        mock_storage.list_active_workers.assert_called_once()

    @patch("awa.core.api.registry.storage.FileSystemRegistryStorage")
    @pytest.mark.asyncio
    async def test_get_workflow_queue_registry_access_fails(
        self,
        mock_storage_class: MagicMock,
    ) -> None:
        """Test that function returns None when registry access fails."""
        # Arrange
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        mock_storage.list_active_workers = AsyncMock(side_effect=Exception("Registry access failed"))

        # Act
        result = await get_workflow_queue("TestWorkflow")

        # Assert
        assert result is None
        mock_storage.list_active_workers.assert_called_once()

    @patch("awa.core.api.registry.storage.FileSystemRegistryStorage")
    @pytest.mark.asyncio
    async def test_get_workflow_queue_workflow_in_multiple_workers(
        self,
        mock_storage_class: MagicMock,
    ) -> None:
        """Test that function returns the first match when workflow exists in multiple workers."""
        # Arrange
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock first worker with the target workflow
        first_workflow_def = MagicMock()
        first_workflow_def.name = "TestWorkflow"
        first_workflow_def.task_queue = "first-queue"

        first_worker = MagicMock()
        first_worker.worker_name = "first-worker"
        first_worker.workflows = [first_workflow_def]

        # Mock second worker with same workflow name (should not be used)
        second_workflow_def = MagicMock()
        second_workflow_def.name = "TestWorkflow"
        second_workflow_def.task_queue = "second-queue"

        second_worker = MagicMock()
        second_worker.worker_name = "second-worker"
        second_worker.workflows = [second_workflow_def]

        mock_storage.list_active_workers = AsyncMock(return_value=[first_worker, second_worker])

        # Act
        result = await get_workflow_queue("TestWorkflow")

        # Assert - should return first match
        assert result == "first-queue"
        mock_storage.list_active_workers.assert_called_once()


class TestWorkflowMetadataMcpFields:
    """Test MCP field extraction in workflow metadata."""

    def test_extract_metadata_with_mcp_decorator(self) -> None:
        """Test extracting metadata from MCP-decorated workflow."""
        # Mock workflow class with MCP attributes
        mock_workflow = MagicMock()
        mock_workflow.__temporal_workflow_definition.name = "test-workflow"
        mock_workflow.__module__ = "test.module"
        mock_workflow.__exposed__ = True
        mock_workflow.__description__ = "Test MCP workflow"

        with (
            patch("awa.core.utils.workflow_metadata._extract_run_method_parameters", return_value=[]),
            patch("awa.core.utils.workflow_metadata._extract_run_method_parameter_info", return_value=[]),
        ):
            metadata = _extract_workflow_metadata(mock_workflow)

            assert metadata.exposed is True
            assert metadata.description == "Test MCP workflow"

    def test_extract_metadata_without_mcp_decorator(self) -> None:
        """Test extracting metadata from non-MCP workflow."""
        # Mock workflow class without MCP attributes
        mock_workflow = MagicMock()
        mock_workflow.__temporal_workflow_definition.name = "test-workflow"
        mock_workflow.__module__ = "test.module"
        # MCP attributes don't exist
        del mock_workflow.__exposed__
        del mock_workflow.__description__

        with (
            patch("awa.core.utils.workflow_metadata._extract_run_method_parameters", return_value=[]),
            patch("awa.core.utils.workflow_metadata._extract_run_method_parameter_info", return_value=[]),
        ):
            metadata = _extract_workflow_metadata(mock_workflow)

            assert metadata.exposed is False
            assert metadata.description is None


class TestParameterMetadataEnhancements:
    """Test parameter metadata extraction with field descriptions."""

    def test_format_workflow_parameters_with_field_metadata(self) -> None:
        """Test that field metadata is preserved in parameter schema."""
        from unittest.mock import Mock

        from pydantic import BaseModel, Field

        # Create a test Pydantic model with field metadata
        class TestInput(BaseModel):
            name: str = Field(description="The person's name", title="Name")
            age: int = Field(description="The person's age", title="Age", ge=0)

        # Mock metadata with the TestInput model
        metadata = WorkflowMetadata(
            name="test-workflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=[],
            parameter_info=[ParameterInfo(name="workflow_input", type_str="TestInput")],
        )

        # Mock the module import to return our TestInput
        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_module.TestInput = TestInput
            mock_import.return_value = mock_module
            mock_module.TestInput = TestInput

            # Format parameters
            schema = format_workflow_parameters(metadata)

            # Verify the schema includes field metadata
            assert "properties" in schema
            assert "name" in schema["properties"]
            assert schema["properties"]["name"]["description"] == "The person's name"
            assert schema["properties"]["name"]["title"] == "Name"
            assert "age" in schema["properties"]
            assert schema["properties"]["age"]["description"] == "The person's age"
            assert schema["properties"]["age"]["title"] == "Age"


class TestNullableWorkflowParameters:
    """Test detection and handling of nullable workflow parameters."""

    def test_format_workflow_parameters_detects_nullable_with_pipe_none(self) -> None:
        """Test that nullable parameters with | None are detected correctly."""
        from unittest.mock import Mock

        from pydantic import BaseModel, Field

        class TestInput(BaseModel):
            name: str = Field(description="Test name")

        # Mock metadata with nullable parameter using | None pattern
        metadata = WorkflowMetadata(
            name="test-workflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=[],
            parameter_info=[ParameterInfo(name="workflow_input", type_str="TestInput | None")],
        )

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_module.TestInput = TestInput
            mock_import.return_value = mock_module

            schema = format_workflow_parameters(metadata)

            # Verify x-nullable-input is True
            assert "x-nullable-input" in schema
            assert schema["x-nullable-input"] is True
            # Verify schema structure is preserved
            assert "properties" in schema
            assert "name" in schema["properties"]

    def test_format_workflow_parameters_detects_nullable_with_skipjsonschema(self) -> None:
        """Test that nullable parameters with SkipJsonSchema[None] are detected."""
        from unittest.mock import Mock

        from pydantic import BaseModel, Field

        class TestInput(BaseModel):
            target_dir: str = Field(description="Target directory")
            agent_provider: str = Field(default="claude", description="Agent provider")

        # Mock metadata with nullable parameter using SkipJsonSchema[None] pattern
        metadata = WorkflowMetadata(
            name="test-workflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=[],
            parameter_info=[ParameterInfo(name="workflow_input", type_str="TestInput | SkipJsonSchema[None]")],
        )

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_module.TestInput = TestInput
            mock_import.return_value = mock_module

            schema = format_workflow_parameters(metadata)

            # Verify x-nullable-input is True
            assert "x-nullable-input" in schema
            assert schema["x-nullable-input"] is True
            # Verify schema structure is preserved
            assert "properties" in schema
            assert "target_dir" in schema["properties"]
            assert "agent_provider" in schema["properties"]

    def test_format_workflow_parameters_non_nullable(self) -> None:
        """Test that non-nullable parameters don't set x-nullable-input."""
        from unittest.mock import Mock

        from pydantic import BaseModel, Field

        class TestInput(BaseModel):
            name: str = Field(description="Test name")

        # Mock metadata with required (non-nullable) parameter
        metadata = WorkflowMetadata(
            name="test-workflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=[],
            parameter_info=[ParameterInfo(name="workflow_input", type_str="TestInput")],
        )

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_module.TestInput = TestInput
            mock_import.return_value = mock_module

            schema = format_workflow_parameters(metadata)

            # Verify x-nullable-input is NOT present or is False
            assert "x-nullable-input" not in schema

    def test_format_workflow_parameters_preserves_schema_for_nullable(self) -> None:
        """Test that schema structure is preserved for nullable inputs."""
        from unittest.mock import Mock

        from pydantic import BaseModel, Field

        class ComplexInput(BaseModel):
            required_field: str = Field(description="Required field")
            optional_field: str | None = Field(None, description="Optional field")
            number_field: int = Field(default=42, description="Number field")

        # Mock metadata with nullable parameter
        metadata = WorkflowMetadata(
            name="test-workflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=[],
            parameter_info=[ParameterInfo(name="workflow_input", type_str="ComplexInput | None")],
        )

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_module.ComplexInput = ComplexInput
            mock_import.return_value = mock_module

            schema = format_workflow_parameters(metadata)

            # Verify x-nullable-input is True
            assert schema.get("x-nullable-input") is True

            # Verify properties are correctly extracted from Pydantic model
            assert "properties" in schema
            assert "required_field" in schema["properties"]
            assert "optional_field" in schema["properties"]
            assert "number_field" in schema["properties"]

            # Verify descriptions are preserved
            assert schema["properties"]["required_field"]["description"] == "Required field"
            assert schema["properties"]["optional_field"]["description"] == "Optional field"
            assert schema["properties"]["number_field"]["description"] == "Number field"

    def test_format_workflow_parameters_multiple_params_one_nullable(self) -> None:
        """Test handling of multiple parameters where one is nullable."""
        from unittest.mock import Mock

        # Mock metadata with multiple parameters (edge case but worth testing)
        metadata = WorkflowMetadata(
            name="test-workflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=[],
            parameter_info=[
                ParameterInfo(name="required_param", type_str="str"),
                ParameterInfo(name="optional_param", type_str="str | None"),
            ],
        )

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_import.return_value = mock_module

            schema = format_workflow_parameters(metadata)

            # If ANY parameter is nullable, mark the whole input as nullable
            assert schema.get("x-nullable-input") is True

    def test_format_workflow_parameters_skipjsonschema_reversed_order(self) -> None:
        """Test handling of SkipJsonSchema[None] in reversed order."""
        from unittest.mock import Mock

        from pydantic import BaseModel

        class TestInput(BaseModel):
            name: str

        # Mock metadata with reversed union order (edge case)
        metadata = WorkflowMetadata(
            name="test-workflow",
            class_name="TestWorkflow",
            module="test.module",
            parameters=[],
            parameter_info=[ParameterInfo(name="workflow_input", type_str="SkipJsonSchema[None] | TestInput")],
        )

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_module.TestInput = TestInput
            mock_import.return_value = mock_module

            schema = format_workflow_parameters(metadata)

            # Verify x-nullable-input is True
            assert schema.get("x-nullable-input") is True
            # Verify schema is still generated correctly
            assert "properties" in schema
