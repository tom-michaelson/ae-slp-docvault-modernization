import asyncio
import contextlib
import json
import threading
from pathlib import Path

from agents.extensions.models.litellm_provider import LitellmProvider
from temporalio.client import Client, WorkflowHandle
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin

from awa.core import constants
from awa.core.engine.hitl_task_client import HITLTaskClient
from awa.core.engine.workflow_management_client import WorkflowManagementClient
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.api import (
    HITLTaskDetail,
    HITLTaskInfo,
    WorkflowRun,
)
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.json_utils import JsonUtils
from awa.core.utils.mcp_config_loader import MCPConfigLoader
from awa.core.utils.openai_agents_mcp_provider_factory import MCPProviderFactory
from awa.core.utils.temporal_utils import TemporalUtils
from awa.core.utils.workflow_metadata import get_workflow_queue
from awa.sdk.models.exceptions.invalid_input_error import InvalidInputApplicationError


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""


class TemporalClient:
    def __init__(self, terminate_all: bool = False) -> None:
        self.logger = get_logger(LoggerComponent.CLI)
        self.default_task_queue = constants.TASK_QUEUE
        self._client: Client | None = None
        self._hitl_client: HITLTaskClient | None = None
        self._workflow_mgmt_client: WorkflowManagementClient | None = None
        self.terminate_all = terminate_all
        self._initialized = False

    @classmethod
    async def create(cls, terminate_all: bool = False) -> "TemporalClient":
        """Async factory method for TemporalClient creation."""
        instance = cls(terminate_all=terminate_all)
        # Don't initialize client connection here - do it lazily when needed
        return instance

    async def _initialize_client(self) -> None:
        """Initialize the client connection and optionally terminate workflows."""
        if not self._initialized:
            # Load MCP configuration and create providers
            mcp_providers = self._load_mcp_providers()

            # Create client connection with OpenAI Agents plugin if MCP providers are available
            if mcp_providers:
                self.logger.debug(
                    f"Initializing Temporal client with MCP support: {len(mcp_providers)} MCP server providers",
                )

                self._client = await Client.connect(
                    f"{EnvConfig.get_env_config().temporal_server_host}:{EnvConfig.get_env_config().temporal_server_port}",
                    plugins=[
                        OpenAIAgentsPlugin(
                            model_provider=LitellmProvider(),
                            mcp_server_providers=mcp_providers,
                        ),
                    ],
                )
            else:
                self.logger.debug("Initializing Temporal client without MCP support")
                self._client = await Client.connect(
                    f"{EnvConfig.get_env_config().temporal_server_host}:{EnvConfig.get_env_config().temporal_server_port}",
                )

            # Initialize specialized clients
            self._hitl_client = HITLTaskClient(self._client)
            self._workflow_mgmt_client = WorkflowManagementClient(self._client, hitl_client=self._hitl_client)

            if self.terminate_all:
                await self.terminate_all_workflows()

            self._initialized = True

    async def ensure_initialized(self) -> None:
        """Ensure the client is initialized. Call this before using client functionality."""
        if not self._initialized:
            await self._initialize_client()

    async def get_client(self) -> Client:
        await self.ensure_initialized()
        if self._client is None:
            raise RuntimeError("Failed to initialize Temporal client")
        return self._client

    async def _resolve_task_queue(self, workflow: str, task_queue: str | None) -> str:
        """Resolve the task queue for a workflow, using dynamic lookup if not provided.

        Args:
            workflow: The workflow name
            task_queue: Optional task queue parameter

        Returns:
            The resolved task queue to use

        """
        if task_queue is None:
            task_queue = await get_workflow_queue(workflow)
            if task_queue is None:
                task_queue = self.default_task_queue
                self.logger.debug(f"Using default task queue '{task_queue}' for workflow '{workflow}'")
            else:
                self.logger.debug(f"Using dynamically resolved task queue '{task_queue}' for workflow '{workflow}'")
        else:
            self.logger.debug(f"Using provided task queue '{task_queue}' for workflow '{workflow}'")

        return task_queue

    async def execute_workflow(
        self,
        workflow: str | None = None,
        workflow_input: str | None = None,
        task_queue: str | None = None,
    ) -> object:
        if workflow is None:
            raise ValueError("Workflow is required")
        workflow_id = TemporalUtils.generate_workflow_id()
        self.logger.info(f'Executing workflow "{workflow}" with ID "{workflow_id}" and input:\n"{workflow_input}"')

        # Set up Socket.IO log receiver (lazy import to avoid circular dependency)
        log_receiver = None
        receiver_thread = None

        try:
            # Import here to avoid circular import
            from awa.core.cli.socketio_client import WorkflowLogReceiver

            log_receiver = WorkflowLogReceiver()
            # Try to connect to Socket.IO for log streaming
            if log_receiver.connect_and_subscribe(workflow_id):
                # Run Socket.IO client in background thread
                receiver_thread = threading.Thread(
                    target=log_receiver.run_in_background,
                    daemon=True,
                    name=f"LogReceiver-{workflow_id}",
                )
                receiver_thread.start()
                self.logger.debug("Connected to Socket.IO for log streaming")
            else:
                self.logger.debug("Socket.IO log streaming not available, continuing without it")
        except Exception as e:  # noqa: BLE001
            self.logger.debug(f"Failed to set up log streaming: {e}")
            # Continue without log streaming

        client = await self.get_client()

        # Resolve task queue using shared logic
        task_queue = await self._resolve_task_queue(workflow, task_queue)

        try:
            if workflow_input:
                workflow_input_json = JsonUtils.parse_json(workflow_input)
                workflow_result = await client.execute_workflow(
                    workflow,
                    workflow_input_json,
                    id=workflow_id,
                    task_queue=task_queue,
                )
            else:
                workflow_result = await client.execute_workflow(
                    workflow,
                    id=workflow_id,
                    task_queue=task_queue,
                )
            return workflow_result
        except (json.JSONDecodeError, ValueError) as e:
            # Raise InvalidInputApplicationError for JSON parsing errors
            raise InvalidInputApplicationError("Invalid JSON format in input field") from e
        except Exception as e:
            self.logger.exception("Workflow execution failed")
            # Re-raise with additional context
            raise WorkflowExecutionError(f"Failed to execute workflow '{workflow}': {e!s}") from e
        finally:
            # Wait briefly to allow final logs to be received
            # This is needed because workflow logs may still be in transit
            await asyncio.sleep(1.0)  # Wait 1 second for logs to arrive

            # Clean up Socket.IO connection
            with contextlib.suppress(Exception):
                if log_receiver:
                    log_receiver.disconnect()

    async def start_workflow(
        self,
        workflow: str | None = None,
        workflow_input: str | None = None,
        task_queue: str | None = None,
        workflow_id: str | None = None,
        parent_workflow_id: str | None = None,
        parent_run_id: str | None = None,
    ) -> WorkflowHandle:
        if workflow is None:
            raise ValueError("Workflow is required")

        # Use provided workflow_id or generate one
        if workflow_id is None:
            workflow_id = TemporalUtils.generate_workflow_id()

        self.logger.info(f'Starting workflow "{workflow}" with ID "{workflow_id}" and input:\n"{workflow_input}"')

        client = await self.get_client()

        # Resolve task queue using shared logic
        task_queue = await self._resolve_task_queue(workflow, task_queue)

        try:
            # Build workflow start arguments
            start_args = {
                "id": workflow_id,
                "task_queue": task_queue,
            }

            # Add parent execution info if provided (for child workflows)
            if parent_workflow_id and parent_run_id:
                start_args["parent_execution"] = {
                    "id": parent_workflow_id,
                    "run_id": parent_run_id,
                }
                self.logger.debug(f"Creating child workflow with parent {parent_workflow_id}:{parent_run_id}")

            if workflow_input:
                workflow_input_json = JsonUtils.parse_json(workflow_input)
                workflow_result = await client.start_workflow(
                    workflow,
                    workflow_input_json,
                    **start_args,
                )
            else:
                workflow_result = await client.start_workflow(
                    workflow,
                    **start_args,
                )
            return workflow_result
        except (json.JSONDecodeError, ValueError) as e:
            # Raise InvalidInputApplicationError for JSON parsing errors
            raise InvalidInputApplicationError("Invalid JSON format in input field") from e
        except Exception as e:
            self.logger.exception("Workflow started failed")
            # Re-raise with additional context
            raise WorkflowExecutionError(f"Failed to start workflow '{workflow}': {e!s}") from e

    async def terminate_all_workflows(self) -> None:
        """Delegate to workflow management client."""
        await self.ensure_initialized()
        if self._workflow_mgmt_client:
            await self._workflow_mgmt_client.terminate_all_workflows()

    async def get_workflow_ui_link(self, workflow_id: str, run_id: str) -> str:
        """Delegate to workflow management client."""
        await self.ensure_initialized()
        if self._workflow_mgmt_client:
            return await self._workflow_mgmt_client.get_workflow_ui_link(workflow_id, run_id)
        return ""

    async def list_workflow_runs(self) -> list[WorkflowRun]:
        """Delegate to workflow management client."""
        await self.ensure_initialized()
        if self._workflow_mgmt_client:
            return await self._workflow_mgmt_client.list_workflow_runs()
        return []

    async def get_workflow_run(self, run_id: str) -> WorkflowRun | None:
        """Get a specific workflow run by run ID."""
        await self.ensure_initialized()
        if self._workflow_mgmt_client:
            return await self._workflow_mgmt_client.get_workflow_run(run_id)
        return None

    # Workflow management delegation methods preserved for backward compatibility
    def sort_workflows_by_status(self, workflows: list[WorkflowRun], status: str) -> list[WorkflowRun]:
        """Delegate to workflow management client."""
        if self._workflow_mgmt_client:
            return self._workflow_mgmt_client.sort_workflows_by_status(workflows, status)
        return workflows

    async def list_pending_tasks(self) -> list[HITLTaskInfo]:
        """Delegate to HITL task client."""
        await self.ensure_initialized()
        if self._hitl_client:
            return await self._hitl_client.list_pending_tasks()
        return []

    async def list_pending_tasks_for_workflow(self, workflow_id: str) -> list[HITLTaskInfo]:
        """Get all HITL tasks for a specific workflow."""
        await self.ensure_initialized()
        if self._hitl_client:
            return await self._hitl_client.list_pending_tasks_for_workflow(workflow_id)
        return []

    async def get_hitl_task_details(self, task_id: str) -> HITLTaskDetail | None:
        """Delegate to HITL task client."""
        await self.ensure_initialized()
        if self._hitl_client:
            return await self._hitl_client.get_task_details(task_id)
        return None

    async def submit_hitl_response(self, task_id: str, response_data: str) -> bool:
        """Delegate to HITL task client."""
        await self.ensure_initialized()
        if self._hitl_client:
            await self._hitl_client.submit_response(task_id, response_data)
            return True
        return False

    async def send_hitl_message(self, task_id: str, message: str) -> bool:
        """Delegate to HITL task client for system messages."""
        await self.ensure_initialized()
        if self._hitl_client:
            await self._hitl_client.send_message(task_id, message)
            return True
        return False

    async def send_hitl_human_message(self, task_id: str, message: str, data: dict[str, any] | None = None) -> bool:
        """Delegate to HITL task client for human messages."""
        await self.ensure_initialized()
        if self._hitl_client:
            await self._hitl_client.send_human_message(task_id, message, data)
            return True
        return False

    async def signal_workflow(self, workflow_id: str, signal_name: str, *args: any) -> bool:
        """Send a signal to a workflow."""
        await self.ensure_initialized()
        client = await self.get_client()

        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(signal_name, *args)
        return True

    async def get_workflow_parent_id(self, workflow_id: str) -> str | None:
        """Get the parent workflow ID for a given workflow."""
        await self.ensure_initialized()
        client = await self.get_client()

        handle = client.get_workflow_handle(workflow_id)
        execution = await handle.describe()

        # Check if this workflow has a parent
        if execution.parent_id:
            return execution.parent_id
        return None

    def _load_mcp_providers(self) -> list | None:
        """Load MCP server configurations and create provider instances.

        Returns:
            List of MCP server providers (both stateless and stateful), or None if no MCP config found

        """
        try:
            # Try to load MCP configuration from current working directory
            working_dir = Path.cwd()
            mcp_config = MCPConfigLoader.load_mcp_config(working_dir=working_dir)

            if mcp_config is None:
                self.logger.debug("No MCP configuration file found (mcp.json or .vscode/mcp.json)")
                return None

            # Validate the MCP configuration
            validation_errors = MCPProviderFactory.validate_mcp_config(mcp_config)
            if validation_errors:
                self.logger.warning(f"MCP configuration validation errors: {validation_errors}")
                return None

            # Create MCP providers
            stateless_providers, stateful_providers = MCPProviderFactory.create_mcp_providers(mcp_config)

            # Combine both provider lists
            all_providers = stateless_providers + stateful_providers

            # Log successful initialization
            server_count = len(mcp_config.servers)
            server_names = list(mcp_config.servers.keys())
            self.logger.info(
                f"Successfully loaded {server_count} MCP server configurations "
                f"({', '.join(server_names)}) into {len(all_providers)} providers",
            )

            return all_providers

        except (ValueError, FileNotFoundError, OSError) as e:
            self.logger.warning(f"Failed to load MCP configuration: {e}")
            self.logger.debug("Continuing without MCP server support")
            return None
        except Exception as e:  # noqa: BLE001
            # Catch-all for any unexpected errors during MCP initialization
            # We don't want MCP configuration issues to prevent Temporal client initialization
            self.logger.warning(f"Unexpected error loading MCP configuration: {e}")
            self.logger.debug("Continuing without MCP server support")
            return None
