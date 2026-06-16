"""Models for command execution input and results."""

from pydantic import BaseModel


class CommandInput(BaseModel):
    """Input parameters for command execution."""

    command: str
    working_dir: str | None = None


class CommandResult(BaseModel):
    """Result of executing a command."""

    exit_code: int
    output: str
    success: bool

    def __init__(self, **data: int | str | bool) -> None:
        """Initialize CommandResult and automatically set success based on exit_code."""
        if "success" not in data and "exit_code" in data:
            data["success"] = data["exit_code"] == 0
        super().__init__(**data)
