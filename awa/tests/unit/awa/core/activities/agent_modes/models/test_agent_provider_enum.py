"""Unit tests for the AgentProviderEnum."""

import pytest

from awa.sdk.models.agent_modes.agent_provider_enum import AgentProviderEnum


class TestAgentProviderEnum:
    """Test cases for AgentProviderEnum."""

    def test_enum_values_exist(self) -> None:
        """Test that all expected enum values exist."""
        assert AgentProviderEnum.CLAUDE == "claude"
        assert AgentProviderEnum.GOOSE == "goose"
        assert AgentProviderEnum.CODEX == "codex"
        assert AgentProviderEnum.GEMINI == "gemini"
        assert AgentProviderEnum.Q == "q"
        assert AgentProviderEnum.OPENCODE == "opencode"
        assert AgentProviderEnum.DEFAULT == "default"
        assert AgentProviderEnum.PYDANTIC_AI == "pydantic_ai"
        assert AgentProviderEnum.UNKNOWN == "unknown"

    def test_enum_values_are_strings(self) -> None:
        """Test that all enum values are strings."""
        for enum_value in AgentProviderEnum:
            assert isinstance(enum_value.value, str)
            assert isinstance(enum_value, str)  # StrEnum behavior

    def test_enum_from_string_conversion(self) -> None:
        """Test that enum values can be created from string values."""
        assert AgentProviderEnum("claude") == AgentProviderEnum.CLAUDE
        assert AgentProviderEnum("goose") == AgentProviderEnum.GOOSE
        assert AgentProviderEnum("codex") == AgentProviderEnum.CODEX
        assert AgentProviderEnum("gemini") == AgentProviderEnum.GEMINI
        assert AgentProviderEnum("q") == AgentProviderEnum.Q
        assert AgentProviderEnum("opencode") == AgentProviderEnum.OPENCODE
        assert AgentProviderEnum("default") == AgentProviderEnum.DEFAULT
        assert AgentProviderEnum("pydantic_ai") == AgentProviderEnum.PYDANTIC_AI
        assert AgentProviderEnum("unknown") == AgentProviderEnum.UNKNOWN

    def test_enum_string_comparison(self) -> None:
        """Test that enum values can be compared with strings."""
        assert AgentProviderEnum.CLAUDE == "claude"
        assert AgentProviderEnum.GOOSE == "goose"
        assert AgentProviderEnum.CODEX == "codex"
        assert AgentProviderEnum.GEMINI == "gemini"
        assert AgentProviderEnum.Q == "q"
        assert AgentProviderEnum.OPENCODE == "opencode"
        assert AgentProviderEnum.DEFAULT == "default"
        assert AgentProviderEnum.PYDANTIC_AI == "pydantic_ai"
        assert AgentProviderEnum.UNKNOWN == "unknown"

    def test_enum_membership(self) -> None:
        """Test that all expected values are members of the enum."""
        expected_values = {
            "claude",
            "goose",
            "codex",
            "gemini",
            "q",
            "opencode",
            "github_copilot",
            "default",
            "pydantic_ai",
            "unknown",
        }
        actual_values = {provider.value for provider in AgentProviderEnum}
        assert actual_values == expected_values

    def test_enum_count(self) -> None:
        """Test that the enum has the expected number of values."""
        assert len(AgentProviderEnum) == 10

    def test_enum_iteration(self) -> None:
        """Test that all enum values can be iterated over."""
        provider_values = [provider.value for provider in AgentProviderEnum]
        expected_values = [
            "claude",
            "goose",
            "codex",
            "gemini",
            "q",
            "opencode",
            "github_copilot",
            "default",
            "pydantic_ai",
            "unknown",
        ]
        assert sorted(provider_values) == sorted(expected_values)

    def test_enum_invalid_value_raises_error(self) -> None:
        """Test that creating an enum with an invalid value raises ValueError."""
        with pytest.raises(ValueError, match="'invalid' is not a valid AgentProviderEnum"):
            AgentProviderEnum("invalid")

    def test_enum_case_sensitive(self) -> None:
        """Test that enum values are case-sensitive."""
        with pytest.raises(ValueError, match="'CLAUDE' is not a valid AgentProviderEnum"):
            AgentProviderEnum("CLAUDE")

        with pytest.raises(ValueError, match="'Claude' is not a valid AgentProviderEnum"):
            AgentProviderEnum("Claude")

    def test_enum_str_representation(self) -> None:
        """Test the string representation of enum values."""
        assert str(AgentProviderEnum.CLAUDE) == "claude"
        assert str(AgentProviderEnum.GOOSE) == "goose"
        assert str(AgentProviderEnum.CODEX) == "codex"
        assert str(AgentProviderEnum.GEMINI) == "gemini"
        assert str(AgentProviderEnum.Q) == "q"
        assert str(AgentProviderEnum.OPENCODE) == "opencode"
        assert str(AgentProviderEnum.DEFAULT) == "default"
        assert str(AgentProviderEnum.PYDANTIC_AI) == "pydantic_ai"
        assert str(AgentProviderEnum.UNKNOWN) == "unknown"

    def test_enum_repr_representation(self) -> None:
        """Test the repr representation of enum values."""
        assert repr(AgentProviderEnum.CLAUDE) == "<AgentProviderEnum.CLAUDE: 'claude'>"
        assert repr(AgentProviderEnum.GOOSE) == "<AgentProviderEnum.GOOSE: 'goose'>"
        assert repr(AgentProviderEnum.CODEX) == "<AgentProviderEnum.CODEX: 'codex'>"
        assert repr(AgentProviderEnum.GEMINI) == "<AgentProviderEnum.GEMINI: 'gemini'>"
        assert repr(AgentProviderEnum.Q) == "<AgentProviderEnum.Q: 'q'>"
        assert repr(AgentProviderEnum.OPENCODE) == "<AgentProviderEnum.OPENCODE: 'opencode'>"
        assert repr(AgentProviderEnum.DEFAULT) == "<AgentProviderEnum.DEFAULT: 'default'>"
        assert repr(AgentProviderEnum.PYDANTIC_AI) == "<AgentProviderEnum.PYDANTIC_AI: 'pydantic_ai'>"
        assert repr(AgentProviderEnum.UNKNOWN) == "<AgentProviderEnum.UNKNOWN: 'unknown'>"

    def test_enum_in_container(self) -> None:
        """Test that enum values can be used in containers."""
        providers = [AgentProviderEnum.CLAUDE, AgentProviderEnum.GOOSE, AgentProviderEnum.OPENCODE]
        assert AgentProviderEnum.CLAUDE in providers
        assert AgentProviderEnum.OPENCODE in providers
        assert AgentProviderEnum.CODEX not in providers

    def test_enum_hash_consistency(self) -> None:
        """Test that enum values have consistent hash behavior."""
        providers_set = {AgentProviderEnum.CLAUDE, AgentProviderEnum.OPENCODE, AgentProviderEnum.Q}
        assert len(providers_set) == 3
        assert AgentProviderEnum.CLAUDE in providers_set
        assert AgentProviderEnum.OPENCODE in providers_set
        assert AgentProviderEnum.Q in providers_set

    def test_enum_equality_with_same_enum(self) -> None:
        """Test that enum values are equal to themselves."""
        assert AgentProviderEnum.CLAUDE == AgentProviderEnum.CLAUDE
        assert AgentProviderEnum.GOOSE == AgentProviderEnum.GOOSE
        assert AgentProviderEnum.CODEX == AgentProviderEnum.CODEX
        assert AgentProviderEnum.GEMINI == AgentProviderEnum.GEMINI
        assert AgentProviderEnum.Q == AgentProviderEnum.Q
        assert AgentProviderEnum.OPENCODE == AgentProviderEnum.OPENCODE
        assert AgentProviderEnum.DEFAULT == AgentProviderEnum.DEFAULT
        assert AgentProviderEnum.PYDANTIC_AI == AgentProviderEnum.PYDANTIC_AI
        assert AgentProviderEnum.UNKNOWN == AgentProviderEnum.UNKNOWN

    def test_enum_inequality_with_different_enums(self) -> None:
        """Test that different enum values are not equal."""
        assert AgentProviderEnum.CLAUDE != AgentProviderEnum.GOOSE
        assert AgentProviderEnum.OPENCODE != AgentProviderEnum.CODEX
        assert AgentProviderEnum.Q != AgentProviderEnum.UNKNOWN

    @pytest.mark.parametrize(
        ("provider_value", "expected_enum"),
        [
            ("claude", AgentProviderEnum.CLAUDE),
            ("goose", AgentProviderEnum.GOOSE),
            ("codex", AgentProviderEnum.CODEX),
            ("gemini", AgentProviderEnum.GEMINI),
            ("q", AgentProviderEnum.Q),
            ("opencode", AgentProviderEnum.OPENCODE),
            ("default", AgentProviderEnum.DEFAULT),
            ("pydantic_ai", AgentProviderEnum.PYDANTIC_AI),
            ("unknown", AgentProviderEnum.UNKNOWN),
        ],
    )
    def test_enum_parametrized_creation(self, provider_value: str, expected_enum: AgentProviderEnum) -> None:
        """Test parametrized enum creation from string values."""
        assert AgentProviderEnum(provider_value) == expected_enum

    def test_opencode_specific_behavior(self) -> None:
        """Test specific behavior for the newly added OPENCODE enum value."""
        # Test that OPENCODE can be created and used
        opencode_enum = AgentProviderEnum.OPENCODE
        assert opencode_enum == "opencode"
        assert opencode_enum.value == "opencode"

        # Test that it can be created from string
        opencode_from_string = AgentProviderEnum("opencode")
        assert opencode_from_string == AgentProviderEnum.OPENCODE

        # Test that it's different from other enum values
        assert AgentProviderEnum.OPENCODE != AgentProviderEnum.CLAUDE
        assert AgentProviderEnum.OPENCODE != AgentProviderEnum.GOOSE
        assert AgentProviderEnum.OPENCODE != AgentProviderEnum.CODEX
        assert AgentProviderEnum.OPENCODE != AgentProviderEnum.Q
        assert AgentProviderEnum.OPENCODE != AgentProviderEnum.DEFAULT
        assert AgentProviderEnum.OPENCODE != AgentProviderEnum.PYDANTIC_AI
        assert AgentProviderEnum.OPENCODE != AgentProviderEnum.UNKNOWN

    def test_q_specific_behavior(self) -> None:
        """Test specific behavior for the Q enum value."""
        # Test that Q can be created and used
        q_enum = AgentProviderEnum.Q
        assert q_enum == "q"
        assert q_enum.value == "q"

        # Test that it can be created from string
        q_from_string = AgentProviderEnum("q")
        assert q_from_string == AgentProviderEnum.Q

        # Test that it's different from other enum values
        assert AgentProviderEnum.Q != AgentProviderEnum.CLAUDE
        assert AgentProviderEnum.Q != AgentProviderEnum.GOOSE
        assert AgentProviderEnum.Q != AgentProviderEnum.CODEX
        assert AgentProviderEnum.Q != AgentProviderEnum.OPENCODE
        assert AgentProviderEnum.Q != AgentProviderEnum.DEFAULT
        assert AgentProviderEnum.Q != AgentProviderEnum.PYDANTIC_AI
        assert AgentProviderEnum.Q != AgentProviderEnum.UNKNOWN

    def test_pydantic_ai_specific_behavior(self) -> None:
        """Test specific behavior for the PYDANTIC_AI enum value."""
        # Test that PYDANTIC_AI can be created and used
        pydantic_ai_enum = AgentProviderEnum.PYDANTIC_AI
        assert pydantic_ai_enum == "pydantic_ai"
        assert pydantic_ai_enum.value == "pydantic_ai"

        # Test that it can be created from string
        pydantic_ai_from_string = AgentProviderEnum("pydantic_ai")
        assert pydantic_ai_from_string == AgentProviderEnum.PYDANTIC_AI

        # Test that it's different from other enum values
        assert AgentProviderEnum.PYDANTIC_AI != AgentProviderEnum.CLAUDE
        assert AgentProviderEnum.PYDANTIC_AI != AgentProviderEnum.GOOSE
        assert AgentProviderEnum.PYDANTIC_AI != AgentProviderEnum.CODEX
        assert AgentProviderEnum.PYDANTIC_AI != AgentProviderEnum.Q
        assert AgentProviderEnum.PYDANTIC_AI != AgentProviderEnum.OPENCODE
        assert AgentProviderEnum.PYDANTIC_AI != AgentProviderEnum.DEFAULT
        assert AgentProviderEnum.PYDANTIC_AI != AgentProviderEnum.UNKNOWN

    def test_default_specific_behavior(self) -> None:
        """Test specific behavior for the DEFAULT enum value."""
        # Test that DEFAULT can be created and used
        default_enum = AgentProviderEnum.DEFAULT
        assert default_enum == "default"
        assert default_enum.value == "default"

        # Test that it can be created from string
        default_from_string = AgentProviderEnum("default")
        assert default_from_string == AgentProviderEnum.DEFAULT

        # Test that it's different from other enum values
        assert AgentProviderEnum.DEFAULT != AgentProviderEnum.CLAUDE
        assert AgentProviderEnum.DEFAULT != AgentProviderEnum.GOOSE
        assert AgentProviderEnum.DEFAULT != AgentProviderEnum.CODEX
        assert AgentProviderEnum.DEFAULT != AgentProviderEnum.Q
        assert AgentProviderEnum.DEFAULT != AgentProviderEnum.OPENCODE
        assert AgentProviderEnum.DEFAULT != AgentProviderEnum.PYDANTIC_AI
        assert AgentProviderEnum.DEFAULT != AgentProviderEnum.UNKNOWN

    def test_gemini_specific_behavior(self) -> None:
        """Test specific behavior for the GEMINI enum value."""
        # Test that GEMINI can be created and used
        gemini_enum = AgentProviderEnum.GEMINI
        assert gemini_enum == "gemini"
        assert gemini_enum.value == "gemini"

        # Test that it can be created from string
        gemini_from_string = AgentProviderEnum("gemini")
        assert gemini_from_string == AgentProviderEnum.GEMINI

        # Test that it's different from other enum values
        assert AgentProviderEnum.GEMINI != AgentProviderEnum.CLAUDE
        assert AgentProviderEnum.GEMINI != AgentProviderEnum.GOOSE
        assert AgentProviderEnum.GEMINI != AgentProviderEnum.CODEX
        assert AgentProviderEnum.GEMINI != AgentProviderEnum.Q
        assert AgentProviderEnum.GEMINI != AgentProviderEnum.OPENCODE
        assert AgentProviderEnum.GEMINI != AgentProviderEnum.DEFAULT
        assert AgentProviderEnum.GEMINI != AgentProviderEnum.PYDANTIC_AI
        assert AgentProviderEnum.GEMINI != AgentProviderEnum.UNKNOWN

    def test_all_provider_values_are_lowercase(self) -> None:
        """Test that all provider values follow lowercase naming convention."""
        for provider in AgentProviderEnum:
            assert provider.value.islower(), f"Provider value '{provider.value}' should be lowercase"
            assert provider.value == provider.value.lower()

    def test_no_duplicate_values(self) -> None:
        """Test that there are no duplicate values in the enum."""
        values = [provider.value for provider in AgentProviderEnum]
        assert len(values) == len(set(values)), "Enum should not have duplicate values"
