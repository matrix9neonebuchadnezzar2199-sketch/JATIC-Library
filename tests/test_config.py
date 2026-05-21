"""Tests for Pydantic configuration models."""

import warnings
from pathlib import Path

import pytest
from pydantic import ValidationError

from jatic_library.settings.config import (
    AppConfig,
    DownloadSettings,
    GitHubSettings,
    TargetSelection,
    UISettings,
)


def test_default_config() -> None:
    cfg = AppConfig.default()
    assert cfg.download.save_root is not None
    assert cfg.download.save_root.name == "data"
    assert cfg.is_initial_setup_needed() is False


def test_initial_setup_with_save_root() -> None:
    cfg = AppConfig.default()
    cfg.download.save_root = Path("F:/JATIC_data")
    assert cfg.is_initial_setup_needed() is False


def test_download_concurrency_bounds() -> None:
    with pytest.raises(ValidationError):
        DownloadSettings(concurrency=0)
    with pytest.raises(ValidationError):
        DownloadSettings(concurrency=11)


def test_target_selection_filters_invalid_codes() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        sel = TargetSelection(selected_codes={"tokyo", "not_a_region"})
    assert sel.selected_codes == {"tokyo"}
    assert any("Unknown target codes" in str(w.message) for w in caught)


def test_target_selection_keeps_valid() -> None:
    sel = TargetSelection(selected_codes={"tokyo", "osaka"})
    assert sel.selected_codes == {"tokyo", "osaka"}


def test_ui_theme_validation() -> None:
    with pytest.raises(ValidationError):
        UISettings(theme="invalid")  # type: ignore[arg-type]


def test_github_commit_unit_validation() -> None:
    with pytest.raises(ValidationError):
        GitHubSettings(commit_unit="invalid")  # type: ignore[arg-type]
