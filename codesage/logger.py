"""
codesage.logger
~~~~~~~~~~~~~~~
Centralised logging setup using Python's stdlib logging + Rich handler.
"""

import logging
import sys

from rich.logging import RichHandler

from codesage.config import config


def get_logger(name: str = "codesage") -> logging.Logger:
    """Return a configured logger instance.

    Args:
        name: Logger namespace (typically the module __name__).

    Returns:
        A stdlib Logger configured with a Rich console handler.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Avoid adding duplicate handlers on repeated calls
        return logger

    level = getattr(logging, config.log_level, logging.INFO)
    logger.setLevel(level)

    handler = RichHandler(
        rich_tracebacks=True,
        show_path=False,
        markup=True,
        log_time_format="[%X]",
    )
    handler.setLevel(level)
    logger.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return logger
