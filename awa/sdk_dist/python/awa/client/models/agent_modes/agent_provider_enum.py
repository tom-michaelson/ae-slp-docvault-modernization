from enum import StrEnum


class AgentProviderEnum(StrEnum):
    CLAUDE = "claude"
    GOOSE = "goose"
    CODEX = "codex"
    GEMINI = "gemini"
    Q = "q"
    OPENCODE = "opencode"
    GITHUB_COPILOT = "github_copilot"
    DEFAULT = "default"
    PYDANTIC_AI = "pydantic_ai"
    UNKNOWN = "unknown"
