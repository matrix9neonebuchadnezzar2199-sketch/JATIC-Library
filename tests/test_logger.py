"""Tests for logging setup."""

import sys
from pathlib import Path

from jatic_library.core.logger import get_logger, setup_logging
from jatic_library.settings.config import LogSettings


def test_setup_logging_creates_file(tmp_path: Path) -> None:
    setup_logging(tmp_path, LogSettings(level="DEBUG", retention="30d"))
    log = get_logger()
    log.info("test message")
    assert list(tmp_path.glob("app-*.log"))


def test_setup_logging_without_stderr(tmp_path: Path, monkeypatch) -> None:
    """Windowed PyInstaller builds expose stderr as None."""
    monkeypatch.setattr(sys, "stderr", None)
    setup_logging(tmp_path, LogSettings(level="INFO", retention="30d"))
    get_logger().info("no stderr sink")
    assert list(tmp_path.glob("app-*.log"))
