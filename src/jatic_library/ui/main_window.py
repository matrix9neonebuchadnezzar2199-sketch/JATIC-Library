"""Main application window."""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
)

from jatic_library import __app_name__, __version__
from jatic_library.constants import REPO_URL, TARGETS_CACHE_PATH
from jatic_library.core.downloader import Downloader
from jatic_library.core.exporter import (
    ExportError,
    default_export_name,
    export_merged_csv,
    export_publication_zip_bundle,
)
from jatic_library.core.library_scanner import LibraryFileItem
from jatic_library.core.manifest import Manifest
from jatic_library.core.playwright_scraper import scrape_and_save_targets
from jatic_library.core.repository import Repository
from jatic_library.core.scheduler import CheckOutcome, StartupScheduler
from jatic_library.core.startup import set_startup_enabled
from jatic_library.core.targets import load_overrides
from jatic_library.core.tray import TrayController
from jatic_library.core.url_builder import publish_info_from_folder
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.tabs.calendar_tab import CalendarTab
from jatic_library.ui.tabs.compare_tab import CompareTab
from jatic_library.ui.tabs.library_tab import LibraryTab
from jatic_library.ui.tabs.settings_tab import SettingsTab
from jatic_library.ui.theme import apply_theme
from jatic_library.ui.widgets.download_progress_dialog import DownloadProgressDialog
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
        self._quitting = False

        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.resize(1024, 720)

        self._tabs = QTabWidget()
        self._library_tab = LibraryTab(config, repo)
        self._settings_tab = SettingsTab(config, store)
        self._calendar_tab = CalendarTab(config, repo)
        self._compare_tab = CompareTab(config)
        self._tabs.addTab(self._library_tab, "保管庫")
        self._tabs.addTab(self._settings_tab, "設定")
        self._tabs.addTab(self._calendar_tab, "カレンダー")
        self._tabs.addTab(self._compare_tab, "比較")
        self.setCentralWidget(self._tabs)

        self._tray = TrayController(
            config.tray,
            on_check_now=lambda: self.run_update_check(force=True),
            on_show_window=self._show_from_tray,
            on_quit=self._quit_application,
            parent=self,
        )
        self._tray.setup()

        self._build_menus()
        self.statusBar().showMessage("準備完了")

        self._settings_tab.config_saved.connect(self._on_config_saved)
        self._settings_tab.check_requested.connect(self.run_update_check)
        self._settings_tab.scrape_requested.connect(self.run_scrape)
        self._library_tab.redownload_requested.connect(self._on_redownload_file)
        self._library_tab.delete_requested.connect(self._on_delete_file)
        self._library_tab.export_month_requested.connect(self._on_export_month)
        self._library_tab.sort_changed.connect(self._on_library_sort_changed)

        if config.is_initial_setup_needed():
            self._tabs.setCurrentWidget(self._settings_tab)
            self.statusBar().showMessage("保存先フォルダを設定してください（設定タブ）")
        elif run_startup_check and config.schedule.auto_check_on_startup:
            self.run_update_check(force=False)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("ファイル")
        quit_action = QAction("終了", self)
        quit_action.triggered.connect(self._quit_application)
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

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_application(self) -> None:
        self._quitting = True
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        if (
            not self._quitting
            and self._config.tray.enable_tray
            and self._config.tray.minimize_to_tray
        ):
            event.ignore()
            self.hide()
            self.statusBar().showMessage("トレイに格納しました", 5000)
            return
        super().closeEvent(event)

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
        self._calendar_tab.update_config(config)
        self._compare_tab.update_config(config)
        if config.tray.start_with_windows:
            try:
                set_startup_enabled(True)
            except OSError as exc:
                QMessageBox.warning(self, "スタートアップ", f"登録に失敗しました:\n{exc}")
        else:
            with contextlib.suppress(OSError):
                set_startup_enabled(False)
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, config.ui.theme)
        self.statusBar().showMessage("設定を反映しました", 5000)

    def _on_library_sort_changed(self, _sort_key: str) -> None:
        with contextlib.suppress(OSError):
            self._store.save(self._config)

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
        progress_dialog = DownloadProgressDialog(self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.show()

        async def _task() -> CheckOutcome:
            scheduler = StartupScheduler(self._config, self._repo)

            def _progress_cb(progress: object) -> None:
                from jatic_library.core.downloader import DownloadProgress

                if isinstance(progress, DownloadProgress):
                    progress_dialog.report(progress)

            return await scheduler.run_check(force=force, progress_cb=_progress_cb)

        def _on_success(result: object) -> None:
            progress_dialog.accept()
            outcome = result
            assert isinstance(outcome, CheckOutcome)
            self._settings_tab.load_from_config()
            self._refresh_data_tabs()
            self.statusBar().showMessage(
                f"チェック完了: 新規 {outcome.new_downloads} / "
                f"スキップ {outcome.skipped} / エラー {outcome.errors}",
                10_000,
            )

        def _on_fail(message: str) -> None:
            progress_dialog.reject()
            QMessageBox.critical(self, "エラー", message)

        if self._active_worker is not None and self._active_worker.isRunning():
            QMessageBox.information(self, "処理中", "別のバックグラウンド処理が実行中です。")
            progress_dialog.reject()
            return
        if self._config.download.save_root is None:
            QMessageBox.warning(self, "設定", "保存先フォルダが未設定です。設定タブで指定してください。")
            self._tabs.setCurrentWidget(self._settings_tab)
            progress_dialog.reject()
            return

        self._set_busy(True, "更新を確認しています…")
        worker = AsyncTaskWorker(_task, self)
        self._active_worker = worker

        def _done(result: object) -> None:
            self._set_busy(False, "準備完了")
            self._active_worker = None
            _on_success(result)

        worker.finished_ok.connect(_done)
        worker.failed.connect(_on_fail)
        worker.start()

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

    def _refresh_data_tabs(self) -> None:
        self._library_tab.refresh()
        self._calendar_tab.refresh()
        self._compare_tab.refresh()

    def _on_redownload_file(self, file_item: object) -> None:
        if not isinstance(file_item, LibraryFileItem) or file_item.target_code is None:
            return
        if self._config.download.save_root is None:
            return
        info = publish_info_from_folder(file_item.publish_ym)
        master = load_overrides(TARGETS_CACHE_PATH)
        target = next((t for t in master if t.code == file_item.target_code), None)
        if target is None:
            QMessageBox.warning(self, "再ダウンロード", "地域マスタに該当コードがありません。")
            return

        async def _task() -> object:
            downloader = Downloader(self._config.download, self._repo)
            return await downloader.download_publication(info, [target])

        def _on_success(_result: object) -> None:
            self._refresh_data_tabs()
            self.statusBar().showMessage("再ダウンロードが完了しました", 8000)

        self._start_worker(_task, busy_message="再ダウンロード中…", on_success=_on_success)

    def _on_delete_file(self, file_item: object) -> None:
        if not isinstance(file_item, LibraryFileItem):
            return
        path = file_item.file_path
        try:
            if path.is_file():
                path.unlink()
        except OSError as exc:
            QMessageBox.critical(self, "削除", f"ファイル削除に失敗しました:\n{exc}")
            return

        folder = path.parent
        manifest = Manifest.load(folder)
        if manifest is not None and file_item.target_code:
            manifest.remove_file(file_item.target_code)
            manifest.save(folder)

        if file_item.target_code:
            row = self._repo.get_file(file_item.publish_ym, file_item.target_code)
            if row is not None and row.id is not None:
                self._repo.delete_file(row.id)

        self._refresh_data_tabs()
        self.statusBar().showMessage("ファイルを削除しました", 5000)

    def _on_export_month(self, publish_ym: str) -> None:
        if self._config.download.save_root is None:
            return
        choice = QMessageBox.question(
            self,
            "エクスポート",
            f"{publish_ym} を ZIP バンドルとして出力しますか？\n"
            "「いいえ」で統合 CSV を出力します。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if choice == QMessageBox.StandardButton.Yes:
            default_name = default_export_name(publish_ym, "zip")
            dest, _ = QFileDialog.getSaveFileName(
                self,
                "ZIP バンドルを保存",
                default_name,
                "ZIP (*.zip)",
            )
            if not dest:
                return
            try:
                export_publication_zip_bundle(
                    self._config.download.save_root,
                    publish_ym,
                    Path(dest),
                )
            except ExportError as exc:
                QMessageBox.warning(self, "エクスポート", str(exc))
                return
        elif choice == QMessageBox.StandardButton.No:
            default_name = default_export_name(publish_ym, "csv")
            dest, _ = QFileDialog.getSaveFileName(
                self,
                "統合 CSV を保存",
                default_name,
                "CSV (*.csv)",
            )
            if not dest:
                return
            try:
                export_merged_csv(
                    self._config.download.save_root,
                    publish_ym,
                    Path(dest),
                )
            except ExportError as exc:
                QMessageBox.warning(self, "エクスポート", str(exc))
                return
        else:
            return
        QMessageBox.information(self, "エクスポート", "エクスポートが完了しました。")
