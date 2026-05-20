"""Loguru configuration."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_dir: Path) -> None:
    """Configure file and stderr logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
    )
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_dir / "app-{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            encoding="utf-8",
            level="DEBUG",
        )
    except OSError as exc:
        logger.warning("Could not create log directory {}: {}", log_dir, exc)
