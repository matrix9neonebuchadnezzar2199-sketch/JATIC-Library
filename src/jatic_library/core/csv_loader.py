"""Load and merge CSV data from ZIP archives."""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path
from typing import IO

import polars as pl

from jatic_library.constants import MERGED_CSV_ENCODING

# JARTIC region ZIP CSVs are typically cp932; try these before UTF-8.
_SOURCE_CSV_ENCODINGS = ("cp932", "shift_jis", "utf-8")


class CsvLoadError(Exception):
    """Raised when CSV data cannot be read from an archive."""


def _count_newlines_in_binary_stream(stream: IO[bytes]) -> int:
    """Count newline bytes while streaming."""
    total = 0
    while chunk := stream.read(1024 * 1024):
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
    for encoding in _SOURCE_CSV_ENCODINGS:
        try:
            return pl.read_csv(
                io.BytesIO(raw),
                encoding=encoding,
                infer_schema_length=0,
            )
        except (UnicodeDecodeError, pl.exceptions.ComputeError) as exc:
            last_error = exc
    raise CsvLoadError(str(last_error or "Could not decode CSV"))


def _transcode_utf8_csv_file(src: Path, dest: Path, encoding: str) -> None:
    """Rewrite a UTF-8 CSV file produced by Polars as *encoding*."""
    dest.write_bytes(src.read_text(encoding="utf-8").encode(encoding))


def read_csv_frame_from_zip(zip_path: Path) -> pl.DataFrame:
    """Read the first CSV member inside *zip_path*."""
    csv_name = find_first_csv_name(zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        raw = archive.read(csv_name)
    return read_csv_frame_from_bytes(raw)


def merge_region_zip_csvs(zip_paths: list[Path]) -> pl.DataFrame:
    """Concatenate the first CSV from each ZIP (one header row, all data)."""
    if not zip_paths:
        raise CsvLoadError("No CSV content to merge")
    frames = [read_csv_frame_from_zip(path) for path in zip_paths]
    return pl.concat(frames, how="vertical_relaxed")


def merge_region_zip_csvs_to_path(
    zip_paths: list[Path],
    dest_path: Path,
    *,
    temp_dir: Path | None = None,
) -> None:
    """Merge ZIP CSVs into *dest_path* with bounded peak memory.

    Each ZIP is decoded with cp932-first detection, combined via LazyFrame
    ``sink_csv`` (UTF-8 intermediate), then written to *dest_path* as Shift_JIS
    (``MERGED_CSV_ENCODING``). Temp files live under *temp_dir* when set
    (use publication folder to avoid filling the system temp drive).
    """
    if not zip_paths:
        raise CsvLoadError("No CSV content to merge")

    parent = temp_dir if temp_dir is not None else dest_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=parent) as tmp_name:
        tmp = Path(tmp_name)
        lazy_frames: list[pl.LazyFrame] = []
        column_names: list[str] | None = None
        for index, zip_path in enumerate(zip_paths):
            frame = read_csv_frame_from_zip(zip_path)
            if frame.height == 0:
                continue
            if column_names is None:
                column_names = list(frame.columns)
            part_path = tmp / f"part_{index:04d}.csv"
            if index == 0:
                frame.write_csv(part_path)
                lazy_frames.append(pl.scan_csv(part_path, infer_schema_length=0))
            else:
                frame.write_csv(part_path, include_header=False)
                lazy_frames.append(
                    pl.scan_csv(
                        part_path,
                        has_header=False,
                        new_columns=column_names,
                        infer_schema_length=0,
                    )
                )

        if not lazy_frames:
            raise CsvLoadError("No CSV content to merge")

        utf8_dest = tmp / "merged_utf8.csv"
        pl.concat(lazy_frames, how="vertical_relaxed").sink_csv(utf8_dest)
        _transcode_utf8_csv_file(utf8_dest, dest_path, MERGED_CSV_ENCODING)


def find_first_csv_name(zip_path: Path) -> str:
    """Return the first ``.csv`` member name inside *zip_path*."""
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".csv") and not name.endswith("/"):
                return name
    raise CsvLoadError(f"No CSV file in archive: {zip_path.name}")
