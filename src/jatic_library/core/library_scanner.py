"""Scan on-disk publication folders into a library tree model."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from jatic_library.core.manifest import Manifest, ManifestFileEntry
from jatic_library.core.models import FileRow
from jatic_library.core.repository import Repository
from jatic_library.core.url_builder import parse_folder_name

_FOLDER_RE = re.compile(r"^(\d{4})_(\d{1,2})$")


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
    status: str | None


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

    size = zip_path.stat().st_size
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

    return LibraryFileItem(
        publish_ym=publish_ym,
        file_name=zip_path.name,
        file_path=zip_path,
        display_name=display,
        target_code=target_code,
        file_size=db_row.file_size if db_row is not None else size,
        sha256=sha256,
        source_url=source_url,
        downloaded_at=downloaded_at,
        status=db_row.status if db_row is not None else None,
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
