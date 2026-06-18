"""Integration tests for logger functionality."""

from cookbook.recipes.utilities.logger import logger
from cookbook.recipes.utilities.logger.logger import LoggerComponent


def test_logger_module_structure() -> None:
    """Test that the logger module has the expected structure and exports."""
    # Verify key components are available
    assert hasattr(logger, "get_logger")
    assert hasattr(logger, "init_logging")
    assert hasattr(logger, "LoggerComponent")


def test_logger_component_enum() -> None:
    """Test that LoggerComponent enum is properly defined."""
    # Verify some key logger components exist
    expected_components = [
        "WORKFLOW",
        "ACTIVITY",
        "WORKER",
        "API",
        "CLI",
    ]

    for component_name in expected_components:
        assert hasattr(LoggerComponent, component_name), f"LoggerComponent should have {component_name}"
        component = getattr(LoggerComponent, component_name)
        assert isinstance(component.value, str), f"{component_name} should have a string value"
