from enum import StrEnum


# pylint: disable=mixed-line-endings
class AgentModeEnum(StrEnum):
    ANALYZE = "analyze"
    ACT = "act"
    UNKNOWN = "unknown"
