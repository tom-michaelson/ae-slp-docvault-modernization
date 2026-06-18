"""Input models for MCP tool workflows."""

from pydantic import BaseModel


class CalculatorInput(BaseModel):
    """Input for calculator-based MCP tool workflows."""

    a: float
    b: float


class NPXStdioFilesystemInput(BaseModel):
    """Input for NPX stdio filesystem MCP tool workflows."""

    directory_path: str = "."


class UVXStdioTimeInput(BaseModel):
    """Input for UVX stdio time MCP tool workflows."""

    source_timezone: str = "America/New_York"
    target_timezone: str = "Asia/Tokyo"
    time: str = "16:30"
