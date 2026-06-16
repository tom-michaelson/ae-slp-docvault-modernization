"""Models for requirements gathering workflow."""

from pydantic import BaseModel
from pydantic.json_schema import SkipJsonSchema

from awa.core.models.hitl import HITLChatMessage


class RequirementsGatheringInput(BaseModel):
    """Input for requirements gathering workflow."""

    initial_description: str
    timeout_seconds: int | SkipJsonSchema[None] = 3600  # 1 hour default


class RequirementsGatheringOutput(BaseModel):
    """Output from requirements gathering workflow."""

    requirements: list[str] | None = None
    user_stories: list[str] | None = None
    acceptance_criteria: list[str] | None = None
    technical_notes: list[str] | None = None
    chat_history: list[HITLChatMessage] = []
    success: bool = False
    error_message: str | None = None


class ClarifyingQuestions(BaseModel):
    """Generated clarifying questions for requirements gathering."""

    questions: list[str]


class StructuredRequirements(BaseModel):
    """Structured requirements extracted from conversation."""

    requirements: list[str]
    user_stories: list[str]
    acceptance_criteria: list[str]
    technical_notes: list[str]
