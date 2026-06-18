from typing import Any

from temporalio.exceptions import ApplicationError


class InvalidInputApplicationError(ApplicationError):
    def __init__(self, message: str, *details: Any) -> None:  # noqa: ANN401
        super().__init__(message, *details, non_retryable=True)
