from pathlib import Path

from pydantic import BaseModel


class GenerateSdkSchemasInput(BaseModel):
    models_path: str | Path
    """Path to the Pydantic models directory"""
    output_path: str | Path
    """Path where JSON schemas should be generated"""
