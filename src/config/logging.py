"""
Logging configuration for the application.

Provides structured logging with:
- Console output (INFO and above) for development
- Per-run file logs (DEBUG and above) - each app run gets its own log file
- Configurable log levels via environment variables
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """
    Configure application-wide logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files

    Sets up:
        - Console handler with INFO level
        - Per-run file handler with DEBUG level (unique file for each run)
        - Structured format with timestamps and module info
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    app_log_path = log_path / "app"
    app_log_path.mkdir(parents=True, exist_ok=True)

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, handlers will filter

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_formatter = logging.Formatter(
        "%(levelname)-8s [%(name)s] %(message)s",
    )

    # Console Handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler - Per-run log file (DEBUG and above)
    # Create unique filename with timestamp for this run
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = app_log_path / f"app_{timestamp}.log"

    file_handler = logging.FileHandler(
        filename=log_file,
        mode="a",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Log the initialization
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: level={log_level}, dir={log_dir}")
    logger.debug(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
