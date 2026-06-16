from pydantic import BaseModel, Field


class UiUsage(BaseModel):
    """Link between an API endpoint and a UI feature that calls it."""

    api_key: str = Field(..., description="Key of the API endpoint inventory item.")
    ui_feature_key: str = Field(..., description="Key of the UI feature that calls the endpoint.")
    location: str | None = Field(
        default=None,
        description="File/line where the UI feature invokes the endpoint.",
    )
