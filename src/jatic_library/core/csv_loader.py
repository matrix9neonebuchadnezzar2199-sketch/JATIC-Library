"""Load CSV snippets from ZIP archives for preview."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import polars as pl


class CsvPreviewError(Exception):
    """Raised when CSV preview cannot be produced."""


def find_first_csv_name(zip_path: Path) -> str:
    """Return the first ``.csv`` member name inside *zip_path*."""
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".csv") and not name.endswith("/"):
                return name
    raise CsvPreviewError(f"No CSV file in archive: {zip_path.name}")


def preview_csv_from_zip(
    zip_path: Path,
    *,
    max_rows: int = 1000,
) -> tuple[list[str], list[list[str]]]:
    """Read up to *max_rows* from the first CSV in *zip_path*.

    Returns:
        Column names and row values as strings for table display.
    """
    if not zip_path.is_file():
        raise CsvPreviewError(f"File not found: {zip_path}")

    csv_name = find_first_csv_name(zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        raw = archive.read(csv_name)

    frame: pl.DataFrame | None = None
    last_error: Exception | None = None
    for encoding in ("utf-8", "cp932", "shift_jis"):
        try:
            frame = pl.read_csv(
                io.BytesIO(raw),
                n_rows=max_rows,
                encoding=encoding,
                infer_schema_length=0,
                ignore_errors=True,
            )
            break
        except Exception as exc:
            last_error = exc

    if frame is None:
        raise CsvPreviewError(str(last_error or "Could not decode CSV"))

    headers = [str(column) for column in frame.columns]
    rows = [[str(value) for value in row] for row in frame.iter_rows()]
    return headers, rows
