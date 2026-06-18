"""Custom logging formatter with color support."""

import logging
from typing import ClassVar


class LogFormatter(logging.Formatter):
    """A custom logging formatter that adds color to log messages based on their severity level.

    Attributes:
        grey (str): ANSI escape code for grey color, used for DEBUG and INFO messages.
        yellow (str): ANSI escape code for yellow color, used for WARNING messages.
        red (str): ANSI escape code for red color, used for ERROR messages.
        bold_red (str): ANSI escape code for bold red color, used for CRITICAL messages.
        reset (str): ANSI escape code to reset color formatting.
        base_format (str): The base format string for log messages.
        FORMATS (dict): Mapping of logging levels to their respective colored format strings.

    Methods:
        format(record):
            Formats the specified log record with the appropriate color
            and format based on its severity level.

    """

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    base_format = "%(asctime)s | %(levelname)s | %(name)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS: ClassVar[dict] = {
        logging.DEBUG: f"{grey}{base_format}{reset}",
        logging.INFO: f"{grey}{base_format}{reset}",
        logging.WARNING: f"{yellow}{base_format}{reset}",
        logging.ERROR: f"{red}{base_format}{reset}",
        logging.CRITICAL: f"{bold_red}{base_format}{reset}",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
