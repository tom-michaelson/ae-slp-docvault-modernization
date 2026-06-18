"""Test cases for RetryableApplicationError."""

import pytest
from temporalio.exceptions import ApplicationError

from awa.sdk.models.exceptions.retryable_application_error import RetryableApplicationError


class TestRetryableApplicationError:
    """Test cases for RetryableApplicationError."""

    def test_retryable_error_creation(self) -> None:
        """Test creating RetryableApplicationError with message."""
        # Arrange
        message = "Temporary service unavailable"

        # Act
        error = RetryableApplicationError(message)

        # Assert
        assert isinstance(error, ApplicationError)
        assert str(error) == message
        assert error.non_retryable is False

    def test_retryable_error_with_details(self) -> None:
        """Test creating RetryableApplicationError with message and details."""
        # Arrange
        message = "Service error"
        detail1 = "Connection timeout"
        detail2 = "Retry in 30 seconds"

        # Act
        error = RetryableApplicationError(message, detail1, detail2)

        # Assert
        assert isinstance(error, ApplicationError)
        assert str(error) == message
        assert error.non_retryable is False

    def test_retryable_error_inheritance(self) -> None:
        """Test that RetryableApplicationError inherits from ApplicationError."""
        # Arrange & Act
        error = RetryableApplicationError("Test message")

        # Assert
        assert isinstance(error, ApplicationError)

    def test_retryable_error_is_retryable(self) -> None:
        """Test that RetryableApplicationError is retryable by default."""
        # Arrange & Act
        error = RetryableApplicationError("Test message")

        # Assert
        assert error.non_retryable is False

    def test_retryable_error_raise_and_catch(self) -> None:
        """Test raising and catching RetryableApplicationError."""
        # Arrange
        message = "This error can be retried"

        # Act & Assert
        with pytest.raises(RetryableApplicationError) as exc_info:
            raise RetryableApplicationError(message)

        assert str(exc_info.value) == message
        assert exc_info.value.non_retryable is False

    def test_retryable_error_catch_as_application_error(self) -> None:
        """Test catching RetryableApplicationError as ApplicationError."""
        # Arrange
        message = "Retryable error test"

        # Act & Assert
        with pytest.raises(ApplicationError) as exc_info:
            raise RetryableApplicationError(message)

        # Should catch as ApplicationError parent class
        assert isinstance(exc_info.value, RetryableApplicationError)
        assert str(exc_info.value) == message

    def test_contrast_with_invalid_input_error(self) -> None:
        """Test that RetryableApplicationError behaves differently from non-retryable errors."""
        # This test demonstrates the difference between retryable and non-retryable errors

        # Arrange & Act
        retryable_error = RetryableApplicationError("Temporary failure")

        # Assert - RetryableApplicationError should be retryable
        assert retryable_error.non_retryable is False

        # For comparison - this would be true for non-retryable errors
        # but we're just testing that our retryable error is indeed retryable
