"""Approval input model for workflow signals."""

from pydantic import BaseModel


class ApproveInput(BaseModel):
    """Input model for approval signals."""

    name: str
