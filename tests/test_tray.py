"""Tests for system tray controller."""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from jatic_library.core.tray import TrayController
from jatic_library.settings.config import TraySettings


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_setup_disabled_returns_false(qapp: QApplication) -> None:
    calls: list[str] = []
    tray = TrayController(
        TraySettings(enable_tray=False),
        on_check_now=lambda: calls.append("check"),
        on_show_window=lambda: calls.append("show"),
        on_quit=lambda: calls.append("quit"),
    )
    assert tray.setup() is False
    assert tray.is_active() is False


def test_setup_active_when_available(qapp: QApplication) -> None:
    calls: list[str] = []
    tray = TrayController(
        TraySettings(enable_tray=True),
        on_check_now=lambda: calls.append("check"),
        on_show_window=lambda: calls.append("show"),
        on_quit=lambda: calls.append("quit"),
    )
    mock_icon = MagicMock()
    with (
        patch(
            "jatic_library.core.tray.QSystemTrayIcon.isSystemTrayAvailable",
            return_value=True,
        ),
        patch("jatic_library.core.tray.QSystemTrayIcon", return_value=mock_icon),
    ):
        assert tray.setup() is True
        assert tray.is_active() is True
        tray.teardown()
    assert tray.is_active() is False
    mock_icon.show.assert_called_once()


def test_close_to_tray_requires_active_tray(qapp: QApplication, tmp_path) -> None:
    from jatic_library.core.repository import Repository
    from jatic_library.settings.config import AppConfig
    from jatic_library.settings.store import ConfigStore
    from jatic_library.ui.main_window import MainWindow

    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.tray.enable_tray = True
    config.tray.minimize_to_tray = True
    store = ConfigStore(tmp_path / "cfg.json")
    db = tmp_path / "mw.db"
    with Repository(db) as repo:
        window = MainWindow(config, store, repo, run_startup_check=False)
        window._tray._tray = None
        from PySide6.QtGui import QCloseEvent

        event = QCloseEvent()
        window.closeEvent(event)
        assert event.isAccepted()
        assert not window.isVisible()
