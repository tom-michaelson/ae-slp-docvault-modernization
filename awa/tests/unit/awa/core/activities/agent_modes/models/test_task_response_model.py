"""Unit tests for the TaskResponseModel."""

from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel


def test_task_response_model_all_fields_present() -> None:
    """Test that the model can be instantiated with all fields as strings."""
    data = {
        "status": "success",
        "reason": "Completed",
        "output": "Some output",
        "exception": "An error occurred",
    }
    model = TaskResponseModel(**data)
    assert model.status == data["status"]
    assert model.reason == data["reason"]
    assert model.output == data["output"]
    assert model.exception == data["exception"]


def test_task_response_model_exception_is_none() -> None:
    """Test that the model can be instantiated with exception being None."""
    data = {"status": "success", "reason": "Completed", "output": "Some output", "exception": None}
    model = TaskResponseModel(**data)
    assert model.exception is None


def test_task_response_model_exception_is_exception_object() -> None:
    """Test that the model_validator converts an Exception object to a string."""
    error = ValueError("This is a test error")
    data = {"status": "failed", "reason": "An error occurred", "output": "", "exception": error}
    model = TaskResponseModel(**data)
    assert model.exception == str(error)


def test_task_response_model_exception_is_not_string() -> None:
    """Test that the model_validator converts a non-string exception to its string representation."""
    data = {"status": "failed", "reason": "An error occurred", "output": "", "exception": 123}
    model = TaskResponseModel(**data)
    assert model.exception == "123"


def test_task_response_model_empty_initialization() -> None:
    """Test that the model can be initialized with no data, using default values."""
    model = TaskResponseModel()
    assert model.status == ""
    assert model.reason == ""
    assert model.output == ""
    assert model.exception is None


def test_task_response_model_partial_data() -> None:
    """Test that the model can be initialized with partial data."""
    data = {"status": "partial", "output": "Partial output"}
    model = TaskResponseModel(**data)
    assert model.status == "partial"
    assert model.reason == ""

    assert model.output == "Partial output"
    assert model.exception is None
