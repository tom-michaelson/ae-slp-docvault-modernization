"""Human-in-the-Loop (HITL) data models for workflow interactions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HITLInput(BaseModel):
    """Input data for the HITL workflow.

    'input_schema' contains a JSON Schema definition describing the expected shape of the response 'data'.
    """

    # Context for the human
    title: str
    description: str
    markdown: str

    # Input schema (JSON Schema format)
    input_schema: dict[str, Any] | None = None

    # Optional fields
    attachments: list[str] = Field(default_factory=list)
    timeout_seconds: int | None = None
    non_blocking: bool = False
    chat_mode: bool = False


class HITLResponse(BaseModel):
    """Response data from the human interaction."""

    # The data should conform to the schema provided in the input
    data: dict

    # For chat mode, the textual message
    message: str = ""


class HITLOutput(BaseModel):
    """Output from the HITL workflow."""

    response: HITLResponse | None
    timed_out: bool
    chat_history: list[HITLChatMessage] = Field(default_factory=list)


class HITLContext(BaseModel):
    """Context information for the HITL interaction."""

    title: str
    description: str
    markdown: str
    input_schema: dict[str, Any] | None
    attachments: list[str] = Field(default_factory=list)
    chat_mode: bool = False


class HITLChatMessage(BaseModel):
    """Represents a message in the chat history.

    When used as an inbound payload for the `add_system_message` signal, only
    `message` and optional `data` need to be supplied. `timestamp` and
    `is_human` will be normalized by the workflow (timestamp assigned, is_human
    forced to False for system messages / True for human responses).
    """

    message: str
    data: dict[str, Any] | None = None
    timestamp: datetime | None = None
    is_human: bool | None = None
