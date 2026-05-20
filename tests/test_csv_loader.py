"""Tests for CSV preview loader."""

import zipfile
from pathlib import Path

import pytest

from jatic_library.core.csv_loader import CsvPreviewError, preview_csv_from_zip


def test_preview_csv_from_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "sample.zip"
    csv_body = b"col_a,col_b\n1,2\n3,4\n"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("data.csv", csv_body)

    headers, rows = preview_csv_from_zip(zip_path, max_rows=10)
    assert headers == ["col_a", "col_b"]
    assert len(rows) == 2
    assert rows[0] == ["1", "2"]


def test_preview_missing_csv(tmp_path: Path) -> None:
    zip_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("readme.txt", b"no csv")

    with pytest.raises(CsvPreviewError):
        preview_csv_from_zip(zip_path)
