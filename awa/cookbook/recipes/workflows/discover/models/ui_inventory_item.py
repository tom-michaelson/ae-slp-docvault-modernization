from typing import Literal

from pydantic import BaseModel, Field


class UiInventoryItem(BaseModel):
    """Generic UI feature discovered in a legacy codebase.

    Broader than a single page — covers pages, panels, forms, tables, and actions.
    Intentionally framework-agnostic; projects that need framework-specific fields
    should extend this model rather than polluting the generic one.
    """

    key: str = Field(
        ...,
        description="Stable, filesystem-safe identifier (e.g. '0001-catalog-list').",
    )
    name: str = Field(
        ...,
        description="Human-readable feature name.",
    )
    element_type: Literal[
        "ui-page",
        "ui-panel",
        "ui-form",
        "ui-table",
        "ui-action",
        "other",
    ] = Field(
        default="ui-page",
        alias="elementType",
        description="Kind of UI element.",
    )
    location: str = Field(
        ...,
        description="Path to the source file (optionally with :line), relative to target_dir.",
    )
    uri: str | None = Field(
        default=None,
        description="Route or URL path used to reach this feature in the running app.",
    )
    domain: str | None = Field(
        default=None,
        description="Optional business-domain label.",
    )
    parent_key: str | None = Field(
        default=None,
        alias="parentKey",
        description="Key of the parent UI feature, for nested elements.",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Free-form observations captured during inventory.",
    )

    class Config:
        populate_by_name = True
