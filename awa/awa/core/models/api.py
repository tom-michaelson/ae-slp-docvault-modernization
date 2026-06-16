"""API response models for health endpoints."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator
from pydantic.json_schema import SkipJsonSchema

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.hitl import HITLChatMessage


class ServiceStatusValues(StrEnum):
    UP = "up"
    DOWN = "down"


class ServerDownReasons(StrEnum):
    UNREACHABLE = "Temporal service unreachable"


class WorkerDownReasons(StrEnum):
    SERVER_DOWN = "Server down (worker checks skipped)"
    NO_ACTIVE_POLLERS = "No active worker pollers found"


class ServiceStatus(BaseModel):
    """Status of an individual service component.

    Attributes:
        status: The status of the service ("up" or "down")
        message: Optional message providing additional details about the status

    """

    status: str
    message: str | None = Field(default=None)


class HealthStatus(BaseModel):
    """Overall health status containing all service components.

    Attributes:
        temporal_service: Status of the Temporal server service
        temporal_worker: Status of the Temporal worker service

    """

    temporal_service: ServiceStatus
    temporal_worker: ServiceStatus


class HealthResponse(BaseModel):
    """Complete health check response.

    Attributes:
        status: The health status containing all service components

    """

    status: HealthStatus


class WorkflowInfo(BaseModel):
    """Information about a discovered workflow.

    Attributes:
        name: The name of the workflow
        module: The module where the workflow is defined
        parameters: List of parameter names with types for the workflow's run method
        queues: List of task queues this workflow is registered to
        description: Optional human-readable description of the workflow

    """

    name: str
    module: str
    parameters: dict
    queues: list[str] = Field(default_factory=list, description="Task queues this workflow is registered to")
    description: str | None = Field(default=None, description="Human-readable description of the workflow")


class WorkflowListResponse(BaseModel):
    """Response containing a list of available workflows.

    Attributes:
        workflows: List of workflow information objects

    """

    workflows: list[WorkflowInfo]


class WorkflowRunStatus(StrEnum):
    CANCELED = "Canceled"
    COMPLETED = "Completed"
    CONTINUED_AS_NEW = "Continued As New"
    FAILED = "Failed"
    RUNNING = "Running"
    TERMINATED = "Terminated"
    TIMED_OUT = "Timed Out"
    UNSPECIFIED = "Unspecified"
    UNKNOWN = "Unknown"


class WorkflowRun(BaseModel):
    """Overall workflow run data.

    Attributes:
        type: Name of the workflow
        id: Temporal Run id
        workflow_id: Temporal Workflow id
        status: Workflow status from Temporal
        started: Timestamp for when the workflow started
        duration: Duration for how long the workflow ran (or has been running, if it's not completed or terminated)
        monitor: Link to Temporal UI for monitoring this workflow run
        pending_tasks_count: Count of pending child tasks (0 for non-running workflows)

    """

    type: str
    id: str
    workflow_id: str
    status: WorkflowRunStatus
    started: datetime
    duration: str
    monitor: str
    pending_tasks_count: int = 0


class WorkflowRunListResponse(BaseModel):
    """Lists running and completed workflows.

    Attributes:
        data: List of Workflow Runs

    """

    workflows: list[WorkflowRun]


class WorkflowDefinition(BaseModel):
    """Definition of a workflow that can be executed.

    Attributes:
        name: The workflow class name
        task_queue: Task queue for workflow execution
        input_schema: JSON Schema for workflow input validation (must be valid JSON Schema)
        exposed: Whether this workflow should be publicly exposed (API and MCP)
        description: Human-readable description for exposed workflows

    """

    name: str = Field(..., description="Workflow class name", min_length=1)
    task_queue: str = Field(..., description="Task queue for workflow execution", min_length=1)
    input_schema: dict[str, Any] = Field(
        ...,
        description="Valid JSON Schema for workflow input validation.",
    )

    # New fields (preferred)
    exposed: bool = Field(
        default=False,
        description="Whether this workflow should be publicly exposed (API and MCP)",
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description for exposed workflows",
    )

    # Deprecated fields (for backward compatibility)
    mcp_exposed: bool = Field(
        default=False,
        description="[DEPRECATED] Use 'exposed' instead. Whether this workflow should be exposed as an MCP tool",
    )
    mcp_description: str | None = Field(
        default=None,
        description="[DEPRECATED] Use 'description' instead. Human-readable description for MCP tool",
    )

    @field_validator("input_schema")
    @classmethod
    def validate_input_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate that input_schema is proper JSON Schema format.

        Args:
            v: The input schema to validate

        Returns:
            Validated schema

        Raises:
            ValueError: If schema is not valid JSON Schema format
            TypeError: If schema has incorrect types

        """
        if not isinstance(v, dict):
            raise TypeError("input_schema must be a dictionary")

        if not v:
            # Allow empty schema - will be converted to basic object schema
            return {"type": "object", "properties": {}}

        # Check for required JSON Schema structure
        if v.get("type") != "object":
            raise ValueError(
                "input_schema must have 'type': 'object'. "
                "Example: {'type': 'object', 'properties': {'param1': {'type': 'string'}}}",
            )

        # If properties is missing, add an empty properties object
        if "properties" not in v:
            v = dict(v)  # Make a copy to avoid mutating input
            v["properties"] = {}

        if not isinstance(v["properties"], dict):
            raise TypeError("input_schema 'properties' must be a dictionary")

        # Optional: Validate property definitions
        for prop_name, prop_def in v["properties"].items():
            if not isinstance(prop_def, dict):
                raise TypeError(f"Property '{prop_name}' must be a dictionary with type information")
            if ("type" not in prop_def) and ("$ref" not in prop_def):
                raise ValueError(f"Property '{prop_name}' must specify a 'type' or 'ref' field")

        return v

    @field_validator("mcp_description")
    @classmethod
    def validate_mcp_description(cls, v: str | None, info: ValidationInfo) -> str | None:
        """Validate that mcp_description is provided when mcp_exposed is True."""
        if info.data.get("mcp_exposed", False) and not v:
            logger = get_logger(LoggerComponent.API)
            logger.warning(f"Workflow '{info.data.get('name', 'unknown')}' is MCP-exposed but lacks a description")
        return v

    @model_validator(mode="after")
    def migrate_old_fields(self) -> "WorkflowDefinition":
        """Migrate old field names to new ones for backward compatibility.

        If old fields (mcp_exposed, mcp_description) are provided but new fields
        (exposed, description) are not, copy the old values to the new fields.
        """
        # Migrate mcp_exposed to exposed if needed
        if self.mcp_exposed and not self.exposed:
            self.exposed = self.mcp_exposed

        # Migrate mcp_description to description if needed
        if self.mcp_description and not self.description:
            self.description = self.mcp_description

        return self


class ActivityDefinition(BaseModel):
    """Definition of an activity that can be executed.

    Attributes:
        name: The activity function name
        task_queue: Task queue for activity execution
        input_schema: JSON Schema for activity input validation (must be valid JSON Schema)

    """

    name: str = Field(..., description="Activity function name", min_length=1)
    task_queue: str = Field(..., description="Task queue for activity execution", min_length=1)
    input_schema: dict[str, Any] = Field(
        ...,
        description="Valid JSON Schema for activity input validation.",
    )

    @field_validator("input_schema")
    @classmethod
    def validate_input_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate that input_schema is proper JSON Schema format.

        Args:
            v: The input schema to validate

        Returns:
            Validated schema

        Raises:
            ValueError: If schema is not valid JSON Schema format
            TypeError: If schema has incorrect types

        """
        if not isinstance(v, dict):
            raise TypeError("input_schema must be a dictionary")

        if not v:
            # Allow empty schema - will be converted to basic object schema
            return {"type": "object", "properties": {}}

        # Check for required JSON Schema structure
        if v.get("type") != "object":
            raise ValueError(
                "input_schema must have 'type': 'object'. "
                "Example: {'type': 'object', 'properties': {'param1': {'type': 'string'}}}",
            )

        # If properties is missing, add an empty properties object
        if "properties" not in v:
            v = dict(v)  # Make a copy to avoid mutating input
            v["properties"] = {}

        if not isinstance(v["properties"], dict):
            raise TypeError("input_schema 'properties' must be a dictionary")

        # Optional: Validate property definitions
        for prop_name, prop_def in v["properties"].items():
            if not isinstance(prop_def, dict):
                raise TypeError(f"Property '{prop_name}' must be a dictionary with type information")
            if "type" not in prop_def:
                raise ValueError(f"Property '{prop_name}' must specify a 'type' field")

        return v


class WorkerRegistration(BaseModel):
    """Worker registration payload.

    Attributes:
        worker_name: Unique identifier for the worker
        worker_version: Version of the worker
        task_queue: Primary task queue for the worker
        generated_at: Timestamp when registration was generated
        workflows: List of available workflows
        activities: List of available activities

    """

    worker_name: str = Field(..., description="Unique identifier for the worker", min_length=1)
    worker_version: str = Field(..., description="Version of the worker", min_length=1)
    task_queue: str = Field(..., description="Primary task queue for the worker", min_length=1)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when registration was generated",
    )
    workflows: list[WorkflowDefinition] = Field(default_factory=list, description="List of available workflows")
    activities: list[ActivityDefinition] = Field(default_factory=list, description="List of available activities")


class StoredWorkerRegistration(WorkerRegistration):
    """Worker registration with storage metadata.

    Attributes:
        stored_at: Timestamp when registration was stored

    """

    stored_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when registration was stored",
    )


class WorkerRegistrationSummary(BaseModel):
    """Summary of worker registration for discovery.

    Attributes:
        worker_name: Unique identifier for the worker
        worker_version: Version of the worker
        task_queue: Primary task queue for the worker
        last_updated: Timestamp of last registration update
        workflows: List of available workflows
        activities: List of available activities

    """

    worker_name: str = Field(..., description="Unique identifier for the worker")
    worker_version: str = Field(..., description="Version of the worker")
    task_queue: str = Field(..., description="Primary task queue for the worker")
    last_updated: datetime = Field(..., description="Timestamp of last registration update")
    workflows: list[WorkflowDefinition] = Field(..., description="List of available workflows")
    activities: list[ActivityDefinition] = Field(..., description="List of available activities")


class WorkflowRegistryResponse(BaseModel):
    """Response for workflow registry discovery.

    Attributes:
        workers: Active worker registrations
        total_workers: Total number of active workers
        total_workflows: Total number of available workflows
        total_activities: Total number of available activities

    """

    workers: list[WorkerRegistrationSummary] = Field(..., description="Active worker registrations")
    total_workers: int = Field(..., description="Total number of active workers")
    total_workflows: int = Field(..., description="Total number of available workflows")
    total_activities: int = Field(..., description="Total number of available activities")


class WorkerRegistrationResponse(BaseModel):
    """Response for successful worker registration.

    Attributes:
        message: Success message
        worker_name: Name of the registered worker
        registration_id: Unique registration identifier

    """

    message: str = Field(..., description="Success message")
    worker_name: str = Field(..., description="Name of the registered worker")
    registration_id: str = Field(..., description="Unique registration identifier")


class WorkflowRunPayload(BaseModel):
    """POST data needed to initate a new workflow run.

    Attributes:
        name: The name of the workflow to initiate
        input: Input payload to initiate workflow, in json
        task_queue: Optional task queue to use for workflow execution

    """

    name: str
    input: str
    task_queue: str | SkipJsonSchema[None] = Field(None, description="Optional task queue for workflow execution")


class HITLTaskInfo(BaseModel):
    """Information around a HITL Task.

    Attributes:
        id: Unique identifier for a task
        workflow_id: Parent workflow id
        title: Task title
        description: Description of task
        start_time: Datetime of task start
        chat_mode: Whether task uses chat mode
        non_blocking: Whether task is non-blocking

    """

    id: str
    workflow_id: str
    title: str
    description: str
    start_time: datetime
    chat_mode: bool = Field(default=False, description="Whether task uses chat mode")
    non_blocking: bool = Field(default=False, description="Whether task is non-blocking")


class HITLTaskDetail(BaseModel):
    """Detailed Information around a HITL Task.

    Attributes:
        workflow_id: Parent workflow id
        id: Temporal run id
        parent_run_id: Parent workflow run id
        title: Task title
        description: Description of task
        start_time: Datetime of task start
        markdown: Task Markdown
        input_schema: Task Schema
        attachments: List of attachment file paths
        chat_mode: Whether task uses chat mode
        chat_history: List of chat messages
        response_received: Whether a response has been received
        timed_out: Whether the task has timed out

    """

    workflow_id: str
    id: str = Field(..., description="Temporal run id")
    parent_run_id: str = Field(..., description="Parent workflow run id")
    title: str
    description: str
    start_time: datetime
    markdown: str
    input_schema: dict | SkipJsonSchema[None]
    attachments: list[str] = Field(default_factory=list, description="List of attachment file paths")
    chat_mode: bool = Field(default=False, description="Whether task uses chat mode")
    chat_history: list[HITLChatMessage] = Field(default_factory=list, description="List of chat messages")
    response_received: bool = Field(default=False, description="Whether a response has been received")
    timed_out: bool = Field(default=False, description="Whether the task has timed out")


class PostResponse(BaseModel):
    """Generic POST response to provide consistent returns.

    Attributes:
        data: POST response data

    """

    data: str


class AgentWorkflowInfo(BaseModel):
    """Information about an agent child workflow.

    Attributes:
        workflow_id: Child workflow ID
        parent_id: Parent workflow ID
        status: Workflow execution status
        start_time: When the workflow started
        end_time: When the workflow ended (if completed)
        execution_time_ms: Total execution time in milliseconds
        agent_mode: Agent mode (ACT, PLAN, etc)
        agent_provider: Agent provider (CLAUDE, GOOSE, etc)
        prompt_preview: First 100 characters of the prompt
        task_queue: Task queue used
        run_id: Temporal run ID
        attempt: Retry attempt number

    """

    workflow_id: str = Field(..., description="Child workflow ID")
    parent_id: str = Field(..., description="Parent workflow ID")
    status: str = Field(..., description="Workflow execution status")
    start_time: datetime = Field(..., description="When the workflow started")
    end_time: datetime | None = Field(default=None, description="When the workflow ended")
    execution_time_ms: int | None = Field(default=None, description="Total execution time in milliseconds")
    agent_mode: str | None = Field(default=None, description="Agent mode (ACT, PLAN, etc)")
    agent_provider: str | None = Field(default=None, description="Agent provider (CLAUDE, GOOSE, etc)")
    prompt_preview: str | None = Field(default=None, description="First 100 characters of the prompt")
    task_queue: str = Field(..., description="Task queue used")
    run_id: str = Field(..., description="Temporal run ID")
    attempt: int = Field(default=1, description="Retry attempt number")


class AgentSessionType(StrEnum):
    """Type of agent streaming session."""

    AGENT = "agent"
    PARENT = "parent"


class AgentSession(BaseModel):
    """Model for an individual agent streaming session.

    Attributes:
        session_id: Unique session identifier (typically the workflow ID)
        session_type: Type of session ('agent' or 'parent')

    """

    session_id: str = Field(..., description="Unique session identifier")
    session_type: AgentSessionType = Field(..., description="Type of session")


class WorkflowAgentSessionsResponse(BaseModel):
    """Response model for workflow agent sessions query.

    Attributes:
        workflow_id: The parent workflow ID that was queried
        sessions: List of discovered agent sessions
        count: Total number of sessions discovered

    """

    workflow_id: str = Field(..., description="The parent workflow ID")
    sessions: list[AgentSession] = Field(..., description="List of discovered agent sessions")
    count: int = Field(..., description="Total number of sessions")
