"""Build JARTIC open-data URLs from calendar rules."""

import re
from dataclasses import dataclass
from datetime import date

from jatic_library.constants import (
    JARTIC_DATA_DIR_TPL,
    JARTIC_ZIP_TPL,
    PUBLISH_LAG_MONTHS,
)

_FOLDER_RE = re.compile(r"^(\d{4})_(\d{1,2})$")


@dataclass(frozen=True)
class PublishInfo:
    """Resolved publication month and on-disk folder naming."""

    publish_year: int
    publish_month: int
    data_year: int
    data_month: int
    folder_name: str
    publish_ym_compact: str
    dir_url: str


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    return total // 12, total % 12 + 1


def compute_publish_info(today: date) -> PublishInfo:
    """Compute which dataset month JARTIC exposes on *today*."""
    publish_year, publish_month = today.year, today.month
    data_year, data_month = _shift_month(publish_year, publish_month, -PUBLISH_LAG_MONTHS)
    folder_name = f"{data_year}_{data_month}"
    publish_ym_compact = f"{publish_year}{publish_month:02d}010000"
    dir_url = JARTIC_DATA_DIR_TPL.format(publish_ym_compact=publish_ym_compact)
    return PublishInfo(
        publish_year=publish_year,
        publish_month=publish_month,
        data_year=data_year,
        data_month=data_month,
        folder_name=folder_name,
        publish_ym_compact=publish_ym_compact,
        dir_url=dir_url,
    )


def build_zip_url(info: PublishInfo, filename_key: str) -> str:
    """Return the typeB ZIP URL for a region key."""
    return JARTIC_ZIP_TPL.format(
        publish_ym_compact=info.publish_ym_compact,
        filename_key=filename_key,
    )


def build_doc_url(info: PublishInfo) -> str:
    """Return the typeB documentation PDF URL (estimated)."""
    return info.dir_url + "typeB_danmen.pdf"


def publish_info_from_folder(folder_name: str) -> PublishInfo:
    """Build ``PublishInfo`` for an on-disk ``YYYY_M`` data folder."""
    data_year, data_month = parse_folder_name(folder_name)
    publish_year, publish_month = _shift_month(data_year, data_month, PUBLISH_LAG_MONTHS)
    folder = folder_name
    publish_ym_compact = f"{publish_year}{publish_month:02d}010000"
    dir_url = JARTIC_DATA_DIR_TPL.format(publish_ym_compact=publish_ym_compact)
    return PublishInfo(
        publish_year=publish_year,
        publish_month=publish_month,
        data_year=data_year,
        data_month=data_month,
        folder_name=folder,
        publish_ym_compact=publish_ym_compact,
        dir_url=dir_url,
    )


def parse_folder_name(folder_name: str) -> tuple[int, int]:
    """Parse ``YYYY_M`` folder name into year and month."""
    match = _FOLDER_RE.match(folder_name)
    if not match:
        raise ValueError(f"Invalid folder name: {folder_name}")
    year = int(match.group(1))
    month = int(match.group(2))
    if month < 1 or month > 12:
        raise ValueError(f"Month out of range in folder name: {folder_name}")
    return year, month
