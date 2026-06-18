from typing import Literal

from pydantic import BaseModel, Field


class ItemResult(BaseModel):
    key: str
    type: str
    status: Literal["implemented", "failed", "blocked", "skipped"] = "implemented"
    attempts: int = 0
    notes: str | None = None


class BatchResult(BaseModel):
    batch_id: str = Field(..., alias="batchId")
    branch: str | None = None
    pushed: bool = False
    verified: bool = False
    item_results: list[ItemResult] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class PageResult(BaseModel):
    page_key: str = Field(..., alias="pageKey")
    progress_branch: str = Field(..., alias="progressBranch")
    batch_results: list[BatchResult] = Field(default_factory=list)
    implementation_complete: bool = Field(default=False, alias="implementationComplete")

    class Config:
        populate_by_name = True
