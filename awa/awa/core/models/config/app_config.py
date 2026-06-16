from pydantic import BaseModel, Field

from awa.core.models.config.jira_config import JiraConfig
from awa.core.models.config.llm_config import LLMConfig
from awa.core.models.config.log_config import LogConfig
from awa.core.models.config.s3_vector_config import S3VectorConfig


class AppConfig(BaseModel):
    """Main application configuration."""

    llm: LLMConfig = Field(description="LLM configuration")
    jira: JiraConfig | None = Field(default=None, description="Jira configuration")
    logging: LogConfig = Field(default_factory=LogConfig, description="Logging configuration")
    recipes: bool = Field(
        default=True,
        description=(
            "Enable recipe workflows and activities registration. "
            "When true, recipe workflows will be discovered and registered with the worker."
        ),
    )
    s3_vector: S3VectorConfig | None = Field(default=None, description="S3 Vector Store configuration")
