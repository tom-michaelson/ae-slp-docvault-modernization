from typing import Literal

from pydantic import BaseModel, Field


class PlanItem(BaseModel):
    """A single implementable unit inside an E2E batch."""

    key: str = Field(..., description="Item identifier (matches Discover entry-point key).")
    type: Literal["api-endpoint", "ui-feature"] = Field(
        ...,
        description="Implementation type; drives which slash commands are invoked.",
    )
    functional_spec_path: str | None = Field(
        default=None,
        alias="functionalSpecPath",
        description="Absolute path to the item's functional-spec.md, if one exists.",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Item keys that must be implemented before this one.",
    )

    class Config:
        populate_by_name = True


class E2EBatch(BaseModel):
    """A batch of independent items that become one stacked PR branch."""

    batch_id: str = Field(..., alias="batchId")
    items: list[PlanItem] = Field(default_factory=list)

    # Mutable state persisted to the in-progress plan file across runs.
    branch_name: str | None = Field(default=None, alias="branchName")
    pushed: bool = False
    completed: bool = False

    class Config:
        populate_by_name = True


class PagePlan(BaseModel):
    """Full plan for a single page: an ordered list of E2E batches."""

    page_key: str = Field(..., alias="pageKey")
    domain: str
    batches: list[E2EBatch] = Field(default_factory=list)

    class Config:
        populate_by_name = True
