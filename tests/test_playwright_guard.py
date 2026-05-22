"""Tests for Playwright Chromium guards on MainWindow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from jatic_library.core.library_scanner import LibraryFileItem
from jatic_library.core.repository import Repository
from jatic_library.core.targets import TARGETS
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp: QApplication, tmp_path: Path) -> MainWindow:
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


def _file_item(tmp_path: Path) -> LibraryFileItem:
    folder = tmp_path / "data" / "2026_3"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "tokyo.zip"
    path.write_bytes(b"x")
    return LibraryFileItem(
        publish_ym="2026_3",
        file_name="tokyo.zip",
        file_path=path,
        display_name="東京都",
        target_code="tokyo",
        file_size=1,
        sha256=None,
        source_url=None,
        downloaded_at=None,
    )


def test_run_update_check_blocked_when_chromium_missing(main_window: MainWindow) -> None:
    with (
        patch.object(main_window, "_warn_playwright_chromium_missing", return_value=True),
        patch("jatic_library.ui.main_window.DownloadProgressDialog") as mock_dialog_cls,
        patch("jatic_library.ui.main_window.AsyncTaskWorker") as mock_worker_cls,
    ):
        main_window.run_update_check(force=True)

    mock_dialog_cls.assert_not_called()
    mock_worker_cls.assert_not_called()
    assert main_window._active_worker is None


def test_run_update_check_proceeds_when_chromium_ready(main_window: MainWindow) -> None:
    mock_worker = MagicMock()
    mock_worker.isRunning.return_value = False

    with (
        patch.object(main_window, "_warn_playwright_chromium_missing", return_value=False),
        patch(
            "jatic_library.ui.main_window.DownloadProgressDialog",
            return_value=MagicMock(),
        ),
        patch(
            "jatic_library.ui.main_window.AsyncTaskWorker",
            return_value=mock_worker,
        ) as mock_worker_cls,
    ):
        main_window.run_update_check(force=True)

    mock_worker_cls.assert_called_once()
    assert main_window._active_worker is mock_worker
    mock_worker.start.assert_called_once()


def test_redownload_blocked_when_chromium_missing(
    main_window: MainWindow,
    tmp_path: Path,
) -> None:
    item = _file_item(tmp_path)

    with (
        patch.object(main_window, "_warn_playwright_chromium_missing", return_value=True),
        patch("jatic_library.ui.main_window.AsyncTaskWorker") as mock_worker_cls,
    ):
        main_window._on_redownload_file(item)

    mock_worker_cls.assert_not_called()
    assert main_window._active_worker is None


def test_redownload_proceeds_when_chromium_ready(
    main_window: MainWindow,
    tmp_path: Path,
) -> None:
    item = _file_item(tmp_path)
    mock_worker = MagicMock()
    mock_worker.isRunning.return_value = False
    tokyo = next(t for t in TARGETS if t.code == "tokyo")

    with (
        patch.object(main_window, "_warn_playwright_chromium_missing", return_value=False),
        patch(
            "jatic_library.ui.main_window.AsyncTaskWorker",
            return_value=mock_worker,
        ) as mock_worker_cls,
        patch(
            "jatic_library.ui.main_window.load_overrides",
            return_value=[tokyo],
        ),
    ):
        main_window._on_redownload_file(item)

    mock_worker_cls.assert_called_once()
    assert main_window._active_worker is mock_worker
    mock_worker.start.assert_called_once()
