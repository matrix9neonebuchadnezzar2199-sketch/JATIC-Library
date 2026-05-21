"""Loguru configuration."""

import sys
from pathlib import Path
from typing import Any

from loguru import logger

from jatic_library.settings.config import LogSettings

_RETENTION_MAP = {
    "30d": "30 days",
    "90d": "90 days",
    "infinite": "3650 days",
}


def setup_logging(log_dir: Path, log_settings: LogSettings | None = None) -> None:
    """Configure stderr and rotating file logging."""
    settings = log_settings or LogSettings()
    retention = _RETENTION_MAP.get(settings.retention, "90 days")
    logger.remove()
    # PyInstaller windowed exe (console=False) has sys.stderr is None.
    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            level=settings.level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
        )
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_dir / "app-{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention=retention,
            encoding="utf-8",
            level="DEBUG",
        )
    except OSError as exc:
        logger.warning("Could not create log directory {}: {}", log_dir, exc)


def get_logger() -> Any:
    """Return the configured loguru logger."""
    return logger
