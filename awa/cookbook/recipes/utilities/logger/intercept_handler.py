import logging
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from types import FrameType


class InterceptHandler(logging.Handler):
    """Handler that intercepts standard logging and routes to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()

        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = logging.getLevelName(record.levelno)

        # Find caller from where originated the logged message
        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Build extra context
        extra_context = {}

        # Add original logger name for reference
        if record.name and record.name != "root":
            extra_context["original_logger"] = record.name

        logger.opt(depth=depth, exception=record.exc_info).bind(**extra_context).log(
            level,
            message,
        )
