"""Tests for SettingsTab dirty-state indicator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from jatic_library import __app_name__, __version__
from jatic_library.core.repository import Repository
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.main_window import MainWindow
from jatic_library.ui.tabs.settings_tab import SettingsTab


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def settings_tab(qapp: QApplication, tmp_path: Path) -> SettingsTab:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    store = ConfigStore(tmp_path / "config.json")
    return SettingsTab(config, store)


def test_initial_state_clean(settings_tab: SettingsTab) -> None:
    assert settings_tab.is_dirty is False
    assert not settings_tab._save_button.isEnabled()


def test_region_change_marks_dirty(settings_tab: SettingsTab) -> None:
    spy = QSignalSpy(settings_tab.dirty_changed)

    settings_tab._region_selector.clear_all()

    assert settings_tab.is_dirty is True
    assert settings_tab._save_button.isEnabled()
    assert spy.count() >= 1
    assert spy.at(spy.count() - 1)[0] is True


@patch("jatic_library.ui.tabs.settings_tab.QMessageBox.information")
def test_save_clears_dirty(_info, settings_tab: SettingsTab) -> None:
    spy = QSignalSpy(settings_tab.dirty_changed)
    settings_tab._concurrency.setValue(settings_tab._concurrency.value() + 1)

    settings_tab.save_to_store()

    assert settings_tab.is_dirty is False
    assert not settings_tab._save_button.isEnabled()
    assert any(spy.at(index)[0] is False for index in range(spy.count()))


def test_load_from_config_does_not_mark_dirty(settings_tab: SettingsTab) -> None:
    settings_tab._concurrency.setValue(settings_tab._concurrency.value() + 1)
    assert settings_tab.is_dirty is True

    settings_tab.load_from_config()

    assert settings_tab.is_dirty is False
    assert not settings_tab._save_button.isEnabled()


def test_run_update_check_blocked_when_dirty(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.download.save_root.mkdir(parents=True, exist_ok=True)
    store = ConfigStore(tmp_path / "cfg.json")
    repo = Repository(tmp_path / "db")
    repo.connect()
    window = MainWindow(config, store, repo, run_startup_check=False)
    window._settings_tab._concurrency.setValue(window._settings_tab._concurrency.value() + 1)

    with (
        patch.object(window, "_warn_playwright_chromium_missing", return_value=False),
        patch("jatic_library.ui.main_window.QMessageBox.warning"),
        patch("jatic_library.ui.main_window.DownloadProgressDialog") as mock_dialog,
        patch("jatic_library.ui.main_window.AsyncTaskWorker") as mock_worker,
    ):
        window.run_update_check(force=True)

    mock_dialog.assert_not_called()
    mock_worker.assert_not_called()
    assert window._tabs.currentWidget() is window._settings_tab
    repo.close()


def test_main_window_title_shows_asterisk_when_dirty(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    store = ConfigStore(tmp_path / "cfg.json")
    repo = Repository(tmp_path / "db")
    repo.connect()
    window = MainWindow(config, store, repo, run_startup_check=False)
    base = f"{__app_name__} v{__version__}"

    assert window.windowTitle() == base
    window._settings_tab._retry.setValue(window._settings_tab._retry.value() + 1)
    assert window.windowTitle() == f"{base} *"
    repo.close()
