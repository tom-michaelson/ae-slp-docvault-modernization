from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    """Generic inventory item for non-UI entry points (API endpoints, batch jobs, etc.)."""

    key: str = Field(
        ...,
        description="Stable, filesystem-safe identifier (e.g. '0001-get-catalog-items').",
    )
    name: str | None = Field(
        default=None,
        description="Human-readable name (e.g. the method/handler name).",
    )
    type: str = Field(
        ...,
        description="Entry-point category (e.g. 'api-endpoint', 'batch-job').",
    )
    location: str = Field(
        ...,
        description="Path to the source file defining this entry point (optionally with :line).",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Free-form observations captured during inventory.",
    )
