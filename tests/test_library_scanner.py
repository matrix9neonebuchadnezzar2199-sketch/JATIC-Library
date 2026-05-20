"""Tests for library folder scanner."""

from pathlib import Path

from jatic_library.core.library_scanner import scan_library
from jatic_library.core.manifest import Manifest, ManifestFileEntry
from jatic_library.core.repository import Repository


def test_scan_library_empty_root(tmp_path: Path) -> None:
    assert scan_library(tmp_path) == []


def test_scan_library_month_and_file(tmp_path: Path) -> None:
    save_root = tmp_path / "data"
    folder = save_root / "2026_3"
    folder.mkdir(parents=True)
    zip_path = folder / "東京都.zip"
    zip_path.write_bytes(b"fake")

    manifest = Manifest(
        publish_ym="2026_3",
        publish_date="2026-05-01",
        downloaded_at="2026-05-01T10:00:00+09:00",
        source_dir_url="https://example.test/",
        files=[
            ManifestFileEntry(
                target_code="tokyo",
                display_name="東京都",
                filename="東京都.zip",
                source_url="https://example.test/typeB_tokyo.zip",
                size=4,
                sha256="abc",
                downloaded_at="2026-05-01T10:00:00+09:00",
            )
        ],
    )
    manifest.save(folder)

    db = tmp_path / "hist.db"
    with Repository(db) as repo:
        repo.upsert_publication("2026_3", "2026-05-01", "complete")
        years = scan_library(save_root, repo)

    assert len(years) == 1
    assert years[0].year == 2026
    assert len(years[0].months) == 1
    files = years[0].months[0].files
    assert len(files) == 1
    assert files[0].target_code == "tokyo"
    assert files[0].sha256 == "abc"


def test_scan_ignores_invalid_folder(tmp_path: Path) -> None:
    save_root = tmp_path / "data"
    save_root.mkdir()
    (save_root / "not_a_month").mkdir()
    assert scan_library(save_root) == []
