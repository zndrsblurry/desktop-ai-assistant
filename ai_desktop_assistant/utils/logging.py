# Location: ai_desktop_assistant/utils/logging.py
"""
Logging Utilities

This module provides utilities for configuring logging.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = None, log_file: str = None) -> None:
    """
    Set up logging configuration.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: The file to write logs to (optional)
    """
    # Get log level from environment if not provided
    if log_level is None:
        log_level = os.environ.get("AI_ASSISTANT_LOG_LEVEL", "INFO")

    # Convert string level to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create log directory if it doesn't exist
    if log_file is None:
        log_dir = os.path.join(str(Path.home()), ".logs", "ai-desktop-assistant")
        os.makedirs(log_dir, exist_ok=True)

        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"assistant_{timestamp}.log")

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file)],
    )

    # Set specific logger levels
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    # Log initial setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level {log_level}")
    logger.info(f"Log file: {log_file}")

    return logger  # Add this return statement


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: The logger name

    Returns:
        A logger instance
    """
    return logging.getLogger(name)
