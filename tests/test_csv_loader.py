"""Tests for CSV loader helpers."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from jatic_library.core.csv_loader import (
    CsvLoadError,
    find_first_csv_name,
    merge_region_zip_csvs,
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
