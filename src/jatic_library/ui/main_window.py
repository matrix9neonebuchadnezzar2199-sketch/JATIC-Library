"""Main application window."""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Coroutine
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QTabWidget,
)

from jatic_library import __app_name__, __version__
from jatic_library.constants import REPO_URL
from jatic_library.core.playwright_scraper import scrape_and_save_targets
from jatic_library.core.repository import Repository
from jatic_library.core.scheduler import CheckOutcome, StartupScheduler
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.tabs.calendar_tab import CalendarTab
from jatic_library.ui.tabs.compare_tab import CompareTab
from jatic_library.ui.tabs.library_tab import LibraryTab
from jatic_library.ui.tabs.settings_tab import SettingsTab
from jatic_library.ui.theme import apply_theme
from jatic_library.ui.workers import AsyncTaskWorker


class MainWindow(QMainWindow):
    """Primary window with four feature tabs."""

    def __init__(
        self,
        config: AppConfig,
        store: ConfigStore,
        repo: Repository,
        *,
        run_startup_check: bool = True,
        parent: QMainWindow | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._store = store
        self._repo = repo
        self._active_worker: AsyncTaskWorker | None = None

        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.resize(1024, 720)

        self._tabs = QTabWidget()
        self._library_tab = LibraryTab(config, repo)
        self._settings_tab = SettingsTab(config, store)
        self._calendar_tab = CalendarTab()
        self._compare_tab = CompareTab()
        self._tabs.addTab(self._library_tab, "保管庫")
        self._tabs.addTab(self._settings_tab, "設定")
        self._tabs.addTab(self._calendar_tab, "カレンダー")
        self._tabs.addTab(self._compare_tab, "比較")
        self.setCentralWidget(self._tabs)

        self._build_menus()
        self.statusBar().showMessage("準備完了")

        self._settings_tab.config_saved.connect(self._on_config_saved)
        self._settings_tab.check_requested.connect(self.run_update_check)
        self._settings_tab.scrape_requested.connect(self.run_scrape)

        if config.is_initial_setup_needed():
            self._tabs.setCurrentWidget(self._settings_tab)
            self.statusBar().showMessage("保存先フォルダを設定してください（設定タブ）")
        elif run_startup_check and config.schedule.auto_check_on_startup:
            self.run_update_check(force=False)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("ファイル")
        quit_action = QAction("終了", self)
        quit_action.triggered.connect(QApplication.quit)
        file_menu.addAction(quit_action)

        tools_menu = self.menuBar().addMenu("ツール")
        check_action = QAction("今すぐ更新確認", self)
        check_action.triggered.connect(lambda: self.run_update_check(force=True))
        tools_menu.addAction(check_action)
        scrape_action = QAction("サイト再スキャン", self)
        scrape_action.triggered.connect(self.run_scrape)
        tools_menu.addAction(scrape_action)

        view_menu = self.menuBar().addMenu("表示")
        light_action = QAction("ライトテーマ", self)
        light_action.triggered.connect(lambda: self._set_theme("light"))
        dark_action = QAction("ダークテーマ", self)
        dark_action.triggered.connect(lambda: self._set_theme("dark"))
        view_menu.addAction(light_action)
        view_menu.addAction(dark_action)

        help_menu = self.menuBar().addMenu("ヘルプ")
        about_action = QAction("バージョン情報", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _set_theme(self, theme: str) -> None:
        self._config.ui.theme = theme  # type: ignore[assignment]
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, self._config.ui.theme)
        with contextlib.suppress(OSError):
            self._store.save(self._config)
        self._settings_tab.load_from_config()

    def _on_config_saved(self, config: AppConfig) -> None:
        self._config = config
        self._library_tab.update_config(config)
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, config.ui.theme)
        self.statusBar().showMessage("設定を反映しました", 5000)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            __app_name__,
            f"{__app_name__} v{__version__}\n\nJARTIC 断面交通量情報の自動取得・管理\n\n{REPO_URL}",
        )

    def _set_busy(self, busy: bool, message: str) -> None:
        if busy:
            self.setCursor(Qt.CursorShape.WaitCursor)
        else:
            self.unsetCursor()
        self.statusBar().showMessage(message)

    def _start_worker(
        self,
        coro_factory: Callable[[], Coroutine[Any, Any, object]],
        *,
        busy_message: str,
        on_success: Callable[[object], None],
    ) -> None:
        if self._active_worker is not None and self._active_worker.isRunning():
            QMessageBox.information(self, "処理中", "別のバックグラウンド処理が実行中です。")
            return
        if self._config.download.save_root is None:
            QMessageBox.warning(self, "設定", "保存先フォルダが未設定です。設定タブで指定してください。")
            self._tabs.setCurrentWidget(self._settings_tab)
            return

        self._set_busy(True, busy_message)
        worker = AsyncTaskWorker(coro_factory, self)
        self._active_worker = worker

        def _done(result: object) -> None:
            self._set_busy(False, "準備完了")
            self._active_worker = None
            on_success(result)

        def _fail(message: str) -> None:
            self._set_busy(False, "エラー")
            self._active_worker = None
            QMessageBox.critical(self, "エラー", message)

        worker.finished_ok.connect(_done)
        worker.failed.connect(_fail)
        worker.start()

    def run_update_check(self, *, force: bool) -> None:
        """Run scheduler check in a background thread."""

        async def _task() -> CheckOutcome:
            scheduler = StartupScheduler(self._config, self._repo)
            return await scheduler.run_check(force=force)

        def _on_success(result: object) -> None:
            outcome = result
            assert isinstance(outcome, CheckOutcome)
            self._settings_tab.load_from_config()
            self._library_tab.refresh()
            self.statusBar().showMessage(
                f"チェック完了: 新規 {outcome.new_downloads} / "
                f"スキップ {outcome.skipped} / エラー {outcome.errors}",
                10_000,
            )

        self._start_worker(_task, busy_message="更新を確認しています…", on_success=_on_success)

    def run_scrape(self) -> None:
        """Rescan JARTIC site for typeB links."""

        async def _task() -> int:
            return await scrape_and_save_targets()

        def _on_success(result: object) -> None:
            if not isinstance(result, int):
                return
            count = result
            QMessageBox.information(
                self,
                "再スキャン",
                f"typeB リンク {count} 件を targets.json に保存しました。\n"
                "地域キー変更時はアプリ再起動で一覧を更新してください。",
            )
            self.statusBar().showMessage(f"再スキャン完了: {count} 件", 10_000)

        self._start_worker(_task, busy_message="サイトを再スキャンしています…", on_success=_on_success)
