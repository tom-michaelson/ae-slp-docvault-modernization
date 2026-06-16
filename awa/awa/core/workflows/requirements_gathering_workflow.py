"""Requirements Gathering workflow demonstrating AWA's chat capabilities.

This workflow shows how to use the Human-in-the-Loop (HITL) child workflow for
interactive requirements gathering, generating structured outputs from natural
language conversations.
"""

from __future__ import annotations

from temporalio import workflow

from awa.core.models.hitl import HITLChatMessage, HITLInput, HITLOutput
from awa.core.models.requirements import RequirementsGatheringInput, RequirementsGatheringOutput
from awa.core.workflows.hitl_child_workflow import HITLChildWorkflow
from awa.sdk import constants


@workflow.defn(name=constants.WORKFLOW_GATHER_REQUIREMENTS)
class RequirementsGatheringWorkflow:
    """Interactive requirements gathering workflow using chat mode.

    Demonstrates:
    - Multi-turn conversation with human users
    - Structured output generation from natural language
    - Integration with HITL child workflow in chat mode
    - Dynamic questioning based on user responses
    """

    def __init__(self) -> None:
        self.user_message_received = False
        self.conversation_complete = False
        self.conversation_rounds = 0
        self.max_conversation_rounds = 5
        self.latest_user_message = ""
        self.conversation_context = ""

    @workflow.run
    async def run(self, input_data: RequirementsGatheringInput) -> RequirementsGatheringOutput:
        """Execute the requirements gathering workflow."""
        # Start HITL child workflow in chat mode for interactive conversation
        hitl_input = HITLInput(
            title="Requirements Gathering",
            description="Let's gather requirements for your feature. I'll ask questions to understand what you need.",
            markdown=f"## Initial Request\n\n{input_data.initial_description}",
            chat_mode=True,
            non_blocking=False,
            timeout_seconds=input_data.timeout_seconds,
        )

        # Execute child workflow to handle human interaction
        hitl_handle = await workflow.start_child_workflow(
            HITLChildWorkflow.run,
            hitl_input,
            id=f"hitl-requirements-{workflow.info().workflow_id}",
        )

        # Initialize conversation context
        welcome_message = """
        I'll help you gather comprehensive requirements for your feature. Let's start with some clarifying questions
         based on your initial description.
        """
        self.conversation_context = f"System: {welcome_message}"

        # Send initial system message welcoming user
        await hitl_handle.signal(
            "add_system_message",
            HITLChatMessage(
                message=welcome_message,
                data=None,
            ),
        )

        # Analyze initial description and generate first set of questions
        initial_questions = await workflow.execute_activity(
            activity=constants.ACTIVITY_GENERATE_CLARIFYING_QUESTIONS,
            arg=input_data.initial_description,
            schedule_to_close_timeout=workflow.timedelta(minutes=2),
        )

        # Send clarifying questions to user
        questions_text = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(initial_questions["questions"]))
        questions_message = f"""
        Here are some questions to help me understand your requirements better:\n\n{questions_text}\n\n
        Please answer as many as you can, and feel free to add any additional context.
        """

        # Add to conversation context
        self.conversation_context += f"\nSystem: {questions_message}"

        await hitl_handle.signal(
            "add_system_message",
            HITLChatMessage(
                message=questions_message,
                data=None,
            ),
        )

        # Interactive conversation loop - listen for user messages and respond
        while self.conversation_rounds < self.max_conversation_rounds and not self.conversation_complete:
            self.conversation_rounds += 1
            workflow.logger.info(f"Starting conversation round {self.conversation_rounds}")

            # Wait for user message or completion
            try:
                await workflow.wait_condition(
                    lambda: self.user_message_received or self.conversation_complete,
                    timeout=workflow.timedelta(minutes=10),
                )
            except TimeoutError:
                workflow.logger.info(f"Conversation round {self.conversation_rounds} timed out")
                break

            if self.conversation_complete:
                workflow.logger.info("Conversation marked as complete")
                break

            if self.user_message_received:
                workflow.logger.info(f"Processing user message for follow-up questions: {self.latest_user_message}")
                # Reset the flag and update conversation context
                self.user_message_received = False

                # Generate contextual follow-up questions using BAML
                follow_up_questions = await workflow.execute_activity(
                    activity=constants.ACTIVITY_GENERATE_CONTEXTUAL_FOLLOW_UP,
                    arg={
                        "original_request": input_data.initial_description,
                        "conversation_history": self.conversation_context,
                        "latest_user_response": self.latest_user_message,
                    },
                    schedule_to_close_timeout=workflow.timedelta(minutes=2),
                )

                if follow_up_questions["questions"]:
                    questions_text = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(follow_up_questions["questions"]))
                    follow_up_message = f"""
                    Thank you for that information! I have a few more questions to help refine the requirements:\n\n
                    {questions_text}\n\nFeel free to answer what you can, or let me know if you think we have enough
                     information to proceed.
                    """
                else:
                    follow_up_message = """Thank you for that information! That helps clarify things. Do you have any
                     other requirements or details you'd like to add, or shall we proceed with analyzing what we have?
                    """

                # Add to conversation context and send follow-up message
                self.conversation_context += f"\nSystem: {follow_up_message}"

                await hitl_handle.signal(
                    "add_system_message",
                    HITLChatMessage(
                        message=follow_up_message,
                        data=None,
                    ),
                )

        workflow.logger.info("Conversation loop completed, waiting for final HITL output")

        # Get final chat history and check if we have a formal completion
        final_hitl_output: HITLOutput = await hitl_handle

        if not final_hitl_output.chat_history:
            return RequirementsGatheringOutput(
                requirements=None,
                user_stories=None,
                acceptance_criteria=None,
                technical_notes=None,
                chat_history=[],
                success=False,
                error_message="No conversation occurred",
            )

        # Process the full conversation to extract structured requirements
        conversation_text = "\n".join(
            [f"{'User' if msg.is_human else 'System'}: {msg.message}" for msg in final_hitl_output.chat_history],
        )

        structured_requirements = await workflow.execute_activity(
            activity=constants.ACTIVITY_ANALYZE_REQUIREMENTS,
            arg=conversation_text,
            schedule_to_close_timeout=workflow.timedelta(minutes=5),
        )

        return RequirementsGatheringOutput(
            requirements=structured_requirements["requirements"],
            user_stories=structured_requirements["user_stories"],
            acceptance_criteria=structured_requirements["acceptance_criteria"],
            technical_notes=structured_requirements["technical_notes"],
            chat_history=final_hitl_output.chat_history,
            success=True,
            error_message=None,
        )

    # ---------------- Signals for external communication ----------------
    @workflow.signal
    def notify_user_message_received(self, user_message: str = "") -> None:
        """Signal that a user message was received and needs processing."""
        self.user_message_received = True
        self.latest_user_message = user_message
        self.conversation_context += f"\nUser: {user_message}"
        workflow.logger.info(f"Received signal: user message received - {user_message}")

    @workflow.signal
    def mark_conversation_complete(self) -> None:
        """Signal that the conversation should be considered complete."""
        self.conversation_complete = True
        workflow.logger.info("Received signal: conversation marked as complete")
