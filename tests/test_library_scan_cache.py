"""Tests for library scan statistics cache."""

from __future__ import annotations

import json
import time
from pathlib import Path

from jatic_library.core.library_scan_cache import (
    cache_key_for,
    get_cached_stats,
    set_cached_stats,
)


def test_cache_hit_returns_stored_row_count(tmp_path: Path, monkeypatch) -> None:
    cache_file = tmp_path / "library_scan_cache.json"
    monkeypatch.setattr(
        "jatic_library.core.library_scan_cache.LIBRARY_SCAN_CACHE_PATH",
        cache_file,
    )
    target = tmp_path / "sample.zip"
    target.write_bytes(b"zip")
    set_cached_stats(target, row_count=42, uncompressed_csv_size=9000)
    cached = get_cached_stats(target)
    assert cached is not None
    assert cached.row_count == 42
    assert cached.uncompressed_csv_size == 9000


def test_cache_miss_when_mtime_changes(tmp_path: Path, monkeypatch) -> None:
    cache_file = tmp_path / "library_scan_cache.json"
    monkeypatch.setattr(
        "jatic_library.core.library_scan_cache.LIBRARY_SCAN_CACHE_PATH",
        cache_file,
    )
    target = tmp_path / "sample.zip"
    target.write_bytes(b"v1")
    set_cached_stats(target, row_count=1, uncompressed_csv_size=100)
    time.sleep(0.05)
    target.write_bytes(b"v2-longer")
    assert get_cached_stats(target) is None


def test_cache_miss_when_file_size_changes(tmp_path: Path, monkeypatch) -> None:
    cache_file = tmp_path / "library_scan_cache.json"
    monkeypatch.setattr(
        "jatic_library.core.library_scan_cache.LIBRARY_SCAN_CACHE_PATH",
        cache_file,
    )
    target = tmp_path / "sample.zip"
    target.write_bytes(b"short")
    key = cache_key_for(target)
    assert key is not None
    entries = {key: {"row_count": 5, "uncompressed_csv_size": 50}}
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    target.write_bytes(b"much-longer-content")
    assert get_cached_stats(target) is None
