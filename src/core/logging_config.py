"""
Centralized logging configuration for the Medical Patients Generator.

Provides structured logging with configurable levels per module.
"""

import logging
import os
import sys
from typing import Optional


def configure_logging(
    level: str = "INFO",
    json_format: bool = False,
    module_levels: Optional[dict] = None,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format for production (future enhancement)
        module_levels: Dict of module names to log levels for fine-grained control
    """
    # Get level from environment or parameter
    env_level = os.environ.get("LOG_LEVEL", level).upper()
    numeric_level = getattr(logging, env_level, logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Create formatter
    if json_format:
        # Simple JSON-like format for production log aggregation
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Apply module-specific log levels
    if module_levels:
        for module_name, module_level in module_levels.items():
            logging.getLogger(module_name).setLevel(
                getattr(logging, module_level.upper(), logging.INFO)
            )

    # Default module levels for noisy libraries
    noisy_modules = [
        "urllib3",
        "asyncio",
        "httpcore",
        "httpx",
        "watchfiles",
    ]
    for module in noisy_modules:
        logging.getLogger(module).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the specified module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
