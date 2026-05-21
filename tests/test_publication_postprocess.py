"""Tests for post-download extract and merged CSV."""

from __future__ import annotations

import zipfile
from pathlib import Path

import polars as pl

from jatic_library.constants import EXTRACTED_DIR_NAME, MERGED_CSV_FILENAME
from jatic_library.core.publication_postprocess import postprocess_publication_folder
from jatic_library.core.targets import TARGETS


def _write_region_zip(path: Path, region: str, rows: str) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("data.csv", f"region,volume\n{rows}\n")


def test_postprocess_extracts_and_merges(tmp_path: Path) -> None:
    folder = tmp_path / "2026_3"
    folder.mkdir()
    _write_region_zip(folder / "東京都.zip", "tokyo", "tokyo,100")
    _write_region_zip(folder / "神奈川県.zip", "kanagawa", "kanagawa,200")

    tokyo = next(t for t in TARGETS if t.code == "tokyo")
    kanagawa = next(t for t in TARGETS if t.code == "kanagawa")
    merged_path = postprocess_publication_folder(folder, [tokyo, kanagawa])
    assert merged_path is not None
    assert merged_path.name == MERGED_CSV_FILENAME
    assert (folder / EXTRACTED_DIR_NAME / "東京都").is_dir()
    assert (folder / EXTRACTED_DIR_NAME / "神奈川県").is_dir()

    frame = pl.read_csv(merged_path)
    assert frame.height == 2
    assert set(frame["region"].to_list()) == {"tokyo", "kanagawa"}
