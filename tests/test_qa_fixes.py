"""Regression tests for QA review fixes (2026-05-22)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from jatic_library.core.repository import Repository
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.main_window import MainWindow
from jatic_library.ui.tabs.library_tab import LibraryTab


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_patch_library_sort_preserves_other_fields(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "download": {"save_root": str(tmp_path / "saved"), "concurrency": 7},
                "ui": {"library_default_sort": "date_desc", "theme": "light"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    store = ConfigStore(path)
    store.patch_library_sort("name")

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["ui"]["library_default_sort"] == "name"
    assert raw["download"]["concurrency"] == 7


def test_sort_changed_uses_patch_when_settings_dirty(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.download.save_root.mkdir(parents=True, exist_ok=True)
    config.ui.library_default_sort = "date_desc"
    store = ConfigStore(tmp_path / "cfg.json")
    store.save(config)
    repo = Repository(tmp_path / "db")
    repo.connect()
    window = MainWindow(config, store, repo, run_startup_check=False)
    window._settings_tab._concurrency.setValue(window._settings_tab._concurrency.value() + 1)
    assert window._settings_tab.is_dirty is True

    with (
        patch.object(store, "save") as mock_save,
        patch.object(store, "patch_library_sort") as mock_patch,
    ):
        window._on_library_sort_changed("name")

    mock_patch.assert_called_once_with("name")
    mock_save.assert_not_called()
    repo.close()


def test_theme_menu_does_not_reload_settings_when_dirty(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    store = ConfigStore(tmp_path / "cfg.json")
    repo = Repository(tmp_path / "db")
    repo.connect()
    window = MainWindow(config, store, repo, run_startup_check=False)
    window._settings_tab._retry.setValue(window._settings_tab._retry.value() + 1)

    with patch.object(window._settings_tab, "load_from_config") as mock_load:
        window._set_theme("dark")

    mock_load.assert_not_called()
    assert window._settings_tab.is_dirty is True
    assert window._config.ui.theme == "dark"
    repo.close()


def test_export_month_has_separate_signals(qapp: QApplication, tmp_path: Path) -> None:
    save_root = tmp_path / "data"
    save_root.mkdir(parents=True, exist_ok=True)
    config = AppConfig.default()
    config.download.save_root = save_root
    db = tmp_path / "export.db"
    repo = Repository(db)
    repo.connect()
    tab = LibraryTab(config, repo)
    zip_spy = QSignalSpy(tab.export_month_zip_requested)
    csv_spy = QSignalSpy(tab.export_month_csv_requested)
    tab.export_month_zip_requested.emit("2026_3")
    tab.export_month_csv_requested.emit("2026_3")
    assert zip_spy.count() == 1
    assert csv_spy.count() == 1
    repo.close()


def _index_for_key(tab: LibraryTab, sort_key: str) -> int:
    for index in range(tab._sort.count()):
        if tab._sort.itemData(index) == sort_key:
            return index
    raise AssertionError(f"sort key not found: {sort_key}")


def test_sort_integration_patch_on_disk_when_dirty(
    qapp: QApplication,
    tmp_path: Path,
) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.download.save_root.mkdir(parents=True, exist_ok=True)
    config.download.concurrency = 3
    config.ui.library_default_sort = "date_desc"
    cfg_path = tmp_path / "cfg.json"
    store = ConfigStore(cfg_path)
    store.save(config)
    repo = Repository(tmp_path / "db")
    repo.connect()
    window = MainWindow(config, store, repo, run_startup_check=False)
    window._settings_tab._concurrency.setValue(9)

    window._library_tab._sort.setCurrentIndex(_index_for_key(window._library_tab, "name"))
    QTest.qWait(400)

    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert raw["ui"]["library_default_sort"] == "name"
    assert raw["download"]["concurrency"] == 3
    repo.close()
