"""Tests for CSV row counting and library labels."""

from __future__ import annotations

import zipfile
from pathlib import Path

from jatic_library.core.csv_loader import (
    count_data_rows_for_path,
    count_data_rows_in_zip,
    uncompressed_csv_size_in_zip,
)
from jatic_library.core.library_scanner import format_library_file_label


def test_uncompressed_csv_size_in_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "region.zip"
    payload = b"a,b\n" + b"1,2\n" * 100
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("data.csv", payload)
    assert uncompressed_csv_size_in_zip(zip_path) == len(payload)


def test_count_data_rows_in_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "region.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("data.csv", "a,b\n1,2\n3,4\n5,6\n")
    assert count_data_rows_in_zip(zip_path) == 3


def test_format_library_file_label() -> None:
    label = format_library_file_label("東京都", int(1.5 * 1024**3), 12_345)
    assert "東京都" in label
    assert "12,345行" in label
    assert "1.50GB" in label


def test_count_merged_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "統合.csv"
    csv_path.write_text("h\n" + "\n".join(str(i) for i in range(5)) + "\n", encoding="utf-8")
    assert count_data_rows_for_path(csv_path) == 5
