"""Unit tests for models/command_result.py."""

import json
from typing import Any

import pytest
from pydantic import ValidationError

from awa.sdk.models.command_result import CommandInput, CommandResult


class TestCommandInput:
    """Test cases for CommandInput model."""

    def test_command_input_with_required_fields_only(self) -> None:
        """Test CommandInput creation with only required field."""
        cmd_input = CommandInput(command="echo hello")

        assert cmd_input.command == "echo hello"
        assert cmd_input.working_dir is None

    def test_command_input_with_all_fields(self) -> None:
        """Test CommandInput creation with all fields."""
        cmd_input = CommandInput(
            command="ls -la",
            working_dir="/opt/test",
        )

        assert cmd_input.command == "ls -la"
        assert cmd_input.working_dir == "/opt/test"

    def test_command_input_empty_command(self) -> None:
        """Test CommandInput with empty command string."""
        cmd_input = CommandInput(command="")

        assert cmd_input.command == ""
        assert cmd_input.working_dir is None

    def test_command_input_working_dir_none_explicit(self) -> None:
        """Test CommandInput with explicitly set None working_dir."""
        cmd_input = CommandInput(command="pwd", working_dir=None)

        assert cmd_input.command == "pwd"
        assert cmd_input.working_dir is None

    def test_command_input_working_dir_empty_string(self) -> None:
        """Test CommandInput with empty string working_dir."""
        cmd_input = CommandInput(command="pwd", working_dir="")

        assert cmd_input.command == "pwd"
        assert cmd_input.working_dir == ""

    def test_command_input_missing_required_field(self) -> None:
        """Test CommandInput validation fails without required command field."""
        with pytest.raises(ValidationError) as exc_info:
            CommandInput()  # type: ignore[call-arg]

        error = exc_info.value
        assert len(error.errors()) == 1
        assert error.errors()[0]["type"] == "missing"
        assert error.errors()[0]["loc"] == ("command",)

    def test_command_input_invalid_types(self) -> None:
        """Test CommandInput validation with invalid field types."""
        # Invalid command type
        with pytest.raises(ValidationError) as exc_info:
            CommandInput(command=123)  # type: ignore[arg-type]

        error = exc_info.value
        assert any("string" in str(err) for err in error.errors())

        # Invalid working_dir type
        with pytest.raises(ValidationError) as exc_info:
            CommandInput(command="test", working_dir=123)  # type: ignore[arg-type]

        error = exc_info.value
        assert any("string" in str(err) for err in error.errors())

    def test_command_input_serialization(self) -> None:
        """Test CommandInput model serialization."""
        cmd_input = CommandInput(command="test", working_dir="/path")

        # Test model_dump
        data = cmd_input.model_dump()
        expected = {"command": "test", "working_dir": "/path"}
        assert data == expected

        # Test model_dump_json
        json_str = cmd_input.model_dump_json()
        assert '"command":"test"' in json_str
        assert '"working_dir":"/path"' in json_str

    def test_command_input_equality(self) -> None:
        """Test CommandInput equality comparison."""
        cmd1 = CommandInput(command="test", working_dir="/path")
        cmd2 = CommandInput(command="test", working_dir="/path")
        cmd3 = CommandInput(command="different", working_dir="/path")

        assert cmd1 == cmd2
        assert cmd1 != cmd3


class TestCommandResult:
    """Test cases for CommandResult model."""

    def test_command_result_with_all_fields_explicit(self) -> None:
        """Test CommandResult creation with all fields explicitly set."""
        result = CommandResult(
            exit_code=0,
            output="success output",
            success=True,
        )

        assert result.exit_code == 0
        assert result.output == "success output"
        assert result.success is True

    def test_command_result_auto_success_true_for_exit_code_zero(self) -> None:
        """Test CommandResult automatically sets success=True for exit_code=0."""
        # This tests lines 22-24 in the original code
        result = CommandResult(
            exit_code=0,
            output="command succeeded",
        )

        assert result.exit_code == 0
        assert result.output == "command succeeded"
        assert result.success is True

    def test_command_result_auto_success_false_for_nonzero_exit_code(self) -> None:
        """Test CommandResult automatically sets success=False for non-zero exit_code."""
        # This tests lines 22-24 in the original code
        result = CommandResult(
            exit_code=1,
            output="command failed",
        )

        assert result.exit_code == 1
        assert result.output == "command failed"
        assert result.success is False

    def test_command_result_auto_success_false_for_negative_exit_code(self) -> None:
        """Test CommandResult automatically sets success=False for negative exit_code."""
        # This tests lines 22-24 in the original code
        result = CommandResult(
            exit_code=-1,
            output="command crashed",
        )

        assert result.exit_code == -1
        assert result.output == "command crashed"
        assert result.success is False

    def test_command_result_auto_success_false_for_high_exit_code(self) -> None:
        """Test CommandResult automatically sets success=False for high exit_code."""
        # This tests lines 22-24 in the original code
        result = CommandResult(
            exit_code=255,
            output="command error",
        )

        assert result.exit_code == 255
        assert result.output == "command error"
        assert result.success is False

    def test_command_result_explicit_success_overrides_auto_logic(self) -> None:
        """Test explicitly set success field overrides automatic logic."""
        # success=False with exit_code=0
        result1 = CommandResult(
            exit_code=0,
            output="output",
            success=False,
        )
        assert result1.success is False

        # success=True with exit_code=1
        result2 = CommandResult(
            exit_code=1,
            output="output",
            success=True,
        )
        assert result2.success is True

    def test_command_result_empty_output(self) -> None:
        """Test CommandResult with empty output string."""
        result = CommandResult(
            exit_code=0,
            output="",
        )

        assert result.exit_code == 0
        assert result.output == ""
        assert result.success is True

    def test_command_result_multiline_output(self) -> None:
        """Test CommandResult with multiline output."""
        multiline_output = "Line 1\nLine 2\nLine 3"
        result = CommandResult(
            exit_code=0,
            output=multiline_output,
        )

        assert result.exit_code == 0
        assert result.output == multiline_output
        assert result.success is True

    def test_command_result_missing_required_fields(self) -> None:
        """Test CommandResult validation fails without required fields."""
        # Missing exit_code
        with pytest.raises(ValidationError) as exc_info:
            CommandResult(output="test")  # type: ignore[call-arg]

        error = exc_info.value
        assert any(err["loc"] == ("exit_code",) and err["type"] == "missing" for err in error.errors())

        # Missing output
        with pytest.raises(ValidationError) as exc_info:
            CommandResult(exit_code=0)  # type: ignore[call-arg]

        error = exc_info.value
        assert any(err["loc"] == ("output",) and err["type"] == "missing" for err in error.errors())

    def test_command_result_invalid_types(self) -> None:
        """Test CommandResult validation with invalid field types."""
        # Invalid exit_code type
        with pytest.raises(ValidationError) as exc_info:
            CommandResult(exit_code="invalid", output="test", success=True)  # type: ignore[arg-type]

        error = exc_info.value
        assert any("int" in str(err) for err in error.errors())

        # Invalid output type
        with pytest.raises(ValidationError) as exc_info:
            CommandResult(exit_code=0, output=123, success=True)  # type: ignore[arg-type]

        error = exc_info.value
        assert any("string" in str(err) for err in error.errors())

        # Invalid success type
        with pytest.raises(ValidationError) as exc_info:
            CommandResult(exit_code=0, output="test", success="invalid")  # type: ignore[arg-type]

        error = exc_info.value
        assert any("bool" in str(err) for err in error.errors())

    def test_command_result_serialization(self) -> None:
        """Test CommandResult model serialization."""
        result = CommandResult(
            exit_code=1,
            output="error message",
        )

        # Test model_dump
        data = result.model_dump()
        expected = {
            "exit_code": 1,
            "output": "error message",
            "success": False,
        }
        assert data == expected

        # Test model_dump_json
        json_str = result.model_dump_json()
        assert '"exit_code":1' in json_str
        assert '"output":"error message"' in json_str
        assert '"success":false' in json_str

    def test_command_result_equality(self) -> None:
        """Test CommandResult equality comparison."""
        result1 = CommandResult(exit_code=0, output="test")
        result2 = CommandResult(exit_code=0, output="test")
        result3 = CommandResult(exit_code=1, output="test")

        assert result1 == result2
        assert result1 != result3

    def test_command_result_init_with_kwargs(self) -> None:
        """Test CommandResult initialization with various kwargs combinations."""
        # Test with only required fields as kwargs
        data: dict[str, Any] = {"exit_code": 2, "output": "test output"}
        result = CommandResult(**data)

        assert result.exit_code == 2
        assert result.output == "test output"
        assert result.success is False

    def test_command_result_boundary_exit_codes(self) -> None:
        """Test CommandResult with boundary exit code values."""
        # Test with zero
        result_zero = CommandResult(exit_code=0, output="")
        assert result_zero.success is True

        # Test with positive boundary
        result_pos = CommandResult(exit_code=127, output="")
        assert result_pos.success is False

        # Test with negative boundary
        result_neg = CommandResult(exit_code=-128, output="")
        assert result_neg.success is False

    def test_command_result_unicode_output(self) -> None:
        """Test CommandResult with unicode characters in output."""
        unicode_output = "Hello 世界 🌍 café naïve résumé"
        result = CommandResult(
            exit_code=0,
            output=unicode_output,
        )

        assert result.output == unicode_output
        assert result.success is True

    def test_command_result_large_output(self) -> None:
        """Test CommandResult with large output string."""
        large_output = "x" * 10000
        result = CommandResult(
            exit_code=0,
            output=large_output,
        )

        assert result.output == large_output
        assert len(result.output) == 10000
        assert result.success is True

    def test_command_result_json_roundtrip(self) -> None:
        """Test CommandResult JSON serialization and deserialization roundtrip."""
        original = CommandResult(
            exit_code=42,
            output="test output with special chars: \n\t\r",
        )

        # Serialize to JSON
        json_data = original.model_dump_json()

        # Deserialize back
        data = json.loads(json_data)
        restored = CommandResult(**data)

        assert restored == original
        assert restored.exit_code == original.exit_code
        assert restored.output == original.output
        assert restored.success == original.success

    def test_command_result_auto_success_edge_cases(self) -> None:
        """Test edge cases for automatic success field setting."""
        # Test when success key exists but is None (should not auto-set)
        # Note: Pydantic will validate this, so we test valid scenarios

        # Test the specific condition in __init__ where success not in data
        result = CommandResult.model_validate(
            {
                "exit_code": 0,
                "output": "test",
                # success not provided - should auto-set
            },
        )
        assert result.success is True

        # Test when exit_code not in data (should not auto-set success)
        with pytest.raises(ValidationError):
            CommandResult.model_validate(
                {
                    "output": "test",
                    # exit_code missing - should fail validation
                },
            )

    def test_command_result_pydantic_features(self) -> None:
        """Test CommandResult with various Pydantic features."""
        # Test field access
        result = CommandResult(exit_code=0, output="test")

        # Test __dict__ access
        assert result.__dict__["exit_code"] == 0
        assert result.__dict__["output"] == "test"
        assert result.__dict__["success"] is True

        # Test model_fields
        assert "exit_code" in CommandResult.model_fields
        assert "output" in CommandResult.model_fields
        assert "success" in CommandResult.model_fields
