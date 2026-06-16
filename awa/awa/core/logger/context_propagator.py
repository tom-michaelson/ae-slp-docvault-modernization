"""Context propagation for workflow logging metadata.

This module implements Temporal interceptors to propagate workflow context
(top-level workflow ID and type) through the workflow/activity hierarchy,
ensuring proper log aggregation even for deeply nested workflows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from temporalio import workflow

if TYPE_CHECKING:
    from collections.abc import Mapping

    from temporalio.api.common.v1 import Payload

# Import these at runtime as they're needed for actual execution
from collections.abc import Mapping

from temporalio.api.common.v1 import Payload
from temporalio.client import Interceptor as ClientInterceptor
from temporalio.client import OutboundInterceptor as ClientOutboundInterceptor
from temporalio.client import (
    StartWorkflowInput,
)
from temporalio.converter import PayloadConverter, default
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    ExecuteWorkflowInput,
    WorkflowInboundInterceptor,
    WorkflowInterceptorClassInput,
    WorkflowOutboundInterceptor,
)
from temporalio.worker import (
    Interceptor as WorkerInterceptor,
)

if TYPE_CHECKING:
    from temporalio.workflow import ExecuteActivityInput as WorkflowExecuteActivityInput

# Header keys for context propagation
HEADER_TOP_LEVEL_WORKFLOW_ID = "awa-top-level-workflow-id"
HEADER_TOP_LEVEL_WORKFLOW_TYPE = "awa-top-level-workflow-type"

# Global storage for context when headers don't work (sandbox mode)
# Key is workflow_id, value is dict with top_level_workflow_id and top_level_workflow_type
_workflow_context_storage: dict[str, dict[str, str | None]] = {}


class LoggingContextPropagator(ClientInterceptor, WorkerInterceptor):
    """Interceptor that propagates logging context through workflow/activity hierarchy.

    This interceptor ensures that top-level workflow information is available
    to all child workflows and activities, regardless of nesting depth.
    """

    def __init__(
        self,
        payload_converter: PayloadConverter | None = None,
    ) -> None:
        """Initialize the context propagator.

        Args:
            payload_converter: Optional payload converter for header serialization.
                               Defaults to Temporal's default converter.

        """
        self._payload_converter = payload_converter or default().payload_converter

    def _encode_header(self, value: str | None) -> Payload | None:
        """Encode a string value into a Temporal Payload for headers.

        Args:
            value: The string value to encode

        Returns:
            Encoded Payload or None if value is None

        """
        if value is None:
            return None
        payloads = self._payload_converter.to_payloads([value])
        return payloads[0] if payloads else None

    def _decode_header(self, payload: Payload | None) -> str | None:
        """Decode a Temporal Payload from headers into a string value.

        Args:
            payload: The Payload to decode

        Returns:
            Decoded string value or None if payload is None

        """
        if payload is None:
            return None
        values = self._payload_converter.from_payloads([payload])
        return values[0] if values else None

    def _add_context_to_headers(
        self,
        headers: Mapping[str, Payload],
        top_level_workflow_id: str | None = None,
        top_level_workflow_type: str | None = None,
    ) -> Mapping[str, Payload]:
        """Add logging context to headers.

        Args:
            headers: Existing headers
            top_level_workflow_id: Top-level workflow ID to propagate
            top_level_workflow_type: Top-level workflow type to propagate

        Returns:
            Updated headers with context

        """
        new_headers = dict(headers)

        if top_level_workflow_id:
            payload = self._encode_header(top_level_workflow_id)
            if payload:
                new_headers[HEADER_TOP_LEVEL_WORKFLOW_ID] = payload

        if top_level_workflow_type:
            payload = self._encode_header(top_level_workflow_type)
            if payload:
                new_headers[HEADER_TOP_LEVEL_WORKFLOW_TYPE] = payload

        return new_headers

    def _extract_context_from_headers(
        self,
        headers: Mapping[str, Payload],
    ) -> tuple[str | None, str | None]:
        """Extract logging context from headers.

        Args:
            headers: Headers containing context

        Returns:
            Tuple of (top_level_workflow_id, top_level_workflow_type)

        """
        top_level_workflow_id = None
        top_level_workflow_type = None

        if HEADER_TOP_LEVEL_WORKFLOW_ID in headers:
            top_level_workflow_id = self._decode_header(headers[HEADER_TOP_LEVEL_WORKFLOW_ID])

        if HEADER_TOP_LEVEL_WORKFLOW_TYPE in headers:
            top_level_workflow_type = self._decode_header(headers[HEADER_TOP_LEVEL_WORKFLOW_TYPE])

        return top_level_workflow_id, top_level_workflow_type

    # Client interceptor methods (for starting workflows from client)
    def intercept_client(self, next_: ClientOutboundInterceptor) -> ClientOutboundInterceptor:
        """Create client outbound interceptor."""
        return _LoggingClientOutboundInterceptor(next_, self)

    # Worker interceptor methods (for workflow and activity execution)
    def workflow_interceptor_class(
        self,
        input_: WorkflowInterceptorClassInput,  # noqa: ARG002
    ) -> type[WorkflowInboundInterceptor]:
        """Return workflow interceptor class for context propagation."""
        # Create a factory class that captures the root propagator
        root = self

        class _LoggingWorkflowInboundInterceptorWithRoot(_LoggingWorkflowInboundInterceptor):
            def __init__(self, next_: WorkflowInboundInterceptor) -> None:
                super().__init__(next_, root)

        return _LoggingWorkflowInboundInterceptorWithRoot

    def intercept_activity(self, next_: ActivityInboundInterceptor) -> ActivityInboundInterceptor:
        """Return activity interceptor for context propagation."""
        return _LoggingActivityInboundInterceptor(next_, self)


class _LoggingClientOutboundInterceptor(ClientOutboundInterceptor):
    """Client outbound interceptor for propagating context when starting workflows."""

    def __init__(self, next_: ClientOutboundInterceptor, root: LoggingContextPropagator) -> None:
        super().__init__(next_)
        self.root = root

    async def start_workflow(self, input_: StartWorkflowInput) -> Any:  # noqa: ANN401
        """Add context to headers when starting a workflow from client.

        For top-level workflows started from the client, we don't have
        parent context yet, so we just pass through.
        """
        # When starting from client, this is a top-level workflow
        # The workflow interceptor will set up the context
        return await super().start_workflow(input_)


class _LoggingWorkflowInboundInterceptor(WorkflowInboundInterceptor):
    """Workflow interceptor that sets up logging context and propagates to children."""

    def __init__(self, next_: WorkflowInboundInterceptor, root: LoggingContextPropagator) -> None:
        super().__init__(next_)
        self.top_level_workflow_id: str | None = None
        self.top_level_workflow_type: str | None = None
        # Use the root propagator passed in
        self.propagator: LoggingContextPropagator = root

    async def execute_workflow(self, input_: ExecuteWorkflowInput) -> Any:  # noqa: ANN401
        """Set up logging context for workflow execution."""
        # Get workflow info
        workflow_info = workflow.info()
        workflow_id = workflow_info.workflow_id
        workflow_type = workflow_info.workflow_type

        # Extract context from headers (if this is a child workflow)
        # Use the existing propagator instance
        parent_top_level_id, parent_top_level_type = self.propagator._extract_context_from_headers(  # noqa: SLF001
            input_.headers,
        )

        # Determine if this is a top-level workflow
        is_top_level = workflow_info.parent is None

        if is_top_level:
            # This is a top-level workflow
            self.top_level_workflow_id = workflow_id
            self.top_level_workflow_type = workflow_type
        else:
            # This is a child workflow - use parent's top-level info
            self.top_level_workflow_id = parent_top_level_id or workflow_id
            self.top_level_workflow_type = parent_top_level_type

        # Set up workflow context for logging
        # These imports need to be passed through the sandbox
        with workflow.unsafe.imports_passed_through():
            from loguru import logger as loguru_logger

            from awa.core.logger.logger import LoggerComponent
            from awa.core.logger.logger import get_logger as get_logger_func
            from awa.core.logger.workflow_context import (
                set_is_top_level,
                set_top_level_workflow_id,
                set_top_level_workflow_type,
                set_workflow_context,
            )
            from awa.core.utils.workflow_logging_utils import setup_workflow_file_logging

        set_workflow_context(workflow_id)
        set_top_level_workflow_id(self.top_level_workflow_id)
        set_top_level_workflow_type(self.top_level_workflow_type)
        set_is_top_level(is_top_level)

        # Store the context in global storage for activities to access
        # This is needed because sandbox mode prevents outbound interceptor from working
        _workflow_context_storage[workflow_id] = {
            "top_level_workflow_id": self.top_level_workflow_id,
            "top_level_workflow_type": self.top_level_workflow_type,
        }

        # Set up file logging (only for top-level workflows)
        file_handler_id = None
        if is_top_level:
            file_handler_id = setup_workflow_file_logging(
                workflow_id,
                self.top_level_workflow_id,
                workflow_type,
            )

        # Set up workflow logger
        workflow_bound_logger = get_logger_func(LoggerComponent.WORKFLOW).bind(
            workflow_id=workflow_id,
            top_level_workflow_id=self.top_level_workflow_id,
            top_level_workflow_type=self.top_level_workflow_type,
            is_top_level=is_top_level,
        )

        # Replace workflow.logger
        original_logger = workflow.logger
        workflow.logger = workflow_bound_logger

        # Log workflow start
        # Get worker logger from safe imports
        worker_logger = get_logger_func(LoggerComponent.WORKER)
        workflow_logger = worker_logger.bind(
            workflow_id=workflow_id,
            is_top_level=is_top_level,
            top_level_workflow_id=self.top_level_workflow_id,
        )

        try:
            workflow_logger.info(f"Starting workflow {workflow_type} (ID: {workflow_id})")
            result = await super().execute_workflow(input_)
            workflow_logger.info(f"Completed workflow {workflow_type} (ID: {workflow_id})")
            return result
        except Exception:
            workflow_logger.exception(f"Failed workflow {workflow_type} (ID: {workflow_id})")
            raise
        finally:
            # Restore original logger
            workflow.logger = original_logger
            # Clean up file logging
            if file_handler_id is not None:
                loguru_logger.remove(file_handler_id)
            # Clean up context storage to prevent memory leaks
            _workflow_context_storage.pop(workflow_id, None)

    def init(self, outbound: WorkflowOutboundInterceptor) -> None:
        """Initialize with outbound interceptor for child workflows and activities."""
        super().init(_LoggingWorkflowOutboundInterceptor(outbound, self))


class _LoggingWorkflowOutboundInterceptor(WorkflowOutboundInterceptor):
    """Workflow outbound interceptor for propagating context to children and activities."""

    def __init__(
        self,
        next_: WorkflowOutboundInterceptor,
        inbound: _LoggingWorkflowInboundInterceptor,
    ) -> None:
        super().__init__(next_)
        self.inbound = inbound

    async def execute_activity(self, input_: WorkflowExecuteActivityInput) -> Any:  # noqa: ANN401
        """Propagate context when executing activities."""
        # Add top-level context to activity headers
        # Always add headers if we have context, even for top-level workflows
        if self.inbound.propagator and self.inbound.top_level_workflow_id:
            input_.headers = self.inbound.propagator._add_context_to_headers(  # noqa: SLF001
                input_.headers,
                self.inbound.top_level_workflow_id,
                self.inbound.top_level_workflow_type,
            )

        return await super().execute_activity(input_)

    async def start_child_workflow(self, input_: Any) -> Any:  # noqa: ANN401
        """Propagate context when starting child workflows."""
        # Add top-level context to child workflow headers
        if self.inbound.propagator and self.inbound.top_level_workflow_id:
            # Ensure headers exist
            if not hasattr(input_, "headers"):
                input_.headers = {}
            input_.headers = self.inbound.propagator._add_context_to_headers(  # noqa: SLF001
                input_.headers,
                self.inbound.top_level_workflow_id,
                self.inbound.top_level_workflow_type,
            )
        return await super().start_child_workflow(input_)


class _LoggingActivityInboundInterceptor(ActivityInboundInterceptor):
    """Activity interceptor that sets up logging context from propagated headers."""

    def __init__(self, next_: ActivityInboundInterceptor, root: LoggingContextPropagator) -> None:
        super().__init__(next_)
        self.root = root

    async def execute_activity(self, input_: ExecuteActivityInput) -> Any:  # noqa: ANN401
        """Set up logging context for activity execution."""
        from temporalio import activity

        from awa.core.logger.logger import LoggerComponent, get_logger

        # Get activity info
        activity_info = activity.info()
        workflow_id = activity_info.workflow_id

        # Try to get context from headers first
        top_level_workflow_id, top_level_workflow_type = self.root._extract_context_from_headers(  # noqa: SLF001
            input_.headers,
        )

        # If headers are empty, try to get from global storage
        # This is needed because sandbox mode prevents outbound interceptor from adding headers
        if not top_level_workflow_id:
            context = _workflow_context_storage.get(workflow_id, {})
            top_level_workflow_id = context.get("top_level_workflow_id")
            top_level_workflow_type = context.get("top_level_workflow_type")

        # If no context in headers, this activity was called by a top-level workflow
        if not top_level_workflow_id:
            top_level_workflow_id = workflow_id
            # Note: We can't determine the workflow type from activity info alone
            # but the SocketIO server will resolve it if needed

        # Determine if this is from a top-level workflow
        is_top_level = top_level_workflow_id == workflow_id

        # Set up activity logger with context
        activity_bound_logger = get_logger(LoggerComponent.ACTIVITY).bind(
            workflow_id=workflow_id,
            top_level_workflow_id=top_level_workflow_id,
            top_level_workflow_type=top_level_workflow_type,
            is_top_level=is_top_level,
        )

        # Replace activity.logger
        original_logger = activity.logger
        activity.logger = activity_bound_logger

        try:
            result = await super().execute_activity(input_)
            return result
        finally:
            # Restore original logger
            activity.logger = original_logger
