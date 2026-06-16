from pydantic import model_validator

from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel


class StreamingTaskResponseModel(TaskResponseModel):
    """Enhanced TaskResponseModel that includes session_id for streaming workflows.

    Extends the base TaskResponseModel to include the session_id that frontend
    clients can use to connect to the streaming output.
    """

    session_id: str = ""

    @model_validator(mode="before")
    def set_exception_string(self) -> "StreamingTaskResponseModel":
        """Validate and format exception field."""
        exception = self.get("exception", None)
        if exception is not None and not isinstance(exception, str):
            self["exception"] = str(exception)  # type: ignore[index]
        return self
