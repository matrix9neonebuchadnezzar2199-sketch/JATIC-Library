"""Tests for settings tab."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.tabs.settings_tab import SettingsTab
from jatic_library.ui.widgets.region_selector import RegionSelector


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_region_selector_all_codes(qapp: QApplication) -> None:
    widget = RegionSelector()
    widget.select_all()
    assert len(widget.selected_codes()) == 51


def test_region_selector_empty_means_all_on_load(qapp: QApplication) -> None:
    widget = RegionSelector()
    widget.set_selected_codes(set())
    assert len(widget.selected_codes()) == 51


@patch("jatic_library.ui.tabs.settings_tab.QMessageBox.information")
@patch("jatic_library.ui.tabs.settings_tab.QMessageBox.warning")
def test_settings_save_roundtrip(
    _warn,
    _info,
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.download.concurrency = 2
    store = ConfigStore(tmp_path / "config.json")
    tab = SettingsTab(config, store)
    tab._concurrency.setValue(4)
    tab.save_to_store()
    loaded = store.load()
    assert loaded.download.concurrency == 4
    assert loaded.download.save_root == tmp_path / "data"
