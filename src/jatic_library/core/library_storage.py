"""Disk usage helpers for the library tab header."""

from __future__ import annotations

import shutil
from pathlib import Path


def directory_size_bytes(root: Path) -> int:
    """Return total byte size of all files under *root*."""
    if not root.is_dir():
        return 0
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            try:
                total += path.stat().st_size
            except OSError:
                continue
    return total


def format_storage_usage_label(save_root: Path | None) -> str:
    """Format ``library / disk_total (pct% 使用)`` for the tree header."""
    if save_root is None or not save_root.exists():
        return "— / —（—% 使用）"
    try:
        library_bytes = directory_size_bytes(save_root)
        disk = shutil.disk_usage(save_root)
    except OSError:
        return "— / —（—% 使用）"

    library_gb = library_bytes / (1024**3)
    disk_gb = disk.total / (1024**3)
    percent = (library_bytes / disk.total * 100) if disk.total else 0.0
    return f"{library_gb:.2f} GB / {disk_gb:.2f} GB（{percent:.1f}% 使用）"
