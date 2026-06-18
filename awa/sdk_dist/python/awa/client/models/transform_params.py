from typing import Any

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema

from awa.client import constants as sdk_constants
from awa.client.models.baml_image_input_params import BamlImageInputParams
from awa.client.models.input_params import InputParams


class TransformParams(BaseModel):
    model_name: str | SkipJsonSchema[None] = Field(default=None)
    baml_function_name: str
    baml_content: str | SkipJsonSchema[None] = Field(default=None)
    baml_content_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Path to a directory containing BAML files to be compiled and used for transformation",
    )
    request: Any
    inputs: list[InputParams] | SkipJsonSchema[None] = Field(default=None)
    images: list[BamlImageInputParams] | SkipJsonSchema[None] = Field(default=None)
    timeout_seconds: int | SkipJsonSchema[None] = Field(default=sdk_constants.DEFAULT_BAML_ACTIVITY_TIMEOUT_SECONDS)
    output_path: str | SkipJsonSchema[None] = Field(default=None)
    output_json_path: str | SkipJsonSchema[None] = Field(
        default=None,
        description="JSON Path query to extract specific data from the BAML response before writing to output_path",
    )
    baml_src_dir: str | SkipJsonSchema[None] = Field(default=None)


class TransformBatchParams(BaseModel):
    params_by_key: dict[str, TransformParams] = Field(default_factory=dict)
    timeout_seconds: int | SkipJsonSchema[None] = Field(
        default=sdk_constants.DEFAULT_BAML_ACTIVITY_TIMEOUT_SECONDS * 10,
    )
    max_concurrency: int | SkipJsonSchema[None] = Field(
        default=None,
        description="Maximum number of concurrent executions. If None or < 0, defaults to 10. If 0, unlimited.",
    )
