"""Sample Python file for demonstrating the SingleFileDiffWorkflow.

This file contains a simple class with methods that can be modified by the workflow.
"""

import logging

logger = logging.getLogger(__name__)


class Calculator:
    """A simple calculator class with basic arithmetic operations."""

    def __init__(self, initial_value: float = 0) -> None:
        """Initialize the calculator with an initial value.

        Args:
            initial_value: The initial value for calculations.

        """
        self.value = initial_value

    def add(self, num: float) -> float:
        """Add a number to the current value.

        Args:
            num: The number to add.

        Returns:
            The updated value.

        """
        self.value += num
        return self.value

    def subtract(self, num: float) -> float:
        """Subtract a number from the current value.

        Args:
            num: The number to subtract.

        Returns:
            The updated value.

        """
        self.value -= num
        return self.value

    def multiply(self, num: float) -> float:
        """Multiply the current value by a number.

        Args:
            num: The number to multiply by.

        Returns:
            The updated value.

        """
        self.value *= num
        return self.value

    def divide(self, num: float) -> float:
        """Divide the current value by a number.

        Args:
            num: The number to divide by.

        Returns:
            The updated value.

        Raises:
            ValueError: If the divisor is zero.

        """
        if num == 0:
            raise ValueError("Cannot divide by zero")
        self.value /= num
        return self.value

    def get_value(self) -> float:
        """Get the current value.

        Returns:
            The current value.

        """
        return self.value

    def reset(self) -> float:
        """Reset the calculator to zero.

        Returns:
            The reset value (0).

        """
        self.value = 0
        return self.value


def main() -> None:
    """Run the calculator demonstration."""
    logging.basicConfig(level=logging.INFO)
    calc = Calculator(10)
    logger.info(f"Initial value: {calc.get_value()}")
    logger.info(f"Add 5: {calc.add(5)}")
    logger.info(f"Subtract 3: {calc.subtract(3)}")
    logger.info(f"Multiply by 2: {calc.multiply(2)}")
    logger.info(f"Divide by 4: {calc.divide(4)}")
    logger.info(f"Final value: {calc.get_value()}")
    calc.reset()
    logger.info(f"After reset: {calc.get_value()}")


if __name__ == "__main__":
    main()
