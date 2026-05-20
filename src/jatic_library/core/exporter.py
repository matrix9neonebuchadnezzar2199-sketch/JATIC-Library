"""Export downloaded publications."""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path

import polars as pl

from jatic_library.core.csv_loader import CsvPreviewError, find_first_csv_name


class ExportError(Exception):
    """Raised when export fails."""


def export_publication_zip_bundle(
    save_root: Path,
    publish_ym: str,
    dest_zip: Path,
) -> Path:
    """Zip all region ZIP files for *publish_ym* into *dest_zip*."""
    folder = save_root / publish_ym
    if not folder.is_dir():
        raise ExportError(f"Publication folder not found: {folder}")
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for zip_path in sorted(folder.glob("*.zip")):
            archive.write(zip_path, arcname=zip_path.name)
    return dest_zip


def export_merged_csv(
    save_root: Path,
    publish_ym: str,
    dest_csv: Path,
    *,
    max_files: int = 51,
) -> Path:
    """Merge first CSV from each region ZIP into one CSV file."""
    folder = save_root / publish_ym
    if not folder.is_dir():
        raise ExportError(f"Publication folder not found: {folder}")

    frames: list[pl.DataFrame] = []
    for index, zip_path in enumerate(sorted(folder.glob("*.zip"))):
        if index >= max_files:
            break
        try:
            csv_name = find_first_csv_name(zip_path)
        except CsvPreviewError:
            continue
        with zipfile.ZipFile(zip_path) as archive:
            raw = archive.read(csv_name)
        for encoding in ("utf-8", "cp932"):
            try:
                frame = pl.read_csv(
                    raw,
                    encoding=encoding,
                    infer_schema_length=0,
                    ignore_errors=True,
                )
                frame = frame.with_columns(pl.lit(zip_path.stem).alias("_region"))
                frames.append(frame)
                break
            except Exception:  # noqa: S112 — try next encoding
                continue

    if not frames:
        raise ExportError("No CSV content found to merge")

    merged = pl.concat(frames, how="diagonal_relaxed")
    dest_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.write_csv(dest_csv)
    return dest_csv


def default_export_name(publish_ym: str, suffix: str) -> str:
    """Return a timestamped export filename."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"jatic_{publish_ym}_{stamp}.{suffix}"
