"""Unit tests for shared workflow endpoints."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from awa.core.api.routes.shared.workflows import get_workflow_run, list_workflows, run_workflow, workflow_runs
from awa.core.constants import TASK_QUEUE
from awa.core.models.api import (
    WorkflowDefinition,
    WorkflowInfo,
    WorkflowListResponse,
    WorkflowRun,
    WorkflowRunPayload,
    WorkflowRunStatus,
)
from awa.core.utils.workflow_metadata import ParameterInfo, WorkflowMetadata
from awa.sdk.models.exceptions.invalid_input_error import InvalidInputApplicationError


class TestSharedWorkflows:
    """Test cases for the shared workflows function (now using list_workflows)."""

    @pytest.mark.asyncio
    @patch("awa.core.api.auth.EnvConfig.get_env_config")
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_list_workflows_success(
        self,
        mock_format_metadata: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
        mock_env_config: MagicMock,
    ) -> None:
        """Test successful workflow listing."""
        # Arrange
        mock_config = MagicMock()
        mock_config.public_auth_mode = "none"
        mock_env_config.return_value = mock_config

        mock_metadata = [
            WorkflowMetadata(
                name="TestWorkflow1",
                class_name="TestWorkflow1",
                module="test.module1",
                parameters=["param1", "param2"],
                parameter_info=[
                    ParameterInfo(name="param1", type_str="str"),
                    ParameterInfo(name="param2", type_str="int"),
                ],
                exposed=True,
            ),
            WorkflowMetadata(
                name="TestWorkflow2",
                class_name="TestWorkflow2",
                module="test.module2",
                parameters=["input_data"],
                parameter_info=[
                    ParameterInfo(name="input_data", type_str="TestParams"),
                ],
                exposed=True,
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Mock registry storage
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert isinstance(result, WorkflowListResponse)
        assert len(result.workflows) == 2

        # Check workflow
        first_workflow = result.workflows[0]
        assert isinstance(first_workflow, WorkflowInfo)
        assert first_workflow.name == "TestWorkflow1"
        assert first_workflow.module == "test.module1"
        assert first_workflow.parameters == {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }
        assert first_workflow.queues == [TASK_QUEUE]

    @pytest.mark.asyncio
    @patch("awa.core.api.auth.EnvConfig.get_env_config")
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_list_workflows_empty_list(
        self,
        mock_format_metadata: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
        mock_env_config: MagicMock,
    ) -> None:
        """Test workflow listing with empty results."""
        # Arrange
        mock_config = MagicMock()
        mock_config.public_auth_mode = "none"
        mock_env_config.return_value = mock_config

        mock_get_metadata.return_value = []
        mock_format_metadata.return_value = ""

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert isinstance(result, WorkflowListResponse)
        assert len(result.workflows) == 0
        assert result.workflows == []

    @pytest.mark.asyncio
    @patch("awa.core.api.auth.EnvConfig.get_env_config")
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_list_workflows_no_parameters(
        self,
        mock_format_metadata: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
        mock_env_config: MagicMock,
    ) -> None:
        """Test workflow listing with workflows that have no parameters."""
        # Arrange
        mock_config = MagicMock()
        mock_config.public_auth_mode = "none"
        mock_env_config.return_value = mock_config

        mock_metadata = [
            WorkflowMetadata(
                name="NoParamWorkflow",
                class_name="NoParamWorkflow",
                module="test.module",
                parameters=[],
                parameter_info=[],
                exposed=True,
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_format_metadata.return_value = {}

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert isinstance(result, WorkflowListResponse)
        assert len(result.workflows) == 1
        workflow = result.workflows[0]
        assert workflow.name == "NoParamWorkflow"
        assert workflow.parameters == {}
        assert workflow.queues == [TASK_QUEUE]

    @pytest.mark.asyncio
    @patch("awa.core.api.auth.EnvConfig.get_env_config")
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_list_workflows_discovery_failure(
        self,
        mock_format_metadata: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
        mock_env_config: MagicMock,
    ) -> None:
        """Test handling of workflow discovery failures."""
        # Arrange
        mock_config = MagicMock()
        mock_config.public_auth_mode = "none"
        mock_env_config.return_value = mock_config

        mock_get_metadata.side_effect = Exception("Discovery failed")
        mock_format_metadata.return_value = ""

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])
        # Act - list_workflows doesn't raise exception on discovery failure
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert - should return empty list when discovery fails
        assert isinstance(result, WorkflowListResponse)
        assert len(result.workflows) == 0

    @pytest.mark.asyncio
    @patch("awa.core.api.auth.EnvConfig.get_env_config")
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_list_workflows_runtime_error(
        self,
        mock_format_metadata: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
        mock_env_config: MagicMock,
    ) -> None:
        """Test handling of runtime errors during workflow listing."""
        # Arrange
        mock_config = MagicMock()
        mock_config.public_auth_mode = "none"
        mock_env_config.return_value = mock_config

        mock_get_metadata.side_effect = RuntimeError("Runtime error occurred")
        mock_format_metadata.return_value = {}

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])
        # Act - list_workflows doesn't raise exception on runtime error
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert - should return empty list when discovery fails
        assert isinstance(result, WorkflowListResponse)
        assert len(result.workflows) == 0

    @pytest.mark.asyncio
    @patch("awa.core.api.auth.EnvConfig.get_env_config")
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_list_workflows_response_structure(
        self,
        mock_format_metadata: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
        mock_env_config: MagicMock,
    ) -> None:
        """Test that the response structure matches the expected format."""
        # Arrange
        mock_config = MagicMock()
        mock_config.public_auth_mode = "none"
        mock_env_config.return_value = mock_config

        mock_metadata = [
            WorkflowMetadata(
                name="SampleWorkflow",
                class_name="SampleWorkflow",
                module="sample.module",
                parameters=["input1", "input2"],
                exposed=True,
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert isinstance(result, WorkflowListResponse)
        assert hasattr(result, "workflows")
        assert isinstance(result.workflows, list)

        if result.workflows:
            workflow = result.workflows[0]
            assert hasattr(workflow, "name")
            assert hasattr(workflow, "module")
            assert hasattr(workflow, "parameters")
            assert isinstance(workflow.parameters, dict)

    @pytest.mark.asyncio
    @patch("awa.core.api.auth.EnvConfig.get_env_config")
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_list_workflows_with_complex_parameters(
        self,
        mock_format_metadata: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
        mock_env_config: MagicMock,
    ) -> None:
        """Test workflow listing with complex parameter names."""
        # Arrange
        mock_config = MagicMock()
        mock_config.public_auth_mode = "none"
        mock_env_config.return_value = mock_config

        mock_metadata = [
            WorkflowMetadata(
                name="ComplexWorkflow",
                class_name="ComplexWorkflow",
                module="complex.workflow.module",
                parameters=["request_data", "config_settings", "user_context", "optional_flags"],
                parameter_info=[
                    ParameterInfo(name="request_data", type_str="RequestData"),
                    ParameterInfo(name="config_settings", type_str="ConfigSettings"),
                    ParameterInfo(name="user_context", type_str="UserContext"),
                    ParameterInfo(name="optional_flags", type_str="OptionalFlags"),
                ],
                exposed=True,
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert isinstance(result, WorkflowListResponse)
        assert len(result.workflows) == 1
        workflow = result.workflows[0]
        assert workflow.name == "ComplexWorkflow"
        assert workflow.module == "complex.workflow.module"
        assert "type" in workflow.parameters
        assert workflow.parameters["properties"]["name"]["type"] == "string"

    @pytest.mark.asyncio
    @patch("awa.core.api.auth.EnvConfig.get_env_config")
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_list_workflows_metadata_conversion(
        self,
        mock_format_metadata: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
        mock_env_config: MagicMock,
    ) -> None:
        """Test proper conversion from WorkflowMetadata to WorkflowInfo."""
        # Arrange
        mock_config = MagicMock()
        mock_config.public_auth_mode = "none"
        mock_env_config.return_value = mock_config

        mock_metadata = [
            WorkflowMetadata(
                name="ConversionTest",
                class_name="ConversionTestWorkflow",
                module="conversion.test.module",
                parameters=["test_param"],
                parameter_info=[
                    ParameterInfo(name="test_param", type_str="TestParamType"),
                ],
                exposed=True,
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert isinstance(result, WorkflowListResponse)
        workflow_info = result.workflows[0]

        # Verify all fields are properly converted
        assert workflow_info.name == mock_metadata[0].name
        assert workflow_info.module == mock_metadata[0].module

        # Verify types are correct
        assert isinstance(workflow_info.name, str)
        assert isinstance(workflow_info.module, str)
        assert isinstance(workflow_info.parameters, dict)

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_list_workflows_mixed_parameter_info(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test parameter formatting with mix of typed and untyped parameters."""
        # Arrange
        mock_metadata = [
            WorkflowMetadata(
                name="MixedWorkflow",
                class_name="MixedWorkflow",
                module="mixed.module",
                parameters=["param1", "param2", "param3"],
                parameter_info=[
                    ParameterInfo(name="param1", type_str="str"),
                    ParameterInfo(name="param2", type_str=None),  # No type info
                    ParameterInfo(name="param3", type_str="CustomType"),
                ],
                exposed=True,
            ),
        ]
        mock_get_metadata.return_value = mock_metadata

        # Mock the format_workflow_parameters to return expected dict format
        mock_format_params.return_value = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "string"},
                "param3": {"type": "string"},
            },
        }

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert isinstance(result, WorkflowListResponse)
        assert len(result.workflows) == 1
        workflow = result.workflows[0]
        assert workflow.name == "MixedWorkflow"
        assert workflow.parameters == {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "string"},
                "param3": {"type": "string"},
            },
        }


class TestUnifiedWorkflowList:
    """Test unified workflow list endpoint."""

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_combined_workflows(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test combining core and registry workflows."""
        # Mock core workflows
        mock_get_metadata.return_value = [
            WorkflowMetadata(
                name="CoreWorkflow",
                class_name="CoreWorkflow",
                module="awa.workflows.core",
                parameters=["input"],
                parameter_info=[ParameterInfo(name="input", type_str="str")],
                exposed=True,
            ),
        ]

        # Mock format_workflow_parameters to return a dict
        mock_format_params.return_value = {"type": "object", "properties": {"input": {"type": "string"}}}

        # Mock registry storage
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance

        # Mock registry workflows
        mock_worker = MagicMock()
        mock_worker.worker_name = "test-worker"
        mock_worker.workflows = [
            WorkflowDefinition(
                name="ExternalWorkflow",
                task_queue="external-queue",
                input_schema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Input message"},
                        "count": {"type": "integer", "default": 1},
                    },
                },
            ),
        ]
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[mock_worker])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert isinstance(result, WorkflowListResponse)
        assert len(result.workflows) == 2

        # Check core workflow
        core_workflow = next((w for w in result.workflows if w.name == "CoreWorkflow"), None)
        assert core_workflow is not None
        assert core_workflow.module == "awa.workflows.core"
        assert core_workflow.queues == [TASK_QUEUE]
        assert core_workflow.parameters == {"type": "object", "properties": {"input": {"type": "string"}}}

        # Check external workflow
        external_workflow = next((w for w in result.workflows if w.name == "ExternalWorkflow"), None)
        assert external_workflow is not None
        assert external_workflow.module == "external"
        assert external_workflow.queues == ["external-queue"]
        # Parameters should be the input_schema dict
        assert external_workflow.parameters == {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Input message"},
                "count": {"type": "integer", "default": 1},
            },
        }

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_task_queue_filtering(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test filtering by task queue."""
        # Mock workflows with different queues
        mock_get_metadata.return_value = [
            WorkflowMetadata(
                name="DefaultQueueWorkflow",
                class_name="DefaultQueueWorkflow",
                module="awa.workflows.default",
                parameters=[],
                parameter_info=[],
                exposed=True,
            ),
        ]

        # Mock format_workflow_parameters
        mock_format_params.return_value = {"type": "object", "properties": {}}

        # Mock registry storage
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance

        mock_worker = MagicMock()
        mock_worker.workflows = [
            WorkflowDefinition(
                name="CustomQueueWorkflow",
                task_queue="custom-queue",
                input_schema={},
            ),
        ]
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[mock_worker])

        # Test filter for default queue
        result = await list_workflows(current_user=None, task_queue=TASK_QUEUE)
        assert len(result.workflows) == 1, f"Missed for {TASK_QUEUE}"
        assert result.workflows[0].name == "DefaultQueueWorkflow"

        # Test filter for custom queue
        result = await list_workflows(current_user=None, task_queue="custom-queue")
        assert len(result.workflows) == 1
        assert result.workflows[0].name == "CustomQueueWorkflow"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    async def test_graceful_partial_failure(
        self,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test endpoint continues when one data source fails."""
        # Core discovery fails
        mock_get_metadata.side_effect = Exception("Discovery failed")

        # Mock registry storage
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance

        # Registry works
        mock_worker = MagicMock()
        mock_worker.workflows = [
            WorkflowDefinition(name="RegistryWorkflow", task_queue="queue", input_schema={}),
        ]
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[mock_worker])

        # Should not raise exception
        result = await list_workflows(current_user=None, task_queue=None)

        assert len(result.workflows) == 1
        assert result.workflows[0].name == "RegistryWorkflow"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    async def test_empty_input_schema(self, mock_get_storage: MagicMock, mock_get_metadata: MagicMock) -> None:
        """Test handling of workflows with empty input schema."""
        mock_get_metadata.return_value = []

        # Mock registry storage
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance

        mock_worker = MagicMock()
        mock_worker.workflows = [
            WorkflowDefinition(
                name="NoInputWorkflow",
                task_queue="test-queue",
                input_schema={},  # Empty schema
            ),
        ]
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[mock_worker])

        result = await list_workflows(current_user=None, task_queue=None)

        assert len(result.workflows) == 1
        workflow = result.workflows[0]
        assert workflow.name == "NoInputWorkflow"
        assert workflow.parameters == {
            "type": "object",
            "properties": {},
        }  # Should have empty object schema with auto-added properties

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_queue_information(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test that queue information is properly included."""
        # Mock core workflow
        mock_get_metadata.return_value = [
            WorkflowMetadata(
                name="CoreWorkflow",
                class_name="CoreWorkflow",
                module="awa.workflows.test",
                parameters=[],
                parameter_info=[],
                exposed=True,
            ),
        ]

        # Mock format_workflow_parameters
        mock_format_params.return_value = {"type": "object", "properties": {}}

        # Mock registry storage
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance

        # Mock external workflow
        mock_worker = MagicMock()
        mock_worker.workflows = [
            WorkflowDefinition(
                name="ExternalWorkflow",
                task_queue="custom-queue",
                input_schema={},
            ),
        ]
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[mock_worker])

        result = await list_workflows(current_user=None, task_queue=None)

        # Check core workflow has default queue
        core_workflow = next((w for w in result.workflows if w.name == "CoreWorkflow"), None)
        assert core_workflow is not None
        assert core_workflow.queues == [TASK_QUEUE]

        # Check external workflow has custom queue
        external_workflow = next((w for w in result.workflows if w.name == "ExternalWorkflow"), None)
        assert external_workflow is not None
        assert external_workflow.queues == ["custom-queue"]

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_registry_failure_continues(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test that core workflows are returned even if registry fails."""
        # Core workflows work
        mock_get_metadata.return_value = [
            WorkflowMetadata(
                name="CoreWorkflow",
                class_name="CoreWorkflow",
                module="awa.workflows.core",
                parameters=["input"],
                parameter_info=[],
                exposed=True,
            ),
        ]
        # Mock format_workflow_parameters to return a dict
        mock_format_params.return_value = {"type": "object", "properties": {"input": {"type": "string"}}}

        # Mock registry storage that fails
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(side_effect=Exception("Registry error"))

        # Should not raise exception
        result = await list_workflows(current_user=None, task_queue=None)

        assert len(result.workflows) == 1
        assert result.workflows[0].name == "CoreWorkflow"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_sorting_by_module_and_name(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test that workflows are sorted by module then name."""
        # Mock workflows in non-sorted order
        mock_get_metadata.return_value = [
            WorkflowMetadata(
                name="ZWorkflow",
                class_name="ZWorkflow",
                module="awa.workflows.z",
                parameters=[],
                parameter_info=[],
                exposed=True,
            ),
            WorkflowMetadata(
                name="AWorkflow",
                class_name="AWorkflow",
                module="awa.workflows.a",
                parameters=[],
                parameter_info=[],
                exposed=True,
            ),
        ]
        # Mock format_workflow_parameters to return empty dict
        mock_format_params.return_value = {"type": "object", "properties": {}}

        # Mock registry storage
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance

        mock_worker = MagicMock()
        mock_worker.workflows = [
            WorkflowDefinition(name="BExternal", task_queue="queue", input_schema={}),
            WorkflowDefinition(name="AExternal", task_queue="queue", input_schema={}),
        ]
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[mock_worker])

        result = await list_workflows(current_user=None, task_queue=None)

        # Check sorting
        assert len(result.workflows) == 4
        # Core workflows come first sorted by module (awa.workflows.a before awa.workflows.z)
        assert result.workflows[0].name == "AWorkflow"
        assert result.workflows[0].module == "awa.workflows.a"
        assert result.workflows[1].name == "ZWorkflow"
        assert result.workflows[1].module == "awa.workflows.z"
        # External workflows come after, sorted by name (AExternal before BExternal)
        assert result.workflows[2].name == "AExternal"
        assert result.workflows[2].module == "external"
        assert result.workflows[3].name == "BExternal"
        assert result.workflows[3].module == "external"

    @pytest.mark.asyncio
    async def test_workflows_run_direct_success(
        self,
    ) -> None:
        """Test calling the list workflow runs function."""
        # Arrange
        # Mock successful runs call
        mock_client = AsyncMock()

        run_id = str(uuid.uuid4())
        duration = timedelta(seconds=30)
        started = datetime.now(UTC) - duration
        run = WorkflowRun(
            type="Mock Workflow",
            id=run_id,
            workflow_id="workflow-" + run_id,
            status=WorkflowRunStatus.RUNNING,
            started=started,
            duration=str(duration),
            monitor=f"mockurl:1234/namespaces/default/workflows/20250101_123456_12345/{run_id}",
        )
        run_list = []
        run_list.append(run)
        mock_client.list_workflow_runs.return_value = run_list

        response = await workflow_runs(current_user=None, client=mock_client)

        assert response.workflows == run_list

    @pytest.mark.asyncio
    async def test_start_workflow_direct_success(
        self,
    ) -> None:
        """Test calling the start workflow function."""
        # Mock successful runs call
        mock_client = AsyncMock()

        mock_client.start_workflow.return_value = "success"

        response = await run_workflow(
            WorkflowRunPayload(name="awa-test-workflow", input="{ 'test': 'value' }"),
            current_user=None,
            client=mock_client,
        )

        assert response["data"] == "success"

    @pytest.mark.asyncio
    async def test_run_workflow_invalid_json_input(
        self,
    ) -> None:
        """Test that invalid JSON input returns 400 status with correct error message."""
        # Mock client that raises InvalidInputApplicationError
        mock_client = AsyncMock()
        mock_client.start_workflow.side_effect = InvalidInputApplicationError("Invalid JSON format in input field")

        # Test that HTTPException is raised with correct status and message
        with pytest.raises(HTTPException) as exc_info:
            await run_workflow(
                WorkflowRunPayload(name="awa-test-workflow", input="{invalid json"),
                current_user=None,
                client=mock_client,
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid JSON format in input field"

    @pytest.mark.asyncio
    async def test_run_workflow_other_error_returns_500(
        self,
    ) -> None:
        """Test that other errors return 500 status."""
        # Mock client that raises a generic exception
        mock_client = AsyncMock()
        mock_client.start_workflow.side_effect = Exception("Some other error")

        # Test that HTTPException is raised with 500 status
        with pytest.raises(HTTPException) as exc_info:
            await run_workflow(
                WorkflowRunPayload(name="awa-test-workflow", input='{"valid": "json"}'),
                current_user=None,
                client=mock_client,
            )

        assert exc_info.value.status_code == 500
        assert "Workflow execution failed" in exc_info.value.detail


class TestGetWorkflowRun:
    """Test cases for get_workflow_run endpoint."""

    @pytest.mark.asyncio
    async def test_get_workflow_run_success(self) -> None:
        """Test successful retrieval of a workflow run."""
        # Arrange
        mock_client = AsyncMock()

        run_id = str(uuid.uuid4())
        duration = timedelta(seconds=30)
        started = datetime.now(UTC) - duration

        mock_workflow_run = WorkflowRun(
            type="TestWorkflow",
            id=run_id,
            workflow_id="workflow-" + run_id,
            status=WorkflowRunStatus.RUNNING,
            started=started,
            duration=str(duration),
            monitor=f"https://temporal.example.com/namespaces/default/workflows/{run_id}",
        )
        mock_client.get_workflow_run.return_value = mock_workflow_run

        current_user = {"sub": "test-user"}

        # Act
        result = await get_workflow_run(run_id, current_user, mock_client)

        # Assert
        assert result.id == run_id
        assert result.type == "TestWorkflow"
        assert result.status == WorkflowRunStatus.RUNNING
        mock_client.get_workflow_run.assert_called_once_with(run_id)

    @pytest.mark.asyncio
    async def test_get_workflow_run_not_found(self) -> None:
        """Test retrieval when workflow run is not found."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get_workflow_run.return_value = None

        current_user = {"sub": "test-user"}
        run_id = str(uuid.uuid4())

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_workflow_run(run_id, current_user, mock_client)

        assert exc_info.value.status_code == 404
        assert f"Workflow run {run_id} not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_workflow_run_temporal_error(self) -> None:
        """Test error handling when Temporal client fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get_workflow_run.side_effect = Exception("Connection failed")

        current_user = {"sub": "test-user"}
        run_id = str(uuid.uuid4())

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_workflow_run(run_id, current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Failed to get workflow run" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_workflow_run_with_anonymous_user(self) -> None:
        """Test retrieval with anonymous user."""
        # Arrange
        mock_client = AsyncMock()

        run_id = str(uuid.uuid4())
        mock_workflow_run = WorkflowRun(
            type="TestWorkflow",
            id=run_id,
            workflow_id="workflow-" + run_id,
            status=WorkflowRunStatus.RUNNING,
            started=datetime.now(UTC),
            duration="0:00:30",
            monitor=f"https://temporal.example.com/namespaces/default/workflows/{run_id}",
        )
        mock_client.get_workflow_run.return_value = mock_workflow_run

        current_user = {}  # No 'sub' field

        # Act
        result = await get_workflow_run(run_id, current_user, mock_client)

        # Assert
        assert result.id == run_id
        mock_client.get_workflow_run.assert_called_once_with(run_id)

    @pytest.mark.asyncio
    async def test_get_workflow_run_client_query_error(self) -> None:
        """Test error handling when get_workflow_run query fails."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get_workflow_run.side_effect = Exception("Query failed")

        current_user = {"sub": "test-user"}
        run_id = str(uuid.uuid4())

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_workflow_run(run_id, current_user, mock_client)

        assert exc_info.value.status_code == 500
        assert "Failed to get workflow run" in str(exc_info.value.detail)


class TestAPIFiltering:
    """Test cases for API filtering of exposed workflows."""

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_filters_non_exposed_core_workflows(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test that list_workflows filters out non-exposed core workflows."""
        # Arrange - create metadata with mixed exposed/non-exposed workflows
        exposed_metadata = WorkflowMetadata(
            name="ExposedWorkflow",
            class_name="ExposedWorkflow",
            module="awa.workflows.core",
            parameters=["input"],
            parameter_info=[ParameterInfo(name="input", type_str="str")],
            exposed=True,
            description="This workflow is exposed",
        )
        # Add the __exposed__ attribute to simulate decorator behavior
        exposed_metadata.__exposed__ = True
        exposed_metadata.__description__ = "This workflow is exposed"

        non_exposed_metadata = WorkflowMetadata(
            name="InternalWorkflow",
            class_name="InternalWorkflow",
            module="awa.workflows.core",
            parameters=["input"],
            parameter_info=[ParameterInfo(name="input", type_str="str")],
            exposed=False,
            description=None,
        )
        # Non-exposed workflow doesn't have the attribute
        non_exposed_metadata.__exposed__ = False

        mock_get_metadata.return_value = [exposed_metadata, non_exposed_metadata]
        mock_format_params.return_value = {"type": "object", "properties": {"input": {"type": "string"}}}

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert - only exposed workflow should be in results
        assert len(result.workflows) == 1
        assert result.workflows[0].name == "ExposedWorkflow"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_exposed_workflows_appear_in_response(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test that exposed workflows appear in API response."""
        # Arrange
        exposed_metadata = WorkflowMetadata(
            name="ExposedWorkflow",
            class_name="ExposedWorkflow",
            module="awa.workflows.core",
            parameters=[],
            parameter_info=[],
            exposed=True,
            description="Exposed workflow description",
        )
        exposed_metadata.__exposed__ = True
        exposed_metadata.__description__ = "Exposed workflow description"

        mock_get_metadata.return_value = [exposed_metadata]
        mock_format_params.return_value = {"type": "object", "properties": {}}

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert len(result.workflows) == 1
        assert result.workflows[0].name == "ExposedWorkflow"
        assert result.workflows[0].module == "awa.workflows.core"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_external_worker_workflows_not_filtered(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test that external worker workflows are NOT filtered (they manage their own exposure)."""
        # Arrange - no core workflows
        mock_get_metadata.return_value = []
        mock_format_params.return_value = {"type": "object", "properties": {}}

        # Mock registry storage with external workflows (no exposed flag)
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance

        mock_worker = MagicMock()
        mock_worker.worker_name = "external-worker"
        mock_worker.workflows = [
            WorkflowDefinition(
                name="ExternalWorkflow1",
                task_queue="external-queue",
                input_schema={"type": "object", "properties": {}},
            ),
            WorkflowDefinition(
                name="ExternalWorkflow2",
                task_queue="external-queue",
                input_schema={"type": "object", "properties": {}},
            ),
        ]
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[mock_worker])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert - both external workflows should appear (not filtered by exposure)
        assert len(result.workflows) == 2
        assert result.workflows[0].name == "ExternalWorkflow1"
        assert result.workflows[1].name == "ExternalWorkflow2"
        assert result.workflows[0].module == "external"
        assert result.workflows[1].module == "external"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.workflows.get_workflow_metadata")
    @patch("awa.core.api.routes.shared.workflows.get_registry_storage")
    @patch("awa.core.api.routes.shared.workflows.format_workflow_parameters")
    async def test_description_field_populated_correctly(
        self,
        mock_format_params: MagicMock,
        mock_get_storage: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test that description field is populated correctly in responses."""
        # Arrange
        with_description = WorkflowMetadata(
            name="WorkflowWithDescription",
            class_name="WorkflowWithDescription",
            module="awa.workflows.core",
            parameters=[],
            parameter_info=[],
            exposed=True,
            description="This is a test description",
        )
        with_description.__exposed__ = True
        with_description.__description__ = "This is a test description"

        without_description = WorkflowMetadata(
            name="WorkflowWithoutDescription",
            class_name="WorkflowWithoutDescription",
            module="awa.workflows.core",
            parameters=[],
            parameter_info=[],
            exposed=True,
            description=None,
        )
        without_description.__exposed__ = True
        without_description.__description__ = None

        mock_get_metadata.return_value = [with_description, without_description]
        mock_format_params.return_value = {"type": "object", "properties": {}}

        # Mock registry storage to return empty list
        mock_storage_instance = MagicMock()
        mock_get_storage.return_value = mock_storage_instance
        mock_storage_instance.list_active_workers = AsyncMock(return_value=[])

        # Act
        result = await list_workflows(current_user=None, task_queue=None)

        # Assert
        assert len(result.workflows) == 2

        # Find workflows by name
        workflow_with_desc = next(w for w in result.workflows if w.name == "WorkflowWithDescription")
        workflow_without_desc = next(w for w in result.workflows if w.name == "WorkflowWithoutDescription")

        assert workflow_with_desc.description == "This is a test description"
        assert workflow_without_desc.description is None
