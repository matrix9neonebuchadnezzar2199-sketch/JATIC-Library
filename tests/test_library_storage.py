"""Tests for library storage usage label."""

from __future__ import annotations

from pathlib import Path

from jatic_library.core.library_storage import directory_size_bytes, format_storage_usage_label


def test_directory_size_bytes(tmp_path: Path) -> None:
    root = tmp_path / "data"
    folder = root / "2026_3"
    folder.mkdir(parents=True)
    (folder / "a.bin").write_bytes(b"x" * 1000)
    assert directory_size_bytes(root) == 1000


def test_format_storage_usage_label(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "data"
    root.mkdir()
    (root / "file.bin").write_bytes(b"0" * 1024)

    class _Usage:
        total = 100 * 1024**3
        used = 50 * 1024**3
        free = 50 * 1024**3

    monkeypatch.setattr(
        "jatic_library.core.library_storage.shutil.disk_usage",
        lambda _path: _Usage(),
    )
    label = format_storage_usage_label(root)
    assert "GB /" in label
    assert "% 使用）" in label
