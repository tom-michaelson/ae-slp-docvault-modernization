from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import SkipJsonSchema

from awa.sdk.models.transform_params import InputParams


class BuildPromptParams(BaseModel):
    template: str | SkipJsonSchema[None] = None
    template_input: InputParams | SkipJsonSchema[None] = None
    variables: dict[str, Any] | SkipJsonSchema[None] = None
    inputs: list[InputParams] | SkipJsonSchema[None] = None
    output_path: str | SkipJsonSchema[None] = None
