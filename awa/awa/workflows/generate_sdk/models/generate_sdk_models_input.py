from pathlib import Path

from pydantic import BaseModel

from awa.workflows.generate_sdk.models.sdk_config import SdkLanguageConfig


class GenerateSdkModelsInput(BaseModel):
    json_schemas_path: str | Path
    language_config: SdkLanguageConfig
    output_path: str | Path
    """Path where generated SDK models should be written"""
