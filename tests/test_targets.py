"""Tests for region master."""

from pathlib import Path

import pytest

from jatic_library.core.targets import (
    TARGETS,
    Region,
    all_codes,
    all_targets,
    by_code,
    by_region,
    cache_is_fresh_for_folder,
    load_cache_meta,
    load_overrides,
    save_overrides,
    write_cache_meta,
)


def test_target_count() -> None:
    assert len(TARGETS) == 51
    orders = [t.order for t in TARGETS]
    assert orders == list(range(1, 52))
    assert len({t.code for t in TARGETS}) == 51


def test_by_code_tokyo() -> None:
    t = by_code("tokyo")
    assert t.display_name == "東京都"
    assert t.filename_key == "tokyo"


def test_by_code_invalid() -> None:
    with pytest.raises(KeyError):
        by_code("invalid")


def test_by_region_counts() -> None:
    assert len(by_region(Region.HOKKAIDO)) == 5
    assert len(by_region(Region.KANTO)) == 8
    assert len(by_region(Region.OKINAWA)) == 1
    total = sum(len(by_region(r)) for r in Region)
    assert total == 51


def test_all_helpers() -> None:
    assert len(all_targets()) == 51
    assert all_codes()[0] == "hokkaido_sapporo"
    assert len(all_codes()) == 51


def test_overrides_roundtrip(tmp_path: Path) -> None:
    from dataclasses import replace

    cache = tmp_path / "targets.json"
    assert load_overrides(cache) == TARGETS
    modified = [
        replace(t, filename_key="tokyo_custom") if t.code == "tokyo" else t for t in TARGETS
    ]
    save_overrides(modified, cache)
    loaded = load_overrides(cache)
    tokyo = next(t for t in loaded if t.code == "tokyo")
    assert tokyo.filename_key == "tokyo_custom"


def test_cache_meta_roundtrip(tmp_path: Path) -> None:
    cache = tmp_path / "targets.json"
    write_cache_meta(
        cache,
        publish_ym_compact="202606010928",
        scraped_for_folder="2026_4",
        scraped_at="2026-06-01T10:00:00+09:00",
    )
    meta = load_cache_meta(cache)
    assert meta.publish_ym_compact == "202606010928"
    assert meta.scraped_for_folder == "2026_4"
    assert cache_is_fresh_for_folder(meta, "2026_4")
    assert not cache_is_fresh_for_folder(meta, "2026_3")


def test_save_overrides_preserves_cache_meta(tmp_path: Path) -> None:
    cache = tmp_path / "targets.json"
    write_cache_meta(
        cache,
        publish_ym_compact="202606010928",
        scraped_for_folder="2026_4",
    )
    save_overrides(list(TARGETS), cache)
    meta = load_cache_meta(cache)
    assert meta.publish_ym_compact == "202606010928"
    assert meta.scraped_for_folder == "2026_4"
    tokyo = next(t for t in load_overrides(cache) if t.code == "tokyo")
    assert tokyo.filename_key == "tokyo"
