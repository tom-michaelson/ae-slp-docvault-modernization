from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema

from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum
from awa.sdk.models.build_prompt_params import BuildPromptParams


class Repo(BaseModel):
    path: str = Field(default="")
    branch: str = Field(default="")


class McpTool(BaseModel):
    server_name: str = Field(default="", alias="server")
    tool_names: list[str] = Field(default=[], alias="tools")


class McpServer(BaseModel):
    mcp_json: str | SkipJsonSchema[None] = Field(default=None)
    allowed: list[McpTool] | SkipJsonSchema[None] = Field(default=None)


class AgentConfiguration(BaseModel):
    mode: AgentModeEnum = Field(default=AgentModeEnum.UNKNOWN)
    provider: AgentProviderEnum | SkipJsonSchema[str] = Field(default=AgentProviderEnum.UNKNOWN)
    prompt: str | SkipJsonSchema[None] = Field(default="")
    build_prompt_params: BuildPromptParams | SkipJsonSchema[None] = Field(default=None)
    """Params for the build-prompt workflow.
    If build_prompt_params is set, prompt will be ignored.
    """
    command_file_path: str | SkipJsonSchema[None] = Field(default=None)
    working_directory: str | SkipJsonSchema[None] = Field(default=None)
    mcp: McpServer | SkipJsonSchema[None] = Field(default=None)
    initialize: bool | SkipJsonSchema[None] = Field(default=True)
    timeout_seconds: int | SkipJsonSchema[None] = Field(default=None)
    output_schema: str | SkipJsonSchema[None] = Field(default=None)
    session_id: str | SkipJsonSchema[None] = Field(default=None)
    stream_enabled: bool | SkipJsonSchema[None] = Field(default=False)
    stream_session_id: str | SkipJsonSchema[None] = Field(default=None)
    parent_session_id: str | SkipJsonSchema[None] = Field(default=None)
