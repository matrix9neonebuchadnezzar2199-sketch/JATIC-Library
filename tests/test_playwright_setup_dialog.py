"""Tests for Playwright Chromium setup dialog and install helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from jatic_library.core.playwright_env import _resolve_install_command
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.main_window import MainWindow
from jatic_library.ui.widgets.playwright_setup_dialog import PlaywrightSetupDialog


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp: QApplication, tmp_path: Path) -> MainWindow:
    from jatic_library.core.repository import Repository

    db = tmp_path / "test.db"
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.download.save_root.mkdir(parents=True, exist_ok=True)
    store = ConfigStore(tmp_path / "cfg.json")
    repo = Repository(db)
    repo.connect()
    window = MainWindow(config, store, repo, run_startup_check=False)
    yield window
    repo.close()


def test_resolve_install_command_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    cmd, env = _resolve_install_command()
    assert cmd == [sys.executable, "-m", "playwright", "install", "chromium"]
    assert env is None


def test_resolve_install_command_frozen_uses_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        "playwright._impl._driver.compute_driver_executable",
        lambda: ("/fake/node.exe", "/fake/cli.js"),
    )
    monkeypatch.setattr(
        "playwright._impl._driver.get_driver_env",
        lambda: {"DUMMY": "1"},
    )
    cmd, env = _resolve_install_command()
    assert cmd == ["/fake/node.exe", "/fake/cli.js", "install", "chromium"]
    assert env == {"DUMMY": "1"}


def test_warn_returns_false_when_chromium_ready(main_window: MainWindow) -> None:
    with patch("jatic_library.ui.main_window.chromium_is_ready", return_value=True):
        assert main_window._warn_playwright_chromium_missing() is False


def test_warn_shows_setup_dialog_when_chromium_missing(main_window: MainWindow) -> None:
    exec_called: list[bool] = []

    def fake_exec(self: PlaywrightSetupDialog) -> int:
        exec_called.append(True)
        return 0

    with (
        patch("jatic_library.ui.main_window.chromium_is_ready", return_value=False),
        patch.object(PlaywrightSetupDialog, "exec", fake_exec),
        patch.object(PlaywrightSetupDialog, "install_succeeded", return_value=False),
    ):
        assert main_window._warn_playwright_chromium_missing() is True

    assert exec_called == [True]


def test_warn_continues_after_successful_install(main_window: MainWindow) -> None:
    with (
        patch(
            "jatic_library.ui.main_window.chromium_is_ready",
            side_effect=[False, True],
        ),
        patch.object(PlaywrightSetupDialog, "exec", lambda self: 0),
        patch.object(PlaywrightSetupDialog, "install_succeeded", return_value=True),
    ):
        assert main_window._warn_playwright_chromium_missing() is False


def test_run_scrape_execs_setup_dialog_when_chromium_missing(main_window: MainWindow) -> None:
    exec_called: list[bool] = []

    def fake_exec(self: PlaywrightSetupDialog) -> int:
        exec_called.append(True)
        return 0

    with (
        patch("jatic_library.ui.main_window.chromium_is_ready", return_value=False),
        patch.object(PlaywrightSetupDialog, "exec", fake_exec),
        patch.object(PlaywrightSetupDialog, "install_succeeded", return_value=False),
        patch("jatic_library.ui.main_window.AsyncTaskWorker") as mock_worker_cls,
    ):
        main_window.run_scrape()

    assert exec_called == [True]
    mock_worker_cls.assert_not_called()


def test_install_succeeded_after_worker_success(qapp: QApplication) -> None:
    dialog = PlaywrightSetupDialog()
    with patch(
        "jatic_library.ui.widgets.playwright_setup_dialog.install_chromium",
        return_value=(True, "ok"),
    ):
        dialog._start_install()
        while dialog._thread is not None and dialog._thread.isRunning():
            qapp.processEvents()
    assert dialog.install_succeeded() is True


def test_install_worker_forwards_lines(qapp: QApplication) -> None:
    dialog = PlaywrightSetupDialog()

    def fake_install(on_line: object) -> tuple[bool, str]:
        assert callable(on_line)
        on_line("line-one")  # type: ignore[operator]
        return True, "done"

    with patch(
        "jatic_library.ui.widgets.playwright_setup_dialog.install_chromium",
        side_effect=fake_install,
    ):
        dialog._start_install()
        while dialog._thread is not None and dialog._thread.isRunning():
            qapp.processEvents()

    assert "line-one" in dialog._log.toPlainText()
