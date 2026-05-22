"""Tests for CSV loader helpers."""

from __future__ import annotations

import zipfile
from pathlib import Path

import polars as pl
import pytest

from jatic_library.constants import MERGED_CSV_ENCODING
from jatic_library.core.csv_loader import (
    CsvLoadError,
    find_first_csv_name,
    merge_region_zip_csvs,
    merge_region_zip_csvs_to_path,
    read_csv_frame_from_bytes,
)


def test_find_first_csv_in_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "sample.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("readme.txt", b"no")
        archive.writestr("data.csv", b"a,b\n1,2\n")

    assert find_first_csv_name(zip_path) == "data.csv"


def test_merge_region_zip_csvs(tmp_path: Path) -> None:
    first = tmp_path / "a.zip"
    second = tmp_path / "b.zip"
    with zipfile.ZipFile(first, "w") as archive:
        archive.writestr("x.csv", "col\n1\n2\n")
    with zipfile.ZipFile(second, "w") as archive:
        archive.writestr("x.csv", "col\n3\n")

    merged = merge_region_zip_csvs([first, second])
    assert merged.height == 3


def test_find_first_csv_missing(tmp_path: Path) -> None:
    zip_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("readme.txt", b"no")

    with pytest.raises(CsvLoadError):
        find_first_csv_name(zip_path)


def test_memory_error_is_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    import polars as pl

    def boom(*_args: object, **_kwargs: object) -> pl.DataFrame:
        raise MemoryError("simulated OOM")

    monkeypatch.setattr(pl, "read_csv", boom)
    with pytest.raises(MemoryError):
        read_csv_frame_from_bytes(b"a,b\n1\n")


def test_merge_region_zip_csvs_to_path_matches_in_memory(tmp_path: Path) -> None:
    first = tmp_path / "a.zip"
    second = tmp_path / "b.zip"
    third = tmp_path / "c.zip"
    with zipfile.ZipFile(first, "w") as archive:
        archive.writestr("x.csv", "col\n1\n2\n")
    with zipfile.ZipFile(second, "w") as archive:
        archive.writestr("x.csv", "col\n3\n")
    with zipfile.ZipFile(third, "w") as archive:
        archive.writestr("x.csv", "col\n4\n5\n")

    in_memory = merge_region_zip_csvs([first, second, third])
    dest = tmp_path / "merged.csv"
    merge_region_zip_csvs_to_path([first, second, third], dest, temp_dir=tmp_path)
    on_disk = pl.read_csv(dest, encoding=MERGED_CSV_ENCODING, infer_schema_length=0)
    assert on_disk.height == in_memory.height
    assert on_disk.columns == in_memory.columns


def test_read_csv_frame_from_bytes_prefers_cp932_for_japanese_header() -> None:
    """cp932 source must not be mis-read as UTF-8 (garbles header column names)."""
    raw = "都道府県,件数\n13,100\n".encode("cp932")
    frame = read_csv_frame_from_bytes(raw)
    assert frame.columns == ["都道府県", "件数"]
    assert frame.row(0) == ("13", "100")


def test_merge_region_zip_csvs_to_path_writes_shift_jis(tmp_path: Path) -> None:
    first = tmp_path / "a.zip"
    with zipfile.ZipFile(first, "w") as archive:
        archive.writestr("x.csv", "都道府県,件数\n13,100\n".encode("cp932"))

    dest = tmp_path / "merged.csv"
    merge_region_zip_csvs_to_path([first], dest, temp_dir=tmp_path)

    text = dest.read_text(encoding=MERGED_CSV_ENCODING)
    assert text.startswith("都道府県,件数")
    assert "13,100" in text


def test_merge_region_zip_csvs_to_path_empty_raises(tmp_path: Path) -> None:
    dest = tmp_path / "out.csv"
    with pytest.raises(CsvLoadError):
        merge_region_zip_csvs_to_path([], dest)
