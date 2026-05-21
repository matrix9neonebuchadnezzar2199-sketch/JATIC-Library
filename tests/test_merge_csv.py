"""Tests for CSV merge helpers."""

from __future__ import annotations

import zipfile
from pathlib import Path

from jatic_library.constants import MERGED_CSV_DISPLAY_NAME, MERGED_CSV_FILENAME
from jatic_library.core.csv_loader import merge_region_zip_csvs
from jatic_library.core.library_scanner import scan_library


def test_merge_region_zip_csvs(tmp_path: Path) -> None:
    first = tmp_path / "a.zip"
    second = tmp_path / "b.zip"
    with zipfile.ZipFile(first, "w") as archive:
        archive.writestr("x.csv", "col\n1\n2\n")
    with zipfile.ZipFile(second, "w") as archive:
        archive.writestr("x.csv", "col\n3\n")

    merged = merge_region_zip_csvs([first, second])
    assert merged.height == 3
    assert merged.columns == ["col"]


def test_scan_library_includes_merged_csv(tmp_path: Path) -> None:
    folder = tmp_path / "2026_3"
    folder.mkdir()
    merged = folder / MERGED_CSV_FILENAME
    merged.write_text("a,b\n1,2\n", encoding="utf-8")

    tree = scan_library(tmp_path)
    assert len(tree) == 1
    files = tree[0].months[0].files
    assert files[0].display_name == MERGED_CSV_DISPLAY_NAME
    assert files[0].file_path == merged
