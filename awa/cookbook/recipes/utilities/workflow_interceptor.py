"""Workflow interceptor for cookbook recipes.

This module now uses LoggingContextPropagator for full context propagation.
The legacy interceptor classes are kept for backward compatibility but delegate
to the context propagator.
"""

from typing import Any

from temporalio.worker import Interceptor, WorkflowInboundInterceptor, WorkflowInterceptorClassInput

from cookbook.recipes.utilities.context_propagator import LoggingContextPropagator


class LoggingWorkflowInterceptor(Interceptor):
    """Workflow interceptor that adds logging with full context propagation.

    This interceptor now uses LoggingContextPropagator to properly propagate
    top-level workflow context through the entire workflow/activity hierarchy,
    supporting arbitrary nesting depths.
    """

    def __init__(self) -> None:
        """Initialize the interceptor with context propagator."""
        self._context_propagator = LoggingContextPropagator()

    def workflow_interceptor_class(
        self,
        workflow_input: WorkflowInterceptorClassInput,
    ) -> type[WorkflowInboundInterceptor]:
        """Return the workflow interceptor class from context propagator."""
        return self._context_propagator.workflow_interceptor_class(workflow_input)

    def intercept_activity(self, next_interceptor) -> Any:  # noqa: ANN001, ANN401
        """Return the activity interceptor from context propagator."""
        return self._context_propagator.intercept_activity(next_interceptor)
