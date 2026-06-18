from awa.core.activities.agent_modes.claude_agent import ClaudeAgent
from awa.core.activities.agent_modes.codex_agent import CodexAgent
from awa.core.activities.agent_modes.gemini_agent import GeminiAgent
from awa.core.activities.agent_modes.github_copilot_agent import GithubCopilotAgent
from awa.core.activities.agent_modes.goose_agent import GooseAgent
from awa.core.activities.agent_modes.opencode_agent import OpenCodeAgent
from awa.core.activities.agent_modes.pydantic_ai_agent import PydanticAIAgent
from awa.core.activities.agent_modes.q_agent import QAgent
from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum


@staticmethod
def create_agent(
    provider: AgentProviderEnum | str | None,
    mode: AgentModeEnum | None,
) -> AgentModeBase:
    """Create an agent mode instance based on the provider and mode.

    Args:
        provider: The agent provider to use (e.g. CLAUDE, OPENHANDS)
        mode: The agent mode to use (e.g. ANALYZE, ACT)

    Returns:
        An instance of AgentModeBase for the specified provider and mode

    Raises:
        ValueError: If the provider or mode is invalid/unsupported

    """
    if not provider:
        raise ValueError("Agent provider must be specified")

    if not mode:
        raise ValueError("Agent mode must be specified")

    try:
        provider_enum = AgentProviderEnum(provider) if isinstance(provider, str) else provider
    except ValueError as e:
        raise ValueError(f"Unknown agent provider: {provider}") from e

    match provider_enum:
        case AgentProviderEnum.CLAUDE:
            return ClaudeAgent()
        case AgentProviderEnum.GOOSE:
            return GooseAgent()
        case AgentProviderEnum.CODEX:
            return CodexAgent()
        case AgentProviderEnum.GEMINI:
            return GeminiAgent()
        case AgentProviderEnum.Q:
            return QAgent()
        case AgentProviderEnum.OPENCODE:
            return OpenCodeAgent()
        case AgentProviderEnum.GITHUB_COPILOT:
            return GithubCopilotAgent()
        case AgentProviderEnum.PYDANTIC_AI | AgentProviderEnum.DEFAULT:
            return PydanticAIAgent()

        case _:
            error_msg = f"Unknown agent provider: {provider}"
            raise ValueError(error_msg)
