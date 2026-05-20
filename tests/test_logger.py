"""Tests for logging setup."""

from pathlib import Path

from jatic_library.core.logger import get_logger, setup_logging
from jatic_library.settings.config import LogSettings


def test_setup_logging_creates_file(tmp_path: Path) -> None:
    setup_logging(tmp_path, LogSettings(level="DEBUG", retention="30d"))
    log = get_logger()
    log.info("test message")
    assert list(tmp_path.glob("app-*.log"))
