"""Structured JSON logging utility."""

import json
import sys
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "event"):
            log_data["event"] = record.event
        if hasattr(record, "source_url"):
            log_data["source_url"] = record.source_url
        if hasattr(record, "record_id"):
            log_data["record_id"] = record.record_id
        if hasattr(record, "field"):
            log_data["field"] = record.field
        if hasattr(record, "error"):
            log_data["error"] = record.error
        if hasattr(record, "value"):
            log_data["value"] = record.value

        # Add any other extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                if key not in log_data:
                    log_data[key] = value

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Text formatter for human-readable logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as text.

        Args:
            record: Log record to format

        Returns:
            Text-formatted log string
        """
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        level = record.levelname
        logger = record.name
        message = record.getMessage()

        log_line = f"[{timestamp}] {level:8s} [{logger}] {message}"

        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"

        return log_line


def setup_logger(
    name: str = "data_ingestion",
    level: str = "INFO",
    log_format: str = "json",
    stream: Optional[Any] = None,
) -> logging.Logger:
    """
    Setup structured logger.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('json' or 'text')
        stream: Output stream (default: stdout for INFO+, stderr for ERROR+)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Choose formatter
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Setup handlers
    # INFO and above go to stdout
    info_handler = logging.StreamHandler(sys.stdout)
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    info_handler.setFormatter(formatter)
    logger.addHandler(info_handler)

    # ERROR and above go to stderr
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


def get_logger(name: str = "data_ingestion") -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)








