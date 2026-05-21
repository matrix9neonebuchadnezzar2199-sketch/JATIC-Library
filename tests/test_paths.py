"""Tests for default save path resolution."""

from __future__ import annotations

from pathlib import Path

from jatic_library.paths import default_save_root, normalize_save_root


def test_default_save_root_is_app_adjacent() -> None:
    root = default_save_root()
    assert root.name == "data"
    assert root.parent.is_dir()


def test_normalize_none_uses_default() -> None:
    assert normalize_save_root(None) == default_save_root()


def test_normalize_keeps_custom_path(tmp_path: Path) -> None:
    custom = tmp_path / "my_jartic_data"
    assert normalize_save_root(custom) == custom
