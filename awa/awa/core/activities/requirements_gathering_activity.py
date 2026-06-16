"""Activities for requirements gathering workflow."""

from pathlib import Path

from temporalio import activity

from awa.core.models.requirements import ClarifyingQuestions, StructuredRequirements
from awa.core.utils.config_loader import ConfigLoader
from awa.core.utils.llm_invoker import LlmInvoker
from awa.sdk import constants


@activity.defn(name=constants.ACTIVITY_GENERATE_CLARIFYING_QUESTIONS)
async def generate_clarifying_questions(initial_description: str) -> ClarifyingQuestions:
    """Generate clarifying questions based on initial feature description."""
    app_config = ConfigLoader.get_config()
    llm_invoker = LlmInvoker(
        config=app_config,
        baml_src_dir=Path(__file__).parent.parent / "baml_src",
    )

    result = await llm_invoker.execute_transform(
        model_name=app_config.llm.default_model,
        baml_function_name="GenerateClarifyingQuestions",
        request=initial_description,
    )

    return result


@activity.defn(name=constants.ACTIVITY_GENERATE_CONTEXTUAL_FOLLOW_UP)
async def generate_contextual_follow_up(context: dict) -> ClarifyingQuestions:
    """Generate contextual follow-up questions based on conversation history."""
    app_config = ConfigLoader.get_config()
    llm_invoker = LlmInvoker(
        config=app_config,
        baml_src_dir=Path(__file__).parent.parent / "baml_src",
    )

    result = await llm_invoker.execute_transform(
        model_name=app_config.llm.default_model,
        baml_function_name="GenerateContextualFollowUpQuestions",
        request=context,
    )

    return result


@activity.defn(name=constants.ACTIVITY_ANALYZE_REQUIREMENTS)
async def analyze_requirements(conversation_text: str) -> StructuredRequirements:
    """Analyze chat conversation to extract structured requirements."""
    app_config = ConfigLoader.get_config()
    llm_invoker = LlmInvoker(
        config=app_config,
        baml_src_dir=Path(__file__).parent.parent / "baml_src",
    )

    result = await llm_invoker.execute_transform(
        model_name=app_config.llm.default_model,
        baml_function_name="AnalyzeRequirements",
        request=conversation_text,
    )

    return result
