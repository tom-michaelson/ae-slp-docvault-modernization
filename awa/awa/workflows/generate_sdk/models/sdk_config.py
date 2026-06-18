from pydantic import BaseModel

from .supported_language import SupportedLanguage


class SdkLanguageConfig(BaseModel):
    enabled: bool
    name: SupportedLanguage
    ext: str
    model_file_name: str
    model_path: str
    constants_file_name: str
    constants_path: str
    namespace: str | None = None
    package: str | None = None
    test_command: str | None = None
    utils_base_path: str | None = None  # Base path for utility files
    utils_organize_by_type: bool = False  # Whether to organize utils by type (workflow/activity) in subdirectories
    utils_use_pascal_case: bool = False  # Whether to convert snake_case function names to PascalCase for file names


class SdkConfig(BaseModel):
    languages: list[SdkLanguageConfig]
    output_path: str
    """Path where generated SDK models should be written, relative to the project root"""
