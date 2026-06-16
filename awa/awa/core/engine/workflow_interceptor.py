"""Workflow interceptor for logging workflow start/end events in core AWA.

This module now uses LoggingContextPropagator for full context propagation.
The legacy interceptor classes are kept for backward compatibility but delegate
to the context propagator.
"""

from typing import Any

from temporalio.worker import Interceptor, WorkflowInboundInterceptor, WorkflowInterceptorClassInput

from awa.core.logger.context_propagator import LoggingContextPropagator


class LoggingWorkflowInterceptor(Interceptor):
    """Workflow interceptor that adds logging with full context propagation.

    This interceptor now uses LoggingContextPropagator to properly propagate
    top-level workflow context through the entire workflow/activity hierarchy,
    supporting arbitrary nesting depths.
    """

    def __init__(self) -> None:
        """Initialize the interceptor with context propagator."""
        self._context_propagator = LoggingContextPropagator()

    def workflow_interceptor_class(self, input_: WorkflowInterceptorClassInput) -> type[WorkflowInboundInterceptor]:
        """Return the workflow interceptor class from context propagator."""
        return self._context_propagator.workflow_interceptor_class(input_)

    def intercept_activity(self, next_: Any) -> Any:  # noqa: ANN401
        """Return the activity interceptor from context propagator."""
        return self._context_propagator.intercept_activity(next_)
