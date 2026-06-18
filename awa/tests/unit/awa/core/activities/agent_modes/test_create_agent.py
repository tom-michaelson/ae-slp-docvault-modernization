"""Unit tests for the create_agent factory function."""

import pytest

from awa.core.activities.agent_modes.claude_agent import ClaudeAgent
from awa.core.activities.agent_modes.codex_agent import CodexAgent
from awa.core.activities.agent_modes.create_agent import create_agent
from awa.core.activities.agent_modes.gemini_agent import GeminiAgent
from awa.core.activities.agent_modes.github_copilot_agent import GithubCopilotAgent
from awa.core.activities.agent_modes.goose_agent import GooseAgent
from awa.core.activities.agent_modes.opencode_agent import OpenCodeAgent
from awa.core.activities.agent_modes.pydantic_ai_agent import PydanticAIAgent
from awa.core.activities.agent_modes.q_agent import QAgent
from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum


@pytest.mark.parametrize(
    ("provider", "mode", "expected_agent_class"),
    [
        # Test each provider with both enum and string forms, and both modes
        (AgentProviderEnum.CLAUDE, AgentModeEnum.ACT, ClaudeAgent),
        ("claude", AgentModeEnum.ANALYZE, ClaudeAgent),
        (AgentProviderEnum.GOOSE, AgentModeEnum.ACT, GooseAgent),
        ("goose", AgentModeEnum.ANALYZE, GooseAgent),
        (AgentProviderEnum.CODEX, AgentModeEnum.ACT, CodexAgent),
        ("codex", AgentModeEnum.ANALYZE, CodexAgent),
        (AgentProviderEnum.GEMINI, AgentModeEnum.ACT, GeminiAgent),
        ("gemini", AgentModeEnum.ANALYZE, GeminiAgent),
        (AgentProviderEnum.Q, AgentModeEnum.ACT, QAgent),
        ("q", AgentModeEnum.ANALYZE, QAgent),
        (AgentProviderEnum.OPENCODE, AgentModeEnum.ACT, OpenCodeAgent),
        ("opencode", AgentModeEnum.ANALYZE, OpenCodeAgent),
        (AgentProviderEnum.GITHUB_COPILOT, AgentModeEnum.ACT, GithubCopilotAgent),
        ("github_copilot", AgentModeEnum.ANALYZE, GithubCopilotAgent),
        (AgentProviderEnum.PYDANTIC_AI, AgentModeEnum.ANALYZE, PydanticAIAgent),
        ("pydantic_ai", AgentModeEnum.ACT, PydanticAIAgent),
        (AgentProviderEnum.DEFAULT, AgentModeEnum.ACT, PydanticAIAgent),
        ("default", AgentModeEnum.ANALYZE, PydanticAIAgent),
    ],
)
def test_create_agent_success(
    provider: str | AgentProviderEnum,
    mode: AgentModeEnum,
    expected_agent_class: type[AgentModeBase],
) -> None:
    """Test successful creation of agents for all supported providers."""
    agent = create_agent(provider, mode)
    assert isinstance(agent, expected_agent_class)


def test_create_agent_no_provider() -> None:
    """Test that a ValueError is raised if no provider is specified."""
    with pytest.raises(ValueError, match="Agent provider must be specified"):
        create_agent(None, AgentModeEnum.ACT)


def test_create_agent_empty_provider() -> None:
    """Test that a ValueError is raised if empty string provider is specified."""
    with pytest.raises(ValueError, match="Agent provider must be specified"):
        create_agent("", AgentModeEnum.ACT)


def test_create_agent_no_mode() -> None:
    """Test that a ValueError is raised if no mode is specified."""
    with pytest.raises(ValueError, match="Agent mode must be specified"):
        create_agent(AgentProviderEnum.CLAUDE, None)


def test_create_agent_unknown_provider() -> None:
    """Test that a ValueError is raised for an unknown provider string."""
    with pytest.raises(ValueError, match="Unknown agent provider: wat"):
        create_agent("wat", AgentModeEnum.ACT)


def test_create_agent_unknown_provider_enum() -> None:
    """Test that a ValueError is raised for an unknown provider enum."""
    with pytest.raises(ValueError, match="Unknown agent provider: unknown"):
        create_agent(AgentProviderEnum.UNKNOWN, AgentModeEnum.ACT)


def test_create_agent_case_sensitivity() -> None:
    """Test that string providers are case-sensitive."""
    # Test that case mismatches raise errors (enum values are case-sensitive)
    with pytest.raises(ValueError, match="Unknown agent provider: CLAUDE"):
        create_agent("CLAUDE", AgentModeEnum.ACT)

    with pytest.raises(ValueError, match="Unknown agent provider: Claude"):
        create_agent("Claude", AgentModeEnum.ACT)

    # Test that correct case works
    agent = create_agent("claude", AgentModeEnum.ACT)
    assert isinstance(agent, ClaudeAgent)


def test_create_agent_returns_new_instances() -> None:
    """Test that create_agent returns new instances each time."""
    agent1 = create_agent(AgentProviderEnum.CLAUDE, AgentModeEnum.ACT)
    agent2 = create_agent(AgentProviderEnum.CLAUDE, AgentModeEnum.ACT)

    # Should be different instances
    assert agent1 is not agent2
    # But same type
    assert type(agent1) is type(agent2)
    assert isinstance(agent1, ClaudeAgent)
    assert isinstance(agent2, ClaudeAgent)


def test_create_agent_all_providers_implement_base() -> None:
    """Test that all created agents properly implement AgentModeBase."""
    providers = [
        AgentProviderEnum.CLAUDE,
        AgentProviderEnum.GOOSE,
        AgentProviderEnum.CODEX,
        AgentProviderEnum.GEMINI,
        AgentProviderEnum.Q,
        AgentProviderEnum.OPENCODE,
        AgentProviderEnum.GITHUB_COPILOT,
        AgentProviderEnum.DEFAULT,
        AgentProviderEnum.PYDANTIC_AI,
    ]

    for provider in providers:
        agent = create_agent(provider, AgentModeEnum.ACT)
        assert isinstance(agent, AgentModeBase)

        # Test that required methods exist
        assert hasattr(agent, "execute_command")
        assert hasattr(agent, "execute_prompt")
        assert hasattr(agent, "stream_output")
        assert hasattr(agent, "get_log_files")
        assert hasattr(agent, "cleanup")


def test_default_and_pydantic_ai_return_same_type() -> None:
    """Test that DEFAULT and PYDANTIC_AI providers return the same agent type."""
    default_agent = create_agent(AgentProviderEnum.DEFAULT, AgentModeEnum.ACT)
    pydantic_ai_agent = create_agent(AgentProviderEnum.PYDANTIC_AI, AgentModeEnum.ACT)

    # Both should be PydanticAIAgent instances
    assert isinstance(default_agent, PydanticAIAgent)
    assert isinstance(pydantic_ai_agent, PydanticAIAgent)

    # Both should be the same type
    assert type(default_agent) is type(pydantic_ai_agent)

    # Should be different instances though
    assert default_agent is not pydantic_ai_agent


def test_default_with_string_provider() -> None:
    """Test that 'default' string provider works correctly."""
    agent = create_agent("default", AgentModeEnum.ANALYZE)
    assert isinstance(agent, PydanticAIAgent)

    # Should be the same type as using the enum
    enum_agent = create_agent(AgentProviderEnum.DEFAULT, AgentModeEnum.ANALYZE)
    assert type(agent) is type(enum_agent)
