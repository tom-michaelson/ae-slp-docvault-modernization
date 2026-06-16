import pytest
from temporalio.testing import ActivityEnvironment

from awa.core.activities.say_hello import say_hello_activity


class TestSayHelloActivity:
    @pytest.mark.asyncio
    async def test_say_hello_activity_returns_correct_greeting(self, activity_env: ActivityEnvironment) -> None:
        # Arrange
        name = "World"
        expected_result = "Hello, World!"

        # Act
        result = await activity_env.run(say_hello_activity, name)

        # Assert
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_say_hello_activity_with_different_names(self, activity_env: ActivityEnvironment) -> None:
        # Arrange
        test_cases = [
            ("Alice", "Hello, Alice!"),
            ("Bob", "Hello, Bob!"),
            ("", "Hello, !"),
            ("123", "Hello, 123!"),
        ]

        for name, expected in test_cases:
            # Act
            result = await activity_env.run(say_hello_activity, name)

            # Assert
            assert result == expected, f"Failed for name: {name}"
