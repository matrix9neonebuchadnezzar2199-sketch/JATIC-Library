"""Load and merge CSV data from ZIP archives."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import polars as pl


class CsvLoadError(Exception):
    """Raised when CSV data cannot be read from an archive."""


def _count_newlines_in_binary_stream(stream: zipfile.ZipExtFile | object) -> int:
    """Count newline bytes while streaming."""
    total = 0
    while chunk := stream.read(1024 * 1024):  # type: ignore[union-attr]
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        total += chunk.count(b"\n")
    return total


def count_data_rows_in_file(path: Path) -> int | None:
    """Count CSV data rows in a plain file (header excluded)."""
    if not path.is_file():
        return None
    try:
        with path.open("rb") as handle:
            line_count = _count_newlines_in_binary_stream(handle)
        return max(0, line_count - 1)
    except OSError:
        return None


def uncompressed_csv_size_in_zip(zip_path: Path) -> int | None:
    """Return uncompressed size of the first CSV member inside *zip_path*."""
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for name in archive.namelist():
                if name.lower().endswith(".csv") and not name.endswith("/"):
                    return archive.getinfo(name).file_size
    except (OSError, zipfile.BadZipFile):
        return None
    return None


def count_data_rows_in_zip(zip_path: Path) -> int | None:
    """Count data rows in the first CSV member of *zip_path*."""
    try:
        csv_name = find_first_csv_name(zip_path)
        with zipfile.ZipFile(zip_path) as archive, archive.open(csv_name) as member:
            line_count = _count_newlines_in_binary_stream(member)
        return max(0, line_count - 1)
    except (OSError, CsvLoadError, zipfile.BadZipFile, KeyError):
        return None


def count_data_rows_for_path(path: Path) -> int | None:
    """Return data row count for a library file path."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return count_data_rows_in_file(path)
    if suffix == ".zip":
        return count_data_rows_in_zip(path)
    return None


def read_csv_frame_from_bytes(raw: bytes) -> pl.DataFrame:
    """Decode *raw* CSV bytes into a DataFrame."""
    last_error: Exception | None = None
    for encoding in ("utf-8", "cp932", "shift_jis"):
        try:
            return pl.read_csv(
                io.BytesIO(raw),
                encoding=encoding,
                infer_schema_length=0,
                ignore_errors=True,
            )
        except Exception as exc:
            last_error = exc
    raise CsvLoadError(str(last_error or "Could not decode CSV"))


def read_csv_frame_from_zip(zip_path: Path) -> pl.DataFrame:
    """Read the first CSV member inside *zip_path*."""
    csv_name = find_first_csv_name(zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        raw = archive.read(csv_name)
    return read_csv_frame_from_bytes(raw)


def merge_region_zip_csvs(zip_paths: list[Path]) -> pl.DataFrame:
    """Concatenate the first CSV from each ZIP (one header row, all data)."""
    frames = [read_csv_frame_from_zip(path) for path in zip_paths]
    if not frames:
        raise CsvLoadError("No CSV content to merge")
    return pl.concat(frames, how="vertical_relaxed")


def find_first_csv_name(zip_path: Path) -> str:
    """Return the first ``.csv`` member name inside *zip_path*."""
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".csv") and not name.endswith("/"):
                return name
    raise CsvLoadError(f"No CSV file in archive: {zip_path.name}")
