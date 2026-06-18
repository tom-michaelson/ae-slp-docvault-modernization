"""Client for managing Human-in-the-Loop (HITL) tasks in Temporal workflows."""

from typing import Any

from temporalio.client import Client

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.api import HITLTaskDetail, HITLTaskInfo
from awa.core.models.hitl import HITLChatMessage, HITLResponse


class TaskResponseError(Exception):
    """Raised when responding to a HITL Task fails."""


class HITLTaskClient:
    """Client for interacting with HITL tasks in Temporal workflows.

    This client handles all HITL-specific operations including:
    - Listing pending HITL tasks
    - Getting task details
    - Submitting responses
    - Sending chat messages
    """

    def __init__(self, client: Client) -> None:
        """Initialize the HITL Task client.

        Args:
            client: The Temporal client instance

        """
        self.client = client
        self.logger = get_logger(LoggerComponent.CLIENT)

    async def list_pending_tasks(self) -> list[HITLTaskInfo]:
        """List all HITL workflows that are awaiting human input.

        Returns:
            List of HITLTaskInfo objects representing pending HITL tasks

        """
        tasks = []

        # Query for running workflows that might have HITL child workflows
        async for workflow in self.client.list_workflows('ExecutionStatus = "Running"'):
            # Skip parent workflows
            self.logger.info(f"Examing child workflow {workflow.workflow_type}")
            if workflow.parent_id is None:
                continue

            self.logger.info(f"Examining child workflow {workflow.workflow_type}")
            if workflow.workflow_type == "awa-hitl-child-workflow":
                task = await self._extract_task_info(
                    workflow,
                )
                if task:
                    tasks.append(task)

        return tasks

    async def _get_workflow_id_from_run_id(self, run_id: str) -> str | None:
        """Convert run ID to workflow ID by finding the workflow with matching run_id.

        Args:
            run_id: The workflow run ID

        Returns:
            The workflow ID if found, None otherwise

        """
        # Search through all workflows to find one with matching run_id
        async for workflow in self.client.list_workflows(""):
            if workflow.run_id == run_id:
                return workflow.id
        return None

    async def list_pending_tasks_for_workflow(self, run_id: str) -> list[HITLTaskInfo]:
        """List all HITL tasks for a specific parent workflow.

        Args:
            run_id: The parent workflow ID or run ID

        Returns:
            List of HITLTaskInfo objects representing pending HITL tasks for the workflow

        """
        # Try to resolve run_id to workflow_id if needed
        workflow_id = run_id

        # First, try to find a workflow with this as run_id
        resolved_workflow_id = await self._get_workflow_id_from_run_id(run_id)
        if resolved_workflow_id:
            workflow_id = resolved_workflow_id
            self.logger.info(f"Resolved run_id {run_id} to workflow_id {workflow_id}")

        tasks = []

        # Query for running workflows that might have HITL child workflows
        async for workflow in self.client.list_workflows('ExecutionStatus = "Running"'):
            # Skip parent workflows
            if workflow.parent_id is None:
                continue

            # Only include tasks for the specified workflow
            if workflow.parent_id != workflow_id:
                continue

            self.logger.info(f"Examining child workflow {workflow.workflow_type}")
            if workflow.workflow_type == "awa-hitl-child-workflow":
                task = await self._extract_task_info(
                    workflow,
                )
                if task:
                    tasks.append(task)

        return tasks

    async def _extract_task_info(
        self,
        pending_task: Any,  # noqa: ANN401
    ) -> HITLTaskInfo | None:
        """Extract task info from a pending HITL child workflow.

        Args:
            pending_task: The pending child workflow info

        Returns:
            HITLTaskInfo if task is pending, None otherwise

        """
        # Found a HITL child workflow - query its context
        child_handle = self.client.get_workflow_handle(pending_task.id)

        # Query the HITL workflow for its context
        context = await child_handle.query("get_context")
        is_response_received = await child_handle.query("is_response_received")

        # Only include if still waiting for response
        if context and not is_response_received:
            return HITLTaskInfo(
                id=pending_task.id,
                workflow_id=pending_task.parent_id,
                title=context.get("title", "Untitled Task"),
                description=context.get("description", ""),
                start_time=pending_task.execution_time,
                chat_mode=context.get("chat_mode", False),
                non_blocking=False,  # We'll query this if needed
            )
        return None

    async def get_task_details(self, task_id: str) -> HITLTaskDetail | None:
        """Get detailed information about a specific HITL task.

        Args:
            task_id: The HITL child workflow ID

        Returns:
            HITLTaskDetail object with full task information, or None if not found

        """
        # Get the HITL child workflow handle
        child_handle = self.client.get_workflow_handle(task_id)

        # Describe the workflow to get its status and parent
        description = await child_handle.describe()

        # Query the HITL workflow for its context and state
        context = await child_handle.query("get_context")
        chat_history = await child_handle.query("get_chat_history")
        is_response_received = await child_handle.query("is_response_received")

        if not context:
            self.logger.warning(f"No context found for HITL task {task_id}")
            return None

        # Get parent workflow run ID - HITL tasks always have a parent
        parent_handle = self.client.get_workflow_handle(description.parent_id)
        parent_description = await parent_handle.describe()
        parent_run_id = parent_description.run_id

        return HITLTaskDetail(
            workflow_id=description.parent_id,
            id=task_id,
            parent_run_id=parent_run_id,
            title=context.get("title", "Untitled Task"),
            description=context.get("description", ""),
            start_time=description.start_time,
            markdown=context.get("markdown", ""),
            input_schema=context.get("input_schema", {}),
            attachments=context.get("attachments", []),
            chat_mode=context.get("chat_mode", False),
            chat_history=chat_history or [],
            response_received=is_response_received,
            timed_out=False,  # Would need to check workflow status for timeout
        )

    async def submit_response(
        self,
        task_id: str,
        response_data: dict[str, any],
    ) -> None:
        """Submit a response to a HITL task.

        Args:
            task_id: The HITL child workflow ID
            response_data: The response data conforming to the task's input schema
            message: Optional message to include with the response

        Raises:
            TaskResponseError: If submission fails

        """
        try:
            # Get the HITL child workflow handle
            child_handle = self.client.get_workflow_handle(task_id)

            self.logger.info(f"Retrieved child workflow info {child_handle.id}")
            self.logger.info(f"Retrieved child workflow info {child_handle.run_id}")

            response = HITLResponse(data=response_data)

            # Send the submit_response signal with the HITLResponse object
            await child_handle.signal("submit_response", response)

            self.logger.info(f"Successfully submitted response to HITL task {task_id}")

            # Check if this is a child workflow and signal the parent about completion
            description = await child_handle.describe()
            if description.parent_id:
                parent_handle = self.client.get_workflow_handle(description.parent_id)
                await parent_handle.signal("mark_conversation_complete")
                self.logger.info(f"Signaled parent workflow {description.parent_id} about HITL task completion")

        except Exception as e:
            raise TaskResponseError(
                f"Failed to submit response to HITL task {task_id}: {e}",
            ) from e

    async def send_message(
        self,
        task_id: str,
        message: str,
    ) -> None:
        """Send a system chat message to a HITL task in chat mode.

        Args:
            task_id: The HITL child workflow ID
            message: The message content

        Raises:
            TaskResponseError: If task is not in chat mode or sending fails

        """
        try:
            # Get the HITL child workflow handle
            child_handle = self.client.get_workflow_handle(task_id)

            # First check if the task is in chat mode
            context = await child_handle.query("get_context")
            if not context or not context.get("chat_mode", False):
                msg = f"HITL task {task_id} is not in chat mode"
                raise TaskResponseError(msg)  # noqa: TRY301

            # Create the chat message (timestamp and is_human will be set by workflow)
            chat_message = HITLChatMessage(message=message)

            # Send the add_system_message signal
            await child_handle.signal("add_system_message", chat_message)

            self.logger.info(f"Successfully sent system message to HITL task {task_id}")

        except Exception as e:
            raise TaskResponseError(
                f"Failed to send system message to HITL task {task_id}: {e}",
            ) from e

    async def send_human_message(
        self,
        task_id: str,
        message: str,
        data: dict[str, any] | None = None,
    ) -> None:
        """Send a human chat message to a HITL task in chat mode.

        Args:
            task_id: The HITL child workflow ID
            message: The message content
            data: Optional structured data to include with the message

        Raises:
            TaskResponseError: If task is not in chat mode or sending fails

        """
        try:
            # Get the HITL child workflow handle
            child_handle = self.client.get_workflow_handle(task_id)

            # First check if the task is in chat mode
            context = await child_handle.query("get_context")
            if not context or not context.get("chat_mode", False):
                msg = f"HITL task {task_id} is not in chat mode"
                raise TaskResponseError(msg)  # noqa: TRY301

            # Create the chat message (timestamp and is_human will be set by workflow)
            chat_message = HITLChatMessage(message=message, data=data)

            # Send the add_human_message signal
            await child_handle.signal("add_human_message", chat_message)

            self.logger.info(f"Successfully sent human message to HITL task {task_id}")

        except Exception as e:
            raise TaskResponseError(
                f"Failed to send human message to HITL task {task_id}: {e}",
            ) from e
