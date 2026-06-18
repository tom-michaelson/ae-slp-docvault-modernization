"""Test cases for sample input models used in MCP examples."""

import pytest
from pydantic import ValidationError

from tests.unit.awa.sample_input_models import CalculatorInput, NPXStdioFilesystemInput, UVXStdioTimeInput


class TestCalculatorInput:
    """Test cases for CalculatorInput model."""

    def test_calculator_input_initialization_with_valid_data(self) -> None:
        """Test CalculatorInput initialization with valid float values."""
        input_data = CalculatorInput(a=1.5, b=2.5)
        assert input_data.a == 1.5
        assert input_data.b == 2.5

    def test_calculator_input_initialization_with_integers(self) -> None:
        """Test CalculatorInput initialization with integer values (should convert to float)."""
        input_data = CalculatorInput(a=1, b=2)
        assert input_data.a == 1.0
        assert input_data.b == 2.0
        assert isinstance(input_data.a, float)
        assert isinstance(input_data.b, float)

    def test_calculator_input_initialization_with_negative_values(self) -> None:
        """Test CalculatorInput initialization with negative values."""
        input_data = CalculatorInput(a=-1.5, b=-2.5)
        assert input_data.a == -1.5
        assert input_data.b == -2.5

    def test_calculator_input_initialization_with_zero(self) -> None:
        """Test CalculatorInput initialization with zero values."""
        input_data = CalculatorInput(a=0.0, b=0.0)
        assert input_data.a == 0.0
        assert input_data.b == 0.0

    def test_calculator_input_initialization_with_large_values(self) -> None:
        """Test CalculatorInput initialization with large float values."""
        input_data = CalculatorInput(a=1e10, b=1e-10)
        assert input_data.a == 1e10
        assert input_data.b == 1e-10

    def test_calculator_input_field_type_validation(self) -> None:
        """Test that CalculatorInput fields must be numeric types."""
        with pytest.raises(ValidationError) as exc_info:
            CalculatorInput(a="not_a_number", b=2.5)
        error = exc_info.value
        assert "a" in str(error)
        assert "Input should be a valid number" in str(error)

        with pytest.raises(ValidationError) as exc_info:
            CalculatorInput(a=1.5, b="not_a_number")
        error = exc_info.value
        assert "b" in str(error)
        assert "Input should be a valid number" in str(error)

    def test_calculator_input_missing_fields(self) -> None:
        """Test that CalculatorInput requires both a and b fields."""
        with pytest.raises(ValidationError) as exc_info:
            CalculatorInput(a=1.5)
        error = exc_info.value
        assert "b" in str(error)
        assert "Field required" in str(error)

        with pytest.raises(ValidationError) as exc_info:
            CalculatorInput(b=2.5)
        error = exc_info.value
        assert "a" in str(error)
        assert "Field required" in str(error)

    def test_calculator_input_model_dump(self) -> None:
        """Test CalculatorInput model_dump method."""
        input_data = CalculatorInput(a=1.5, b=2.5)
        dumped = input_data.model_dump()
        assert dumped == {"a": 1.5, "b": 2.5}
        assert isinstance(dumped, dict)

    def test_calculator_input_model_validate(self) -> None:
        """Test CalculatorInput model_validate method."""
        data = {"a": 1.5, "b": 2.5}
        input_data = CalculatorInput.model_validate(data)
        assert input_data.a == 1.5
        assert input_data.b == 2.5

    def test_calculator_input_json_serialization(self) -> None:
        """Test CalculatorInput JSON serialization."""
        input_data = CalculatorInput(a=1.5, b=2.5)
        json_str = input_data.model_dump_json()
        assert json_str == '{"a":1.5,"b":2.5}'

    def test_calculator_input_json_deserialization(self) -> None:
        """Test CalculatorInput JSON deserialization."""
        json_str = '{"a":1.5,"b":2.5}'
        input_data = CalculatorInput.model_validate_json(json_str)
        assert input_data.a == 1.5
        assert input_data.b == 2.5

    def test_calculator_input_equality(self) -> None:
        """Test CalculatorInput equality comparison."""
        input1 = CalculatorInput(a=1.5, b=2.5)
        input2 = CalculatorInput(a=1.5, b=2.5)
        input3 = CalculatorInput(a=1.5, b=3.5)

        assert input1 == input2
        assert input1 != input3

    def test_calculator_input_string_representation(self) -> None:
        """Test CalculatorInput string representation."""
        input_data = CalculatorInput(a=1.5, b=2.5)
        repr_str = repr(input_data)
        assert "CalculatorInput" in repr_str
        assert "a=1.5" in repr_str
        assert "b=2.5" in repr_str


class TestNPXStdioFilesystemInput:
    """Test cases for NPXStdioFilesystemInput model."""

    def test_npx_stdio_filesystem_input_initialization_with_default(self) -> None:
        """Test NPXStdioFilesystemInput initialization with default directory_path."""
        input_data = NPXStdioFilesystemInput()
        assert input_data.directory_path == "."

    def test_npx_stdio_filesystem_input_initialization_with_custom_path(self) -> None:
        """Test NPXStdioFilesystemInput initialization with custom directory_path."""
        input_data = NPXStdioFilesystemInput(directory_path="/path/to/directory")
        assert input_data.directory_path == "/path/to/directory"

    def test_npx_stdio_filesystem_input_initialization_with_relative_path(self) -> None:
        """Test NPXStdioFilesystemInput initialization with relative path."""
        input_data = NPXStdioFilesystemInput(directory_path="./relative/path")
        assert input_data.directory_path == "./relative/path"

    def test_npx_stdio_filesystem_input_initialization_with_empty_string(self) -> None:
        """Test NPXStdioFilesystemInput initialization with empty string."""
        input_data = NPXStdioFilesystemInput(directory_path="")
        assert input_data.directory_path == ""

    def test_npx_stdio_filesystem_input_field_type_validation(self) -> None:
        """Test that NPXStdioFilesystemInput directory_path must be a string."""
        with pytest.raises(ValidationError) as exc_info:
            NPXStdioFilesystemInput(directory_path=123)
        error = exc_info.value
        assert "directory_path" in str(error)
        assert "Input should be a valid string" in str(error)

        with pytest.raises(ValidationError) as exc_info:
            NPXStdioFilesystemInput(directory_path=None)
        error = exc_info.value
        assert "directory_path" in str(error)
        assert "Input should be a valid string" in str(error)

    def test_npx_stdio_filesystem_input_model_dump(self) -> None:
        """Test NPXStdioFilesystemInput model_dump method."""
        input_data = NPXStdioFilesystemInput(directory_path="/custom/path")
        dumped = input_data.model_dump()
        assert dumped == {"directory_path": "/custom/path"}
        assert isinstance(dumped, dict)

    def test_npx_stdio_filesystem_input_model_dump_with_default(self) -> None:
        """Test NPXStdioFilesystemInput model_dump with default value."""
        input_data = NPXStdioFilesystemInput()
        dumped = input_data.model_dump()
        assert dumped == {"directory_path": "."}

    def test_npx_stdio_filesystem_input_model_validate(self) -> None:
        """Test NPXStdioFilesystemInput model_validate method."""
        data = {"directory_path": "/custom/path"}
        input_data = NPXStdioFilesystemInput.model_validate(data)
        assert input_data.directory_path == "/custom/path"

    def test_npx_stdio_filesystem_input_model_validate_with_empty_dict(self) -> None:
        """Test NPXStdioFilesystemInput model_validate with empty dict (should use default)."""
        data = {}
        input_data = NPXStdioFilesystemInput.model_validate(data)
        assert input_data.directory_path == "."

    def test_npx_stdio_filesystem_input_json_serialization(self) -> None:
        """Test NPXStdioFilesystemInput JSON serialization."""
        input_data = NPXStdioFilesystemInput(directory_path="/custom/path")
        json_str = input_data.model_dump_json()
        assert json_str == '{"directory_path":"/custom/path"}'

    def test_npx_stdio_filesystem_input_json_deserialization(self) -> None:
        """Test NPXStdioFilesystemInput JSON deserialization."""
        json_str = '{"directory_path":"/custom/path"}'
        input_data = NPXStdioFilesystemInput.model_validate_json(json_str)
        assert input_data.directory_path == "/custom/path"

    def test_npx_stdio_filesystem_input_equality(self) -> None:
        """Test NPXStdioFilesystemInput equality comparison."""
        input1 = NPXStdioFilesystemInput(directory_path="/path1")
        input2 = NPXStdioFilesystemInput(directory_path="/path1")
        input3 = NPXStdioFilesystemInput(directory_path="/path2")

        assert input1 == input2
        assert input1 != input3

    def test_npx_stdio_filesystem_input_string_representation(self) -> None:
        """Test NPXStdioFilesystemInput string representation."""
        input_data = NPXStdioFilesystemInput(directory_path="/custom/path")
        repr_str = repr(input_data)
        assert "NPXStdioFilesystemInput" in repr_str
        assert "directory_path='/custom/path'" in repr_str


class TestUVXStdioTimeInput:
    """Test cases for UVXStdioTimeInput model."""

    def test_uvx_stdio_time_input_initialization_with_defaults(self) -> None:
        """Test UVXStdioTimeInput initialization with default values."""
        input_data = UVXStdioTimeInput()
        assert input_data.source_timezone == "America/New_York"
        assert input_data.target_timezone == "Asia/Tokyo"
        assert input_data.time == "16:30"

    def test_uvx_stdio_time_input_initialization_with_custom_values(self) -> None:
        """Test UVXStdioTimeInput initialization with custom values."""
        input_data = UVXStdioTimeInput(
            source_timezone="Europe/London",
            target_timezone="America/Los_Angeles",
            time="09:15",
        )
        assert input_data.source_timezone == "Europe/London"
        assert input_data.target_timezone == "America/Los_Angeles"
        assert input_data.time == "09:15"

    def test_uvx_stdio_time_input_initialization_with_partial_custom_values(self) -> None:
        """Test UVXStdioTimeInput initialization with partially custom values."""
        input_data = UVXStdioTimeInput(time="12:45")
        assert input_data.source_timezone == "America/New_York"
        assert input_data.target_timezone == "Asia/Tokyo"
        assert input_data.time == "12:45"

    def test_uvx_stdio_time_input_field_type_validation(self) -> None:
        """Test that UVXStdioTimeInput fields must be strings."""
        with pytest.raises(ValidationError) as exc_info:
            UVXStdioTimeInput(source_timezone=123)
        error = exc_info.value
        assert "source_timezone" in str(error)
        assert "Input should be a valid string" in str(error)

        with pytest.raises(ValidationError) as exc_info:
            UVXStdioTimeInput(target_timezone=None)
        error = exc_info.value
        assert "target_timezone" in str(error)
        assert "Input should be a valid string" in str(error)

        with pytest.raises(ValidationError) as exc_info:
            UVXStdioTimeInput(time=1530)
        error = exc_info.value
        assert "time" in str(error)
        assert "Input should be a valid string" in str(error)

    def test_uvx_stdio_time_input_timezone_formats(self) -> None:
        """Test UVXStdioTimeInput with various timezone formats."""
        # Standard timezone names
        input_data = UVXStdioTimeInput(
            source_timezone="UTC",
            target_timezone="GMT",
        )
        assert input_data.source_timezone == "UTC"
        assert input_data.target_timezone == "GMT"

        # Region/City format
        input_data = UVXStdioTimeInput(
            source_timezone="Australia/Sydney",
            target_timezone="Africa/Cairo",
        )
        assert input_data.source_timezone == "Australia/Sydney"
        assert input_data.target_timezone == "Africa/Cairo"

    def test_uvx_stdio_time_input_time_formats(self) -> None:
        """Test UVXStdioTimeInput with various time formats."""
        # Standard HH:MM format
        input_data = UVXStdioTimeInput(time="23:59")
        assert input_data.time == "23:59"

        # Single digit hours/minutes
        input_data = UVXStdioTimeInput(time="9:05")
        assert input_data.time == "9:05"

        # With seconds
        input_data = UVXStdioTimeInput(time="14:30:45")
        assert input_data.time == "14:30:45"

    def test_uvx_stdio_time_input_model_dump(self) -> None:
        """Test UVXStdioTimeInput model_dump method."""
        input_data = UVXStdioTimeInput(
            source_timezone="Europe/Paris",
            target_timezone="America/Chicago",
            time="14:30",
        )
        dumped = input_data.model_dump()
        expected = {
            "source_timezone": "Europe/Paris",
            "target_timezone": "America/Chicago",
            "time": "14:30",
        }
        assert dumped == expected
        assert isinstance(dumped, dict)

    def test_uvx_stdio_time_input_model_dump_with_defaults(self) -> None:
        """Test UVXStdioTimeInput model_dump with default values."""
        input_data = UVXStdioTimeInput()
        dumped = input_data.model_dump()
        expected = {
            "source_timezone": "America/New_York",
            "target_timezone": "Asia/Tokyo",
            "time": "16:30",
        }
        assert dumped == expected

    def test_uvx_stdio_time_input_model_validate(self) -> None:
        """Test UVXStdioTimeInput model_validate method."""
        data = {
            "source_timezone": "Europe/Berlin",
            "target_timezone": "America/Denver",
            "time": "11:45",
        }
        input_data = UVXStdioTimeInput.model_validate(data)
        assert input_data.source_timezone == "Europe/Berlin"
        assert input_data.target_timezone == "America/Denver"
        assert input_data.time == "11:45"

    def test_uvx_stdio_time_input_model_validate_with_empty_dict(self) -> None:
        """Test UVXStdioTimeInput model_validate with empty dict (should use defaults)."""
        data = {}
        input_data = UVXStdioTimeInput.model_validate(data)
        assert input_data.source_timezone == "America/New_York"
        assert input_data.target_timezone == "Asia/Tokyo"
        assert input_data.time == "16:30"

    def test_uvx_stdio_time_input_json_serialization(self) -> None:
        """Test UVXStdioTimeInput JSON serialization."""
        input_data = UVXStdioTimeInput(
            source_timezone="Europe/Madrid",
            target_timezone="Asia/Shanghai",
            time="18:20",
        )
        json_str = input_data.model_dump_json()
        expected = '{"source_timezone":"Europe/Madrid","target_timezone":"Asia/Shanghai","time":"18:20"}'
        assert json_str == expected

    def test_uvx_stdio_time_input_json_deserialization(self) -> None:
        """Test UVXStdioTimeInput JSON deserialization."""
        json_str = '{"source_timezone":"Europe/Rome","target_timezone":"America/Phoenix","time":"20:15"}'
        input_data = UVXStdioTimeInput.model_validate_json(json_str)
        assert input_data.source_timezone == "Europe/Rome"
        assert input_data.target_timezone == "America/Phoenix"
        assert input_data.time == "20:15"

    def test_uvx_stdio_time_input_equality(self) -> None:
        """Test UVXStdioTimeInput equality comparison."""
        input1 = UVXStdioTimeInput(
            source_timezone="UTC",
            target_timezone="GMT",
            time="12:00",
        )
        input2 = UVXStdioTimeInput(
            source_timezone="UTC",
            target_timezone="GMT",
            time="12:00",
        )
        input3 = UVXStdioTimeInput(
            source_timezone="UTC",
            target_timezone="GMT",
            time="13:00",
        )

        assert input1 == input2
        assert input1 != input3

    def test_uvx_stdio_time_input_string_representation(self) -> None:
        """Test UVXStdioTimeInput string representation."""
        input_data = UVXStdioTimeInput(
            source_timezone="Pacific/Auckland",
            target_timezone="Atlantic/Reykjavik",
            time="07:30",
        )
        repr_str = repr(input_data)
        assert "UVXStdioTimeInput" in repr_str
        assert "source_timezone='Pacific/Auckland'" in repr_str
        assert "target_timezone='Atlantic/Reykjavik'" in repr_str
        assert "time='07:30'" in repr_str


class TestAllModelsIntegration:
    """Integration tests for all sample input models."""

    def test_all_models_are_pydantic_models(self) -> None:
        """Test that all models inherit from BaseModel."""
        from pydantic import BaseModel

        assert issubclass(CalculatorInput, BaseModel)
        assert issubclass(NPXStdioFilesystemInput, BaseModel)
        assert issubclass(UVXStdioTimeInput, BaseModel)

    def test_all_models_have_model_fields(self) -> None:
        """Test that all models have the expected model fields."""
        calculator_fields = set(CalculatorInput.model_fields.keys())
        assert calculator_fields == {"a", "b"}

        npx_fields = set(NPXStdioFilesystemInput.model_fields.keys())
        assert npx_fields == {"directory_path"}

        uvx_fields = set(UVXStdioTimeInput.model_fields.keys())
        assert uvx_fields == {"source_timezone", "target_timezone", "time"}

    def test_all_models_schema_generation(self) -> None:
        """Test that all models can generate JSON schemas."""
        calculator_schema = CalculatorInput.model_json_schema()
        assert "properties" in calculator_schema
        assert "a" in calculator_schema["properties"]
        assert "b" in calculator_schema["properties"]

        npx_schema = NPXStdioFilesystemInput.model_json_schema()
        assert "properties" in npx_schema
        assert "directory_path" in npx_schema["properties"]

        uvx_schema = UVXStdioTimeInput.model_json_schema()
        assert "properties" in uvx_schema
        assert "source_timezone" in uvx_schema["properties"]
        assert "target_timezone" in uvx_schema["properties"]
        assert "time" in uvx_schema["properties"]

    def test_all_models_with_empty_dict_validation(self) -> None:
        """Test how all models handle empty dictionary validation."""
        # CalculatorInput should fail with empty dict (required fields)
        with pytest.raises(ValidationError):
            CalculatorInput.model_validate({})

        # NPXStdioFilesystemInput should work with empty dict (has default)
        npx_input = NPXStdioFilesystemInput.model_validate({})
        assert npx_input.directory_path == "."

        # UVXStdioTimeInput should work with empty dict (has defaults)
        uvx_input = UVXStdioTimeInput.model_validate({})
        assert uvx_input.source_timezone == "America/New_York"
        assert uvx_input.target_timezone == "Asia/Tokyo"
        assert uvx_input.time == "16:30"

    def test_all_models_with_extra_fields(self) -> None:
        """Test how all models handle extra fields (should be ignored by default)."""
        calculator_data = {"a": 1.0, "b": 2.0, "extra": "ignored"}
        calculator_input = CalculatorInput.model_validate(calculator_data)
        assert calculator_input.a == 1.0
        assert calculator_input.b == 2.0
        assert not hasattr(calculator_input, "extra")

        npx_data = {"directory_path": "/path", "extra": "ignored"}
        npx_input = NPXStdioFilesystemInput.model_validate(npx_data)
        assert npx_input.directory_path == "/path"
        assert not hasattr(npx_input, "extra")

        uvx_data = {
            "source_timezone": "UTC",
            "target_timezone": "GMT",
            "time": "12:00",
            "extra": "ignored",
        }
        uvx_input = UVXStdioTimeInput.model_validate(uvx_data)
        assert uvx_input.source_timezone == "UTC"
        assert uvx_input.target_timezone == "GMT"
        assert uvx_input.time == "12:00"
        assert not hasattr(uvx_input, "extra")
