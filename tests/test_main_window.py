"""Tests for main window."""

from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from jatic_library.core.repository import Repository
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_tabs(qapp: QApplication, tmp_path) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    store = ConfigStore(tmp_path / "cfg.json")
    db = tmp_path / "test.db"
    with Repository(db) as repo:
        window = MainWindow(
            config,
            store,
            repo,
            run_startup_check=False,
        )
        assert window._tabs.count() == 2
        assert window._tabs.tabText(0) == "保管庫"
        assert window._tabs.tabText(1) == "設定"
        assert window.windowTitle().startswith("JATIC-Library")


@patch("jatic_library.app.run_app", return_value=0)
def test_entry_main_launches_gui(mock_run) -> None:
    from jatic_library.__main__ import main

    assert main([]) == 0
    mock_run.assert_called_once()
