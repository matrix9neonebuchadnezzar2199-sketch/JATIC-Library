"""Resolve install directory and default data paths."""

from __future__ import annotations

import sys
from pathlib import Path

SAVE_ROOT_DIRNAME = "data"


def resolve_app_base_dir() -> Path:
    """Return the directory containing the app (exe or project root)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def default_save_root() -> Path:
    """Default download folder next to the application."""
    return resolve_app_base_dir() / SAVE_ROOT_DIRNAME


def normalize_save_root(path: Path | None) -> Path:
    """Use *path* when set; otherwise the default beside the app."""
    if path is None:
        return default_save_root()
    return path
