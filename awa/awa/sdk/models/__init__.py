from pydantic import BaseModel, Field

from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum


class HelloWorldInput(BaseModel):
    name: str = Field(description="The name of the person to greet", title="Name")


class HelloPoemInput(BaseModel):
    noun: str = Field(description="The noun to use in the poem", title="Noun")
    verb: str = Field(description="The verb to use in the poem", title="Verb")
    adjective: str = Field(description="The adjective to use in the poem", title="Adjective")


class HelloPoemAgentInput(HelloPoemInput):
    provider: AgentProviderEnum = Field(
        description="The agent provider to use",
        title="Provider",
        default=AgentProviderEnum.DEFAULT,
    )
