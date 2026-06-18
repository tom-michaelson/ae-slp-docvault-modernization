from pydantic import BaseModel


class ApplyDiffResult(BaseModel):
    success: bool
    message: str | None = None
