"""Unit tests for hello activities."""

from unittest.mock import MagicMock, patch

import pytest

from cookbook.recipes.activities.hello_activities import say_hello


class TestSayHello:
    """Test cases for say_hello activity."""

    @pytest.mark.asyncio
    async def test_say_hello_basic(self) -> None:
        """Test basic hello functionality."""
        result = await say_hello("World")
        assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_say_hello_different_names(self) -> None:
        """Test hello with different names."""
        test_cases = [
            ("Alice", "Hello, Alice!"),
            ("Bob", "Hello, Bob!"),
            ("Charlie", "Hello, Charlie!"),
            ("", "Hello, !"),
            ("123", "Hello, 123!"),
        ]

        for name, expected in test_cases:
            result = await say_hello(name)
            assert result == expected

    @pytest.mark.asyncio
    async def test_say_hello_special_characters(self) -> None:
        """Test hello with special characters in names."""
        test_cases = [
            ("Alice & Bob", "Hello, Alice & Bob!"),
            ("José", "Hello, José!"),
            ("User@Domain", "Hello, User@Domain!"),
            ("Test User", "Hello, Test User!"),
            ("user_123", "Hello, user_123!"),
        ]

        for name, expected in test_cases:
            result = await say_hello(name)
            assert result == expected

    @pytest.mark.asyncio
    async def test_say_hello_unicode_names(self) -> None:
        """Test hello with Unicode characters."""
        test_cases = [
            ("🌍", "Hello, 🌍!"),
            ("Åsa", "Hello, Åsa!"),
            ("山田太郎", "Hello, 山田太郎!"),
            ("Müller", "Hello, Müller!"),
        ]

        for name, expected in test_cases:
            result = await say_hello(name)
            assert result == expected

    @pytest.mark.asyncio
    async def test_say_hello_long_names(self) -> None:
        """Test hello with very long names."""
        long_name = "A" * 1000
        expected = f"Hello, {long_name}!"
        result = await say_hello(long_name)
        assert result == expected

    @pytest.mark.asyncio
    async def test_say_hello_whitespace_names(self) -> None:
        """Test hello with whitespace in names."""
        test_cases = [
            ("  Alice  ", "Hello,   Alice  !"),
            ("\t\nBob\t\n", "Hello, \t\nBob\t\n!"),
            ("Alice\nBob", "Hello, Alice\nBob!"),
        ]

        for name, expected in test_cases:
            result = await say_hello(name)
            assert result == expected

    @pytest.mark.asyncio
    @patch("cookbook.recipes.activities.hello_activities.activity.logger")
    async def test_say_hello_logging(self, mock_logger: MagicMock) -> None:
        """Test that activity logs the generated greeting."""
        name = "TestUser"
        result = await say_hello(name)

        expected_greeting = "Hello, TestUser!"
        assert result == expected_greeting

        # Verify logging was called with correct message
        mock_logger.info.assert_called_once_with(f"Generated greeting: {expected_greeting}")

    @pytest.mark.asyncio
    @patch("cookbook.recipes.activities.hello_activities.activity.logger")
    async def test_say_hello_logging_multiple_calls(self, mock_logger: MagicMock) -> None:
        """Test logging behavior with multiple calls."""
        names = ["Alice", "Bob", "Charlie"]

        for name in names:
            await say_hello(name)

        # Verify all calls were logged
        assert mock_logger.info.call_count == len(names)

        # Check that each call was logged correctly
        for i, name in enumerate(names):
            expected_message = f"Generated greeting: Hello, {name}!"
            assert mock_logger.info.call_args_list[i][0][0] == expected_message

    @pytest.mark.asyncio
    async def test_say_hello_return_type(self) -> None:
        """Test that say_hello returns a string."""
        result = await say_hello("TypeTest")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_say_hello_format_consistency(self) -> None:
        """Test that the greeting format is consistent."""
        names = ["Alice", "Bob", "Charlie", "", "123"]

        for name in names:
            result = await say_hello(name)
            # Check format: "Hello, <name>!"
            assert result.startswith("Hello, ")
            assert result.endswith("!")
            # Extract name from result
            extracted_name = result[7:-1]  # Remove "Hello, " and "!"
            assert extracted_name == name
