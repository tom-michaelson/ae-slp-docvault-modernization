"""Test cases for InvalidInputApplicationError."""

import pytest
from temporalio.exceptions import ApplicationError

from awa.sdk.models.exceptions.invalid_input_error import InvalidInputApplicationError


class TestInvalidInputApplicationError:
    """Test cases for InvalidInputApplicationError."""

    def test_invalid_input_error_creation(self) -> None:
        """Test creating InvalidInputApplicationError with message."""
        # Arrange
        message = "Invalid input provided"

        # Act
        error = InvalidInputApplicationError(message)

        # Assert
        assert isinstance(error, ApplicationError)
        assert str(error) == message
        assert error.non_retryable is True

    def test_invalid_input_error_with_details(self) -> None:
        """Test creating InvalidInputApplicationError with message and details."""
        # Arrange
        message = "Invalid input"
        detail1 = "Field 'name' is required"
        detail2 = "Field 'age' must be positive"

        # Act
        error = InvalidInputApplicationError(message, detail1, detail2)

        # Assert
        assert isinstance(error, ApplicationError)
        assert str(error) == message
        assert error.non_retryable is True

    def test_invalid_input_error_inheritance(self) -> None:
        """Test that InvalidInputApplicationError inherits from ApplicationError."""
        # Arrange & Act
        error = InvalidInputApplicationError("Test message")

        # Assert
        assert isinstance(error, ApplicationError)

    def test_invalid_input_error_non_retryable(self) -> None:
        """Test that InvalidInputApplicationError is non-retryable by default."""
        # Arrange & Act
        error = InvalidInputApplicationError("Test message")

        # Assert
        assert error.non_retryable is True

    def test_invalid_input_error_raise_and_catch(self) -> None:
        """Test raising and catching InvalidInputApplicationError."""
        # Arrange
        message = "This input is invalid"

        # Act & Assert
        with pytest.raises(InvalidInputApplicationError) as exc_info:
            raise InvalidInputApplicationError(message)

        assert str(exc_info.value) == message
        assert exc_info.value.non_retryable is True

    def test_invalid_input_error_catch_as_application_error(self) -> None:
        """Test catching InvalidInputApplicationError as ApplicationError."""
        # Arrange
        message = "Invalid input test"

        # Act & Assert
        with pytest.raises(ApplicationError) as exc_info:
            raise InvalidInputApplicationError(message)

        # Should catch as ApplicationError parent class
        assert isinstance(exc_info.value, InvalidInputApplicationError)
        assert str(exc_info.value) == message
