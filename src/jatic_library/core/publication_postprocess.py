"""Extract region ZIPs and build a merged CSV after download."""

from __future__ import annotations

import shutil
import zipfile
from collections.abc import Callable
from pathlib import Path

from loguru import logger

from jatic_library.constants import EXTRACTED_DIR_NAME, MERGED_CSV_FILENAME
from jatic_library.core.csv_loader import CsvLoadError, merge_region_zip_csvs_to_path
from jatic_library.core.targets import Target

POSTPROCESS_EXTRACT_CODE = "__extract__"
POSTPROCESS_MERGE_CODE = "__merge__"


class PostprocessError(Exception):
    """Raised when post-download artifact generation fails."""


def region_zip_paths(folder: Path, targets: list[Target]) -> list[Path]:
    """Return on-disk region ZIP paths for *targets* in *folder*."""
    paths: list[Path] = []
    for target in targets:
        zip_path = folder / f"{target.folder_label}.zip"
        if zip_path.is_file():
            paths.append(zip_path)
    return sorted(paths, key=lambda path: path.name)


def extract_region_zips(
    zip_paths: list[Path],
    extract_root: Path,
    progress_cb: Callable[[str, int, int, str], None] | None = None,
) -> None:
    """Extract each region ZIP under *extract_root* / ``<zip_stem>/``."""
    extract_root.mkdir(parents=True, exist_ok=True)
    total = len(zip_paths)
    for index, zip_path in enumerate(zip_paths, start=1):
        dest = extract_root / zip_path.stem
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(dest)
        if progress_cb is not None:
            progress_cb(
                POSTPROCESS_EXTRACT_CODE,
                index,
                total,
                f"解凍中: {zip_path.stem}",
            )


def write_merged_csv(zip_paths: list[Path], dest_csv: Path) -> None:
    """Merge the first CSV in each ZIP (header once, all data rows)."""
    if not zip_paths:
        raise PostprocessError("No region ZIP files to merge")
    dest_csv.parent.mkdir(parents=True, exist_ok=True)
    try:
        merge_region_zip_csvs_to_path(zip_paths, dest_csv, temp_dir=dest_csv.parent)
    except CsvLoadError as exc:
        raise PostprocessError(str(exc)) from exc


def postprocess_publication_folder(
    folder: Path,
    targets: list[Target],
    progress_cb: Callable[[str, int, int, str], None] | None = None,
) -> Path | None:
    """Extract selected region ZIPs and rebuild ``統合.csv``.

    Returns the merged CSV path when created, else ``None``.
    """
    zip_paths = region_zip_paths(folder, targets)
    if not zip_paths:
        logger.info("Post-process skipped: no region ZIPs in {}", folder)
        return None

    extract_root = folder / EXTRACTED_DIR_NAME
    try:
        extract_region_zips(zip_paths, extract_root, progress_cb)
        if progress_cb is not None:
            progress_cb(POSTPROCESS_MERGE_CODE, 0, 1, "CSV結合中…")
        merged_path = folder / MERGED_CSV_FILENAME
        write_merged_csv(zip_paths, merged_path)
        if progress_cb is not None:
            progress_cb(POSTPROCESS_MERGE_CODE, 1, 1, "CSV結合完了")
    except (OSError, PostprocessError, zipfile.BadZipFile) as exc:
        logger.warning("Post-process failed for {}: {}", folder, exc)
        raise PostprocessError(str(exc)) from exc

    logger.info(
        "Post-process complete: {} ZIP(s) extracted, merged CSV {}",
        len(zip_paths),
        merged_path.name,
    )
    return merged_path
