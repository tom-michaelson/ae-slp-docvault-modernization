"""Log configuration models for AWA."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ComponentLogLevels(BaseModel):
    """Component-specific log level configuration."""

    api: str = Field(default="INFO", description="API service log level")
    ui: str = Field(default="INFO", description="UI service log level")
    worker: str = Field(default="INFO", description="Worker service log level")
    server: str = Field(default="INFO", description="Server service log level")  # tested thru here, need to test below
    workflow: str = Field(default="INFO", description="Workflow log level")
    activity: str = Field(default="INFO", description="Activity log level")
    cli: str = Field(default="INFO", description="CLI log level")
    client: str = Field(default="INFO", description="Client log level")
    script: str = Field(default="INFO", description="Script log level")
    auth: str = Field(default="INFO", description="Auth log level")
    http: str = Field(default="INFO", description="HTTP log level")  # TODO can we remove this?
    socketio: str = Field(default="INFO", description="Socket.IO log level")  # tested this
    engine: str = Field(default="INFO", description="Engine log level")
    uvicorn: str = Field(default="INFO", description="Uvicorn/FastAPI log level")  # tested this


LogLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LogConfig(BaseModel):
    """Logging configuration for AWA."""

    # Single log level (string) or component-specific levels (dict)
    log_level: str | ComponentLogLevels = Field(
        default="INFO",
        description="Log level configuration - either a single level or component-specific levels",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def parse_log_level(cls, v: Any) -> str | ComponentLogLevels:  # noqa: ANN401
        """Parse log_level from various input formats."""
        if isinstance(v, str):
            # It's a single log level string
            return v.upper()
        if isinstance(v, dict):
            # It's a component-specific configuration
            return ComponentLogLevels(**v)
        if isinstance(v, ComponentLogLevels):
            # Already the right type
            return v
        # Default to INFO
        return "INFO"

    def get_component_log_level(self, component: str) -> str:
        """Get the log level for a specific component.

        Args:
            component: Component name (e.g., 'api', 'ui', 'worker')

        Returns:
            Log level string for the component

        """
        if isinstance(self.log_level, str):
            # Single log level for all components
            return self.log_level

        # Component-specific levels
        component_lower = component.lower()
        if hasattr(self.log_level, component_lower):
            return getattr(self.log_level, component_lower)

        # Default to INFO if component not found
        return "INFO"
