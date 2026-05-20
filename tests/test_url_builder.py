"""Tests for publish URL logic."""

from datetime import date

import pytest

from jatic_library.core.url_builder import (
    build_zip_url,
    compute_publish_info,
    parse_folder_name,
    publish_info_from_folder,
)

_PUBLISH_CASES = [
    (date(2026, 5, 15), 2026, 5, 2026, 3, "2026_3"),
    (date(2026, 5, 1), 2026, 5, 2026, 3, "2026_3"),
    (date(2026, 5, 31), 2026, 5, 2026, 3, "2026_3"),
    (date(2026, 1, 1), 2026, 1, 2025, 11, "2025_11"),
    (date(2026, 2, 15), 2026, 2, 2025, 12, "2025_12"),
    (date(2026, 3, 1), 2026, 3, 2026, 1, "2026_1"),
    (date(2026, 12, 31), 2026, 12, 2026, 10, "2026_10"),
]


@pytest.mark.parametrize(
    ("today", "pub_y", "pub_m", "data_y", "data_m", "folder"),
    _PUBLISH_CASES,
)
def test_compute_publish_info(
    today: date,
    pub_y: int,
    pub_m: int,
    data_y: int,
    data_m: int,
    folder: str,
) -> None:
    info = compute_publish_info(today)
    assert info.publish_year == pub_y
    assert info.publish_month == pub_m
    assert info.data_year == data_y
    assert info.data_month == data_m
    assert info.folder_name == folder
    assert info.publish_ym_compact == f"{pub_y}{pub_m:02d}010000"


def test_build_zip_url() -> None:
    info = compute_publish_info(date(2026, 5, 15))
    url = build_zip_url(info, "tokyo")
    assert url == "https://www.jartic.or.jp/d/opendata/202605010000/typeB_tokyo.zip"


@pytest.mark.parametrize(
    ("folder", "expected"),
    [("2026_3", (2026, 3)), ("2025_12", (2025, 12))],
)
def test_parse_folder_name_ok(folder: str, expected: tuple[int, int]) -> None:
    assert parse_folder_name(folder) == expected


@pytest.mark.parametrize("folder", ["invalid", "2026_13", ""])
def test_parse_folder_name_invalid(folder: str) -> None:
    with pytest.raises(ValueError):
        parse_folder_name(folder)


def test_publish_info_from_folder() -> None:
    info = publish_info_from_folder("2026_3")
    assert info.folder_name == "2026_3"
    assert info.data_year == 2026
    assert info.data_month == 3
    assert info.publish_year == 2026
    assert info.publish_month == 5
