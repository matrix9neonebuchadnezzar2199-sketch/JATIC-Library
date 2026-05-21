"""Export downloaded publications."""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path

from jatic_library.core.csv_loader import CsvLoadError, merge_region_zip_csvs


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

    zip_paths = sorted(folder.glob("*.zip"))[:max_files]
    try:
        merged = merge_region_zip_csvs(zip_paths)
    except CsvLoadError as exc:
        raise ExportError(str(exc)) from exc

    dest_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.write_csv(dest_csv)
    return dest_csv


def default_export_name(publish_ym: str, suffix: str) -> str:
    """Return a timestamped export filename."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"jatic_{publish_ym}_{stamp}.{suffix}"
