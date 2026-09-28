"""Tests for logging configuration and utilities."""

import logging
from pathlib import Path

from sage_indic.logging import get_logger, setup_logging


def test_get_logger():
    """Verify get_logger returns a standard Logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_setup_logging_console():
    """Verify setup_logging configures root logger level and handler."""
    setup_logging(level="DEBUG")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) >= 1


def test_setup_logging_file(tmp_path: Path):
    """Verify setup_logging creates file handler when log_file is specified."""
    log_file = tmp_path / "test.log"
    setup_logging(level="INFO", log_file=log_file)
    logger = get_logger("file_test")
    logger.info("Test message")

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Test message" in content
