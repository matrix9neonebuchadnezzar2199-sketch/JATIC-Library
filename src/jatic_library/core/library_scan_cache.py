"""Disk-backed cache for expensive library file statistics (row count, CSV size)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from jatic_library.constants import LIBRARY_SCAN_CACHE_PATH


@dataclass(frozen=True)
class CachedFileStats:
    """Cached row count and uncompressed CSV size for one library file."""

    row_count: int | None
    uncompressed_csv_size: int | None


def cache_key_for(path: Path) -> str | None:
    """Build a stable cache key from path, size, and mtime."""
    try:
        stat = path.stat()
    except OSError:
        return None
    mtime_ns = getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000))
    resolved = str(path.resolve())
    payload = [resolved, stat.st_size, mtime_ns]
    return json.dumps(payload, ensure_ascii=False)


def _load_entries() -> dict[str, dict[str, int | None]]:
    if not LIBRARY_SCAN_CACHE_PATH.is_file():
        return {}
    try:
        raw = json.loads(LIBRARY_SCAN_CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read library scan cache {}: {}", LIBRARY_SCAN_CACHE_PATH, exc)
        return {}
    entries = raw.get("entries")
    if not isinstance(entries, dict):
        return {}
    return entries


def _save_entries(entries: dict[str, dict[str, int | None]]) -> None:
    LIBRARY_SCAN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {"entries": entries}
    tmp = LIBRARY_SCAN_CACHE_PATH.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(LIBRARY_SCAN_CACHE_PATH)
    except OSError as exc:
        logger.error("Failed to write library scan cache {}: {}", LIBRARY_SCAN_CACHE_PATH, exc)
        if tmp.is_file():
            tmp.unlink(missing_ok=True)
        raise


def get_cached_stats(path: Path) -> CachedFileStats | None:
    """Return cached stats when *path* matches stored size and mtime."""
    key = cache_key_for(path)
    if key is None:
        return None
    entries = _load_entries()
    stored = entries.get(key)
    if not isinstance(stored, dict):
        return None
    row_raw = stored.get("row_count")
    size_raw = stored.get("uncompressed_csv_size")
    row_count = int(row_raw) if isinstance(row_raw, int) else None
    uncompressed = int(size_raw) if isinstance(size_raw, int) else None
    return CachedFileStats(row_count=row_count, uncompressed_csv_size=uncompressed)


def set_cached_stats(
    path: Path,
    *,
    row_count: int | None,
    uncompressed_csv_size: int | None,
) -> None:
    """Persist stats for *path* under the current cache key."""
    key = cache_key_for(path)
    if key is None:
        return
    entries = _load_entries()
    entries[key] = {
        "row_count": row_count,
        "uncompressed_csv_size": uncompressed_csv_size,
    }
    _save_entries(entries)

