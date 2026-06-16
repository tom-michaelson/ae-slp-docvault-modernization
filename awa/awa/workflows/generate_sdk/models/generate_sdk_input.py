from pathlib import Path

from pydantic import BaseModel
from pydantic.json_schema import SkipJsonSchema


class GenerateSdkInput(BaseModel):
    config_path: str | SkipJsonSchema[Path] | SkipJsonSchema[None] = None
    force: bool = False  # Skip hash check and force regeneration
    bump: bool = False  # Bump the version of the SDK even if the hash is the same
