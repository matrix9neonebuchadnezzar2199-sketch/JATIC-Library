"""Tests for export helpers."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from jatic_library.core.exporter import ExportError, export_publication_zip_bundle


def test_export_zip_bundle(tmp_path: Path) -> None:
    save_root = tmp_path / "data"
    folder = save_root / "2026_3"
    folder.mkdir(parents=True)
    zip_path = folder / "region_a.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("a.csv", "x,y\n1,2\n")

    dest = tmp_path / "bundle.zip"
    export_publication_zip_bundle(save_root, "2026_3", dest)
    assert dest.is_file()
    with zipfile.ZipFile(dest) as archive:
        names = archive.namelist()
    assert "region_a.zip" in names


def test_export_missing_folder(tmp_path: Path) -> None:
    with pytest.raises(ExportError):
        export_publication_zip_bundle(tmp_path, "2099_1", tmp_path / "out.zip")
