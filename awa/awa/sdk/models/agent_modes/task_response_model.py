from typing import Any

from pydantic import BaseModel, model_validator


class TaskResponseModel(BaseModel):
    status: str = ""  # TODO AWA-140: add enum for status
    reason: str = ""
    output: str = ""
    exception: str | None = None

    @model_validator(mode="before")
    @classmethod
    def set_exception_string(cls, data: Any) -> Any:  # noqa: ANN401
        if isinstance(data, dict):
            exception = data.get("exception", None)
            if exception is not None and not isinstance(exception, str):
                data["exception"] = str(exception)
        return data
