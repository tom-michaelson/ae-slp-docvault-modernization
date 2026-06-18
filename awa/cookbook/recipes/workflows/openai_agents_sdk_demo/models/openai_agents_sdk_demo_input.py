"""Input model for the OpenAI Agents Demo Workflow."""

from pydantic import BaseModel, Field


class OpenAIAgentsSdkDemoInput(BaseModel):
    """Input parameters for the OpenAI Agents Demo Workflow.

    This model defines the input schema for creating haikus using the OpenAI Agents workflow.
    """

    topic: str = Field(
        default="autumn leaves",
        description="The topic for the haiku poem. Can be a Jira issue ID or any subject.",
    )
