"""Unit tests for registry API models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from awa.core.models.api import (
    ActivityDefinition,
    StoredWorkerRegistration,
    WorkerRegistration,
    WorkerRegistrationResponse,
    WorkerRegistrationSummary,
    WorkflowDefinition,
    WorkflowRegistryResponse,
)


class TestWorkflowDefinition:
    """Test cases for WorkflowDefinition model."""

    def test_workflow_definition_initialization_with_valid_data(self) -> None:
        """Test WorkflowDefinition initialization with valid data."""
        # Arrange & Act
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
        )

        # Assert
        assert workflow.name == "TestWorkflow"
        assert workflow.task_queue == "test-queue"
        assert workflow.input_schema == {"type": "object", "properties": {"message": {"type": "string"}}}

    def test_workflow_definition_missing_required_fields(self) -> None:
        """Test that WorkflowDefinition requires all fields."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue")
        error = exc_info.value
        assert "input_schema" in str(error)
        assert "Field required" in str(error)

    def test_workflow_definition_empty_name_validation(self) -> None:
        """Test that WorkflowDefinition rejects empty name."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(
                name="",
                task_queue="test-queue",
                input_schema={"type": "object"},
            )
        error = exc_info.value
        assert "name" in str(error)

    def test_workflow_definition_json_serialization(self) -> None:
        """Test WorkflowDefinition JSON serialization."""
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object"},
        )
        json_str = workflow.model_dump_json()
        assert "TestWorkflow" in json_str
        assert "test-queue" in json_str


class TestWorkflowDefinitionValidation:
    """Test JSON Schema validation for WorkflowDefinition."""

    def test_valid_schema_passes(self) -> None:
        """Test that valid JSON Schema passes validation."""
        valid_schema = {
            "type": "object",
            "properties": {"message": {"type": "string"}, "count": {"type": "integer"}},
            "required": ["message"],
        }

        workflow = WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema=valid_schema)

        assert workflow.input_schema == valid_schema

    def test_empty_schema_converts_to_basic_object(self) -> None:
        """Test that empty schema gets converted to basic object schema."""
        workflow = WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema={})

        expected_schema = {"type": "object", "properties": {}}
        assert workflow.input_schema == expected_schema

    def test_missing_type_object_fails(self) -> None:
        """Test that schema without type: object fails validation."""
        invalid_schema = {"properties": {"message": {"type": "string"}}}

        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema=invalid_schema)

        error = exc_info.value
        assert "input_schema must have 'type': 'object'" in str(error)

    def test_wrong_type_fails(self) -> None:
        """Test that schema with wrong type fails validation."""
        invalid_schema = {"type": "string", "properties": {"message": {"type": "string"}}}

        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema=invalid_schema)

        error = exc_info.value
        assert "input_schema must have 'type': 'object'" in str(error)

    def test_missing_properties_gets_added(self) -> None:
        """Test that schema without properties field gets properties added automatically."""
        input_schema = {"type": "object"}

        workflow = WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema=input_schema)

        expected_schema = {"type": "object", "properties": {}}
        assert workflow.input_schema == expected_schema

    def test_non_dict_properties_fails(self) -> None:
        """Test that schema with non-dict properties fails validation."""
        invalid_schema = {"type": "object", "properties": "not a dict"}

        with pytest.raises(TypeError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema=invalid_schema)

        error = exc_info.value
        assert "'properties' must be a dictionary" in str(error)

    def test_property_without_type_fails(self) -> None:
        """Test that property definition without type fails validation."""
        invalid_schema = {
            "type": "object",
            "properties": {
                "message": {"description": "A message"},  # Missing "type" field
            },
        }

        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema=invalid_schema)

        error = exc_info.value
        assert "Property 'message' must specify a 'type' or 'ref' field" in str(error)

    def test_non_dict_property_definition_fails(self) -> None:
        """Test that non-dict property definition fails validation."""
        invalid_schema = {
            "type": "object",
            "properties": {
                "message": "string",  # Should be {"type": "string"}
            },
        }

        with pytest.raises(TypeError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema=invalid_schema)

        error = exc_info.value
        assert "must be a dictionary with type information" in str(error)

    def test_non_dict_input_schema_fails(self) -> None:
        """Test that non-dict input_schema fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema="not a dict")

        error = exc_info.value
        # The TypeError message is wrapped by Pydantic ValidationError, so check for the core message
        assert "must be a dictionary" in str(error) or "Input should be a valid dictionary" in str(error)

    def test_complex_valid_schema_passes(self) -> None:
        """Test that complex but valid JSON Schema passes validation."""
        complex_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "User name", "minLength": 1},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "email": {"type": "string", "format": "email"},
                "preferences": {
                    "type": "object",
                    "properties": {"theme": {"type": "string"}, "notifications": {"type": "boolean"}},
                },
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["name", "email"],
            "additionalProperties": False,
        }

        workflow = WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema=complex_schema)

        assert workflow.input_schema == complex_schema

    def test_old_format_example_fails_with_helpful_message(self) -> None:
        """Test that old format (simple key-value pairs) fails with helpful message."""
        old_format_schema = {"hello": "world", "count": 5}

        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema=old_format_schema)

        error = exc_info.value
        assert "input_schema must have 'type': 'object'" in str(error)
        assert "Example:" in str(error)

    def test_type_error_vs_value_error_distinction(self) -> None:
        """Test that type errors and value errors are properly distinguished."""
        # Test built-in Pydantic validation for wrong input type (caught before our validator)
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema="not a dict")
        assert "Input should be a valid dictionary" in str(exc_info.value)

        # Test ValueError for wrong schema structure
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(name="TestWorkflow", task_queue="test-queue", input_schema={"type": "string"})
        assert "must have 'type': 'object'" in str(exc_info.value)

        # Test TypeError for wrong properties type (our custom validator)
        with pytest.raises(TypeError) as exc_info:
            WorkflowDefinition(
                name="TestWorkflow",
                task_queue="test-queue",
                input_schema={"type": "object", "properties": "not a dict"},
            )
        assert "'properties' must be a dictionary" in str(exc_info.value)


class TestActivityDefinition:
    """Test cases for ActivityDefinition model."""

    def test_activity_definition_initialization_with_valid_data(self) -> None:
        """Test ActivityDefinition initialization with valid data."""
        # Arrange & Act
        activity = ActivityDefinition(
            name="test_activity",
            task_queue="test-queue",
            input_schema={"type": "object"},
        )

        # Assert
        assert activity.name == "test_activity"
        assert activity.task_queue == "test-queue"
        assert activity.input_schema == {"type": "object", "properties": {}}

    def test_activity_definition_missing_required_fields(self) -> None:
        """Test that ActivityDefinition requires all fields."""
        with pytest.raises(ValidationError) as exc_info:
            ActivityDefinition(name="test_activity")
        error = exc_info.value
        assert "task_queue" in str(error) or "input_schema" in str(error)


class TestWorkerRegistration:
    """Test cases for WorkerRegistration model."""

    def test_worker_registration_with_required_fields_only(self) -> None:
        """Test WorkerRegistration with only required fields."""
        # Arrange & Act
        registration = WorkerRegistration(
            worker_name="test-worker",
            worker_version="1.0.0",
            task_queue="test-queue",
        )

        # Assert
        assert registration.worker_name == "test-worker"
        assert registration.worker_version == "1.0.0"
        assert registration.task_queue == "test-queue"
        assert isinstance(registration.generated_at, datetime)
        assert registration.workflows == []
        assert registration.activities == []

    def test_worker_registration_with_workflows_and_activities(self) -> None:
        """Test WorkerRegistration with workflows and activities."""
        # Arrange
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object"},
        )
        activity = ActivityDefinition(
            name="test_activity",
            task_queue="test-queue",
            input_schema={"type": "object"},
        )

        # Act
        registration = WorkerRegistration(
            worker_name="test-worker",
            worker_version="1.0.0",
            task_queue="test-queue",
            workflows=[workflow],
            activities=[activity],
        )

        # Assert
        assert len(registration.workflows) == 1
        assert len(registration.activities) == 1
        assert registration.workflows[0].name == "TestWorkflow"
        assert registration.activities[0].name == "test_activity"

    def test_worker_registration_missing_required_fields(self) -> None:
        """Test that WorkerRegistration requires worker_name, worker_version, and task_queue."""
        with pytest.raises(ValidationError) as exc_info:
            WorkerRegistration(worker_version="1.0.0", task_queue="test-queue")
        error = exc_info.value
        assert "worker_name" in str(error)
        assert "Field required" in str(error)

    def test_worker_registration_generated_at_default(self) -> None:
        """Test that generated_at gets a default datetime value."""
        registration = WorkerRegistration(
            worker_name="test-worker",
            worker_version="1.0.0",
            task_queue="test-queue",
        )

        assert isinstance(registration.generated_at, datetime)
        # Check that the timestamp is recent (within last minute)
        now = datetime.now(UTC)
        time_diff = abs((now - registration.generated_at).total_seconds())
        assert time_diff < 60


class TestStoredWorkerRegistration:
    """Test cases for StoredWorkerRegistration model."""

    def test_stored_worker_registration_inheritance(self) -> None:
        """Test that StoredWorkerRegistration properly inherits from WorkerRegistration."""
        # Arrange
        base_data = {
            "worker_name": "test-worker",
            "worker_version": "1.0.0",
            "task_queue": "test-queue",
        }

        # Act
        stored_registration = StoredWorkerRegistration(**base_data)

        # Assert
        assert stored_registration.worker_name == "test-worker"
        assert stored_registration.worker_version == "1.0.0"
        assert stored_registration.task_queue == "test-queue"
        assert isinstance(stored_registration.generated_at, datetime)
        assert isinstance(stored_registration.stored_at, datetime)

    def test_stored_worker_registration_stored_at_default(self) -> None:
        """Test that stored_at gets a default datetime value."""
        stored_registration = StoredWorkerRegistration(
            worker_name="test-worker",
            worker_version="1.0.0",
            task_queue="test-queue",
        )

        assert isinstance(stored_registration.stored_at, datetime)
        # Check that the timestamp is recent (within last minute)
        now = datetime.now(UTC)
        time_diff = abs((now - stored_registration.stored_at).total_seconds())
        assert time_diff < 60


class TestWorkerRegistrationSummary:
    """Test cases for WorkerRegistrationSummary model."""

    def test_worker_registration_summary_initialization(self) -> None:
        """Test WorkerRegistrationSummary initialization with all fields."""
        # Arrange
        last_updated = datetime.now(UTC)
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object"},
        )

        # Act
        summary = WorkerRegistrationSummary(
            worker_name="test-worker",
            worker_version="1.0.0",
            task_queue="test-queue",
            last_updated=last_updated,
            workflows=[workflow],
            activities=[],
        )

        # Assert
        assert summary.worker_name == "test-worker"
        assert summary.worker_version == "1.0.0"
        assert summary.task_queue == "test-queue"
        assert summary.last_updated == last_updated
        assert len(summary.workflows) == 1
        assert len(summary.activities) == 0

    def test_worker_registration_summary_missing_required_fields(self) -> None:
        """Test that WorkerRegistrationSummary requires all fields."""
        with pytest.raises(ValidationError) as exc_info:
            WorkerRegistrationSummary(
                worker_name="test-worker",
                worker_version="1.0.0",
            )
        error = exc_info.value
        assert "task_queue" in str(error) or "last_updated" in str(error)


class TestWorkflowRegistryResponse:
    """Test cases for WorkflowRegistryResponse model."""

    def test_workflow_registry_response_initialization(self) -> None:
        """Test WorkflowRegistryResponse initialization."""
        # Arrange
        summary = WorkerRegistrationSummary(
            worker_name="test-worker",
            worker_version="1.0.0",
            task_queue="test-queue",
            last_updated=datetime.now(UTC),
            workflows=[],
            activities=[],
        )

        # Act
        response = WorkflowRegistryResponse(
            workers=[summary],
            total_workers=1,
            total_workflows=5,
            total_activities=3,
        )

        # Assert
        assert len(response.workers) == 1
        assert response.total_workers == 1
        assert response.total_workflows == 5
        assert response.total_activities == 3

    def test_workflow_registry_response_empty_workers(self) -> None:
        """Test WorkflowRegistryResponse with empty workers list."""
        response = WorkflowRegistryResponse(
            workers=[],
            total_workers=0,
            total_workflows=0,
            total_activities=0,
        )

        assert response.workers == []
        assert response.total_workers == 0
        assert response.total_workflows == 0
        assert response.total_activities == 0


class TestWorkerRegistrationResponse:
    """Test cases for WorkerRegistrationResponse model."""

    def test_worker_registration_response_initialization(self) -> None:
        """Test WorkerRegistrationResponse initialization."""
        # Arrange & Act
        response = WorkerRegistrationResponse(
            message="Worker registered successfully",
            worker_name="test-worker",
            registration_id="test-worker_2024-01-15T10:30:00Z",
        )

        # Assert
        assert response.message == "Worker registered successfully"
        assert response.worker_name == "test-worker"
        assert response.registration_id == "test-worker_2024-01-15T10:30:00Z"

    def test_worker_registration_response_missing_fields(self) -> None:
        """Test that WorkerRegistrationResponse requires all fields."""
        with pytest.raises(ValidationError) as exc_info:
            WorkerRegistrationResponse(message="Success")
        error = exc_info.value
        assert "worker_name" in str(error) or "registration_id" in str(error)


class TestRegistryModelsIntegration:
    """Integration tests for all registry models."""

    def test_all_models_are_pydantic_models(self) -> None:
        """Test that all models inherit from BaseModel."""
        from pydantic import BaseModel

        assert issubclass(WorkflowDefinition, BaseModel)
        assert issubclass(ActivityDefinition, BaseModel)
        assert issubclass(WorkerRegistration, BaseModel)
        assert issubclass(StoredWorkerRegistration, BaseModel)
        assert issubclass(WorkerRegistrationSummary, BaseModel)
        assert issubclass(WorkflowRegistryResponse, BaseModel)
        assert issubclass(WorkerRegistrationResponse, BaseModel)

    def test_schema_generation(self) -> None:
        """Test that all models can generate JSON schemas."""
        models = [
            WorkflowDefinition,
            ActivityDefinition,
            WorkerRegistration,
            StoredWorkerRegistration,
            WorkerRegistrationSummary,
            WorkflowRegistryResponse,
            WorkerRegistrationResponse,
        ]

        for model in models:
            schema = model.model_json_schema()
            assert "properties" in schema
            assert isinstance(schema["properties"], dict)


class TestWorkflowDefinitionExposureFields:
    """Test cases for WorkflowDefinition exposure and description fields."""

    def test_new_exposed_and_description_fields(self) -> None:
        """Test WorkflowDefinition with new exposed and description fields."""
        # Arrange & Act
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object", "properties": {}},
            exposed=True,
            description="This is a test workflow",
        )

        # Assert
        assert workflow.exposed is True
        assert workflow.description == "This is a test workflow"
        assert workflow.mcp_exposed is False  # Default value for deprecated field
        assert workflow.mcp_description is None  # Default value for deprecated field

    def test_backward_compatibility_mcp_exposed_maps_to_exposed(self) -> None:
        """Test backward compatibility: old mcp_exposed maps to new exposed."""
        # Arrange & Act - using old field name
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object", "properties": {}},
            mcp_exposed=True,
        )

        # Assert - new field should be set via migration
        assert workflow.exposed is True
        assert workflow.mcp_exposed is True  # Old field still accessible

    def test_backward_compatibility_mcp_description_maps_to_description(self) -> None:
        """Test backward compatibility: old mcp_description maps to new description."""
        # Arrange & Act - using old field name
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object", "properties": {}},
            mcp_description="Old style description",
        )

        # Assert - new field should be set via migration
        assert workflow.description == "Old style description"
        assert workflow.mcp_description == "Old style description"  # Old field still accessible

    def test_new_fields_take_precedence_over_old_fields(self) -> None:
        """Test that new fields take precedence over old fields when both provided."""
        # Arrange & Act - provide both old and new field values
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object", "properties": {}},
            exposed=True,
            description="New description",
            mcp_exposed=False,
            mcp_description="Old description",
        )

        # Assert - new fields should take precedence
        assert workflow.exposed is True  # New field value, not False from mcp_exposed
        assert workflow.description == "New description"  # New field value, not old one

    def test_exposed_default_false(self) -> None:
        """Test that exposed defaults to False when not provided."""
        # Arrange & Act
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object", "properties": {}},
        )

        # Assert
        assert workflow.exposed is False
        assert workflow.description is None

    def test_description_default_none(self) -> None:
        """Test that description defaults to None when not provided."""
        # Arrange & Act
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object", "properties": {}},
        )

        # Assert
        assert workflow.description is None

    def test_both_old_fields_migrate_together(self) -> None:
        """Test that both old fields can be migrated at once."""
        # Arrange & Act - using both old fields
        workflow = WorkflowDefinition(
            name="TestWorkflow",
            task_queue="test-queue",
            input_schema={"type": "object", "properties": {}},
            mcp_exposed=True,
            mcp_description="Old style workflow",
        )

        # Assert - both new fields should be set
        assert workflow.exposed is True
        assert workflow.description == "Old style workflow"
