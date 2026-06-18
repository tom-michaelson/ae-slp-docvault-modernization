"""Human-in-the-Loop child workflow for reusable human interactions.

Implements blocking, non-blocking, and chat interaction patterns.
"""

from __future__ import annotations

from temporalio import workflow

from awa.core.activities.socket_activity import emit_hitl_chat_message
from awa.core.engine.temporal_client import WorkflowExecutionError
from awa.core.models.hitl import HITLChatMessage, HITLContext, HITLInput, HITLOutput, HITLResponse
from awa.sdk import constants


@workflow.defn(name=constants.WORKFLOW_HITL)
class HITLChildWorkflow:
    """Reusable workflow enabling human interaction within a parent workflow.

    Patterns:
      * Blocking (default): waits for a response or optional timeout
      * Non-blocking: returns immediately (parent polls via queries or signals later)
      * Chat mode: maintains a chat history of system + human messages
    """

    # State variables (instance initialized)
    response_received: bool
    response: HITLResponse | None
    context: HITLContext | None
    pending_socket_messages: list[HITLChatMessage]
    new_user_input_received: bool
    # chat_history intentionally not declared with mutable default at class level to avoid sharing across instances

    def __init__(self) -> None:
        self.response_received = False
        self.response = None
        self.context = None
        self.chat_history: list[HITLChatMessage] = []
        self.pending_socket_messages: list[HITLChatMessage] = []
        self.new_user_input_received = False

    @workflow.run
    async def run(self, input_data: HITLInput) -> HITLOutput:
        """Execute the HITL workflow with the provided input configuration."""
        # Do NOT reset response/response_received so pre-existing state (tests or
        # replays) is preserved when already set.
        self.context = HITLContext(
            title=input_data.title,
            description=input_data.description,
            markdown=input_data.markdown,
            input_schema=input_data.input_schema,
            attachments=input_data.attachments,
            chat_mode=input_data.chat_mode,
        )

        timeout = input_data.timeout_seconds
        use_timeout = timeout is not None and timeout > 0

        # Background task to emit pending socket messages
        async def emit_pending_messages() -> None:
            """Emit queued system messages to Socket.IO."""
            workflow_id = workflow.info().workflow_id
            workflow.logger.info(f"Starting socket emission background task for {workflow_id}")

            while not self.response_received:
                if self.pending_socket_messages:
                    workflow.logger.info(f"Processing {len(self.pending_socket_messages)} pending messages")

                    # Process all pending messages
                    messages_to_emit = self.pending_socket_messages.copy()
                    self.pending_socket_messages.clear()

                    for msg in messages_to_emit:
                        try:
                            await workflow.execute_activity(
                                emit_hitl_chat_message,
                                workflow_id,
                                msg.message,
                                msg.data,
                                msg.timestamp,
                                schedule_to_close_timeout=workflow.timedelta(seconds=5),
                            )
                            workflow.logger.info(f"Emitted message to socket: {msg.message[:50]}...")
                        except Exception as e:
                            workflow.logger.error(f"Failed to emit message: {e}")
                            raise WorkflowExecutionError from e

                # Check more frequently for messages
                await workflow.sleep(0.01)

        # Start background task for socket emission immediately
        emit_task = workflow.asyncio.create_task(emit_pending_messages())

        # Blocking pattern: wait for human input or timeout
        try:
            if not input_data.non_blocking and not self.response_received:
                if use_timeout:
                    try:
                        await workflow.wait_condition(lambda: self.response_received, timeout=timeout)
                    except TimeoutError:
                        return HITLOutput(response=None, timed_out=True, chat_history=self.chat_history)
                else:
                    await workflow.wait_condition(lambda: self.response_received)
        finally:
            # Cancel the background task
            emit_task.cancel()

        # Non-blocking (or already satisfied blocking) returns current state
        return HITLOutput(response=self.response, timed_out=False, chat_history=self.chat_history)

    # ---------------- Signals -----------------
    @workflow.signal
    def submit_response(self, response: HITLResponse) -> None:
        """Submit the final (or current) human response."""
        self.response = response
        self.response_received = True

    @workflow.signal
    def add_system_message(self, payload: HITLChatMessage) -> None:
        """Add a system/authored message to chat history (chat mode only).

        Accepts a partial HITLChatMessage (message + optional data). Timestamp
        and is_human are assigned/overridden.
        """
        if self.context and self.context.chat_mode:
            ts = workflow.now()
            if hasattr(ts, "__await__"):
                ts = workflow.now()

            chat_message = HITLChatMessage(
                message=payload.message,
                timestamp=ts,  # type: ignore[arg-type]
                is_human=False,
                data=payload.data,
            )
            self.chat_history.append(chat_message)

            # Queue for socket emission (processed by main workflow loop)
            self.pending_socket_messages.append(chat_message)

    @workflow.signal
    def add_human_message(self, payload: HITLChatMessage) -> None:
        """Add a human message to chat history (chat mode only).

        Accepts a partial HITLChatMessage (message + optional data). Timestamp
        and is_human are assigned/overridden.
        """
        if self.context and self.context.chat_mode:
            ts = workflow.now()
            if hasattr(ts, "__await__"):
                ts = workflow.now()

            chat_message = HITLChatMessage(
                message=payload.message,
                timestamp=ts,  # type: ignore[arg-type]
                is_human=True,
                data=payload.data,
            )
            self.chat_history.append(chat_message)

            # Queue for socket emission (processed by main workflow loop)
            self.pending_socket_messages.append(chat_message)

            # Set flag for parent workflow to detect new user input
            self.new_user_input_received = True

    # ---------------- Queries -----------------
    @workflow.query
    def get_context(self) -> HITLContext | None:
        """Return static context for this HITL interaction."""
        return self.context

    @workflow.query
    def get_chat_history(self) -> list[HITLChatMessage]:
        """Return accumulated chat messages (empty if not chat mode)."""
        return self.chat_history

    @workflow.query
    def is_response_received(self) -> bool:
        """Return True if a response has been received via signal."""
        return self.response_received

    @workflow.query
    def has_new_user_input(self) -> bool:
        """Return True if new user input has been received since last check."""
        return self.new_user_input_received

    @workflow.signal
    def mark_user_input_processed(self) -> None:
        """Mark that the parent workflow has processed the new user input."""
        self.new_user_input_received = False
