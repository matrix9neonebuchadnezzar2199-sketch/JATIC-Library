"""Scan on-disk publication folders into a library tree model."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from jatic_library.constants import MERGED_CSV_DISPLAY_NAME, MERGED_CSV_FILENAME
from jatic_library.core.csv_loader import count_data_rows_for_path, uncompressed_csv_size_in_zip
from jatic_library.core.library_scan_cache import get_cached_stats
from jatic_library.core.manifest import Manifest, ManifestFileEntry
from jatic_library.core.models import FileRow
from jatic_library.core.repository import Repository
from jatic_library.core.url_builder import parse_folder_name

_FOLDER_RE = re.compile(r"^(\d{4})_(\d{1,2})$")


def format_library_file_label(
    display_name: str,
    file_size: int,
    row_count: int | None,
) -> str:
    """Build tree label with row count and uncompressed-equivalent size in GB."""
    rows = f"{row_count:,}行" if row_count is not None else "—行"
    size_gb = file_size / (1024**3)
    return f"{display_name}  {rows}  {size_gb:.2f}GB"


def compute_file_stats(path: Path) -> tuple[int | None, int]:
    """Compute row count and display size (uncompressed CSV size when ZIP)."""
    try:
        zip_size = path.stat().st_size
    except OSError:
        zip_size = 0
    row_count = count_data_rows_for_path(path)
    if path.suffix.lower() == ".zip":
        display_size = uncompressed_csv_size_in_zip(path) or zip_size
    else:
        display_size = zip_size
    return row_count, display_size


def _stats_for_path(path: Path) -> tuple[int, int | None]:
    """Return (display_size, row_count) using cache when possible."""
    try:
        zip_size = path.stat().st_size
    except OSError:
        return 0, None

    cached = get_cached_stats(path)
    if cached is not None:
        display_size = cached.uncompressed_csv_size if cached.uncompressed_csv_size else zip_size
        return display_size, cached.row_count

    # Cache miss: show placeholder size only; row count filled asynchronously in UI.
    return zip_size, None


@dataclass(frozen=True)
class LibraryFileItem:
    """One ZIP file on disk with optional DB/manifest metadata."""

    publish_ym: str
    file_name: str
    file_path: Path
    display_name: str
    target_code: str | None
    file_size: int
    sha256: str | None
    source_url: str | None
    downloaded_at: str | None
    status: str | None = None
    row_count: int | None = None


@dataclass
class LibraryMonthItem:
    """One publication month folder."""

    folder_name: str
    year: int
    month: int
    publication_status: str | None
    files: list[LibraryFileItem] = field(default_factory=list)


@dataclass
class LibraryYearItem:
    """Months grouped by data year."""

    year: int
    months: list[LibraryMonthItem] = field(default_factory=list)


def _merge_file(
    publish_ym: str,
    zip_path: Path,
    manifest_entry: ManifestFileEntry | None,
    db_row: FileRow | None,
) -> LibraryFileItem:
    display = zip_path.stem
    if manifest_entry is not None:
        display = manifest_entry.display_name
    elif db_row is not None:
        display = db_row.display_name

    target_code = None
    sha256 = None
    source_url = None
    downloaded_at = None
    if manifest_entry is not None:
        target_code = manifest_entry.target_code
        sha256 = manifest_entry.sha256
        source_url = manifest_entry.source_url
        downloaded_at = manifest_entry.downloaded_at
    elif db_row is not None:
        target_code = db_row.target_code
        sha256 = db_row.sha256
        source_url = db_row.source_url
        downloaded_at = db_row.downloaded_at

    display_size, row_count = _stats_for_path(zip_path)
    return LibraryFileItem(
        publish_ym=publish_ym,
        file_name=zip_path.name,
        file_path=zip_path,
        display_name=display,
        target_code=target_code,
        file_size=display_size,
        sha256=sha256,
        source_url=source_url,
        downloaded_at=downloaded_at,
        status=db_row.status if db_row is not None else None,
        row_count=row_count,
    )


def _scan_month_folder(
    folder: Path,
    folder_name: str,
    repo: Repository | None,
) -> LibraryMonthItem:
    year, month = parse_folder_name(folder_name)
    manifest = Manifest.load(folder)
    manifest_by_name = {entry.filename: entry for entry in manifest.files} if manifest else {}
    db_by_name: dict[str, FileRow] = {}
    if repo is not None:
        for row in repo.list_files_by_publication(folder_name):
            db_by_name[Path(row.file_path).name] = row

    pub_status: str | None = None
    if repo is not None:
        pub = repo.get_publication(folder_name)
        pub_status = pub.status if pub else None

    files: list[LibraryFileItem] = []
    merged_csv = folder / MERGED_CSV_FILENAME
    if merged_csv.is_file():
        display_size, row_count = _stats_for_path(merged_csv)
        files.append(
            LibraryFileItem(
                publish_ym=folder_name,
                file_name=merged_csv.name,
                file_path=merged_csv,
                display_name=MERGED_CSV_DISPLAY_NAME,
                target_code="merged",
                file_size=display_size,
                sha256=None,
                source_url=None,
                downloaded_at=None,
                status=None,
                row_count=row_count,
            )
        )

    for zip_path in sorted(folder.glob("*.zip"), key=lambda p: p.name):
        manifest_entry = manifest_by_name.get(zip_path.name)
        db_row = db_by_name.get(zip_path.name)
        files.append(_merge_file(folder_name, zip_path, manifest_entry, db_row))

    return LibraryMonthItem(
        folder_name=folder_name,
        year=year,
        month=month,
        publication_status=pub_status,
        files=files,
    )


def scan_library(
    save_root: Path | None,
    repo: Repository | None = None,
    *,
    sort: str = "date_desc",
) -> list[LibraryYearItem]:
    """Build year → month → file tree from *save_root*."""
    if save_root is None or not save_root.is_dir():
        return []

    months: list[LibraryMonthItem] = []
    for child in save_root.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        if not _FOLDER_RE.match(child.name):
            continue
        try:
            months.append(_scan_month_folder(child, child.name, repo))
        except (OSError, ValueError):
            continue

    reverse = sort != "date_asc"
    months.sort(key=lambda m: (m.year, m.month), reverse=reverse)
    if sort == "name":
        for month in months:
            month.files.sort(key=lambda f: f.display_name)
    years_map: dict[int, LibraryYearItem] = {}
    for month in months:
        if month.year not in years_map:
            years_map[month.year] = LibraryYearItem(year=month.year)
        years_map[month.year].months.append(month)

    return sorted(years_map.values(), key=lambda y: y.year, reverse=True)


def iter_files_needing_stats(tree: list[LibraryYearItem]) -> list[LibraryFileItem]:
    """Return file items whose row_count was not loaded from cache."""
    pending: list[LibraryFileItem] = []
    for year in tree:
        for month in year.months:
            for file_item in month.files:
                if file_item.row_count is None:
                    pending.append(file_item)
    return pending


def update_file_item_in_tree(
    tree: list[LibraryYearItem],
    path: Path,
    *,
    row_count: int | None,
    file_size: int,
) -> LibraryFileItem | None:
    """Replace the matching ``LibraryFileItem`` in *tree* and return the new item."""
    for year in tree:
        for month in year.months:
            for index, file_item in enumerate(month.files):
                if file_item.file_path.resolve() == path.resolve():
                    updated = replace(
                        file_item,
                        row_count=row_count,
                        file_size=file_size,
                    )
                    month.files[index] = updated
                    return updated
    return None
