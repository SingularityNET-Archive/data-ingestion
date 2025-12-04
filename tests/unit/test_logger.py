"""Unit tests for logger utility."""

import json
import logging
import sys

from src.lib.logger import JSONFormatter, LogLevel, TextFormatter, setup_logger


class TestJSONFormatter:
    """Tests for JSON formatter."""

    def test_format_basic_log(self):
        """Test formatting basic log record."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        data = json.loads(result)
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert "logger" in data

    def test_format_with_extra_fields(self):
        """Test formatting log record with extra fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.event = "test_event"
        record.source_url = "https://example.com"
        record.record_id = "123"
        result = formatter.format(record)
        data = json.loads(result)
        assert data["event"] == "test_event"
        assert data["source_url"] == "https://example.com"
        assert data["record_id"] == "123"

    def test_format_with_exception(self):
        """Test formatting log record with exception."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=sys.exc_info(),
            )
            result = formatter.format(record)
            data = json.loads(result)
            assert "exception" in data
            assert data["level"] == "ERROR"


class TestTextFormatter:
    """Tests for text formatter."""

    def test_format_basic_log(self):
        """Test formatting basic log record."""
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "INFO" in result
        assert "Test message" in result
        assert "test" in result  # logger name

    def test_format_with_exception(self):
        """Test formatting log record with exception."""
        formatter = TextFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=sys.exc_info(),
            )
            result = formatter.format(record)
            assert "ERROR" in result
            assert "Test message" in result
            assert "ValueError" in result


class TestSetupLogger:
    """Tests for logger setup."""

    def test_setup_json_logger(self):
        """Test setting up JSON logger."""
        logger = setup_logger("test_logger", "INFO", "json")
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 2  # INFO handler and ERROR handler

    def test_setup_text_logger(self):
        """Test setting up text logger."""
        logger = setup_logger("test_logger", "DEBUG", "text")
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 2

    def test_logger_output_json(self, capfd):
        """Test that JSON logger outputs JSON format."""
        logger = setup_logger("test_logger", "INFO", "json")
        logger.info("Test message", extra={"event": "test"})
        out, err = capfd.readouterr()
        # Should output to stdout for INFO level
        assert len(out) > 0
        data = json.loads(out.strip())
        assert data["message"] == "Test message"
        assert data["event"] == "test"

    def test_logger_output_text(self, capfd):
        """Test that text logger outputs text format."""
        logger = setup_logger("test_logger", "INFO", "text")
        logger.info("Test message")
        out, err = capfd.readouterr()
        assert "Test message" in out
        assert "INFO" in out

    def test_logger_error_to_stderr(self, capfd):
        """Test that ERROR level logs go to stderr."""
        logger = setup_logger("test_logger", "INFO", "json")
        logger.error("Error message")
        out, err = capfd.readouterr()
        # Error should go to stderr
        assert len(err) > 0
        data = json.loads(err.strip())
        assert data["level"] == "ERROR"
        assert data["message"] == "Error message"

    def test_logger_info_to_stdout(self, capfd):
        """Test that INFO level logs go to stdout."""
        logger = setup_logger("test_logger", "INFO", "json")
        logger.info("Info message")
        out, err = capfd.readouterr()
        # Info should go to stdout
        assert len(out) > 0
        data = json.loads(out.strip())
        assert data["level"] == "INFO"

    def test_logger_level_filtering(self, capfd):
        """Test that logger respects level filtering."""
        logger = setup_logger("test_logger", "WARNING", "json")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        out, err = capfd.readouterr()
        # Only warning should appear
        lines = [line for line in out.strip().split("\n") if line]
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["level"] == "WARNING"


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_log_level_values(self):
        """Test LogLevel enum values."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"






