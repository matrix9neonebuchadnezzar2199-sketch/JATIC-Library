"""Settings tab for AppConfig editing."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from jatic_library.core.targets import all_codes
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.widgets.region_selector import RegionSelector


class SettingsTab(QWidget):
    """Edit and persist application settings."""

    config_saved = Signal(AppConfig)
    check_requested = Signal(bool)
    scrape_requested = Signal()

    def __init__(
        self,
        config: AppConfig,
        store: ConfigStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._store = store
        self._build_ui()
        self.load_from_config()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setSpacing(12)

        # 左列: ダウンロード対象地域 -- タブ高さいっぱい
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        regions = QGroupBox("ダウンロード対象地域")
        regions_layout = QVBoxLayout(regions)
        self._region_selector = RegionSelector()
        regions_layout.addWidget(self._region_selector, stretch=1)
        self._region_summary = QLabel()
        regions_layout.addWidget(self._region_summary)
        self._region_selector.selection_changed.connect(self._update_region_summary)
        left_layout.addWidget(regions, stretch=1)

        root.addWidget(left_panel, stretch=1)

        # 右列: その他の設定 -- 縦スクロール
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_body = QWidget()
        right_layout = QVBoxLayout(right_body)

        basic = QGroupBox("基本")
        basic_form = QFormLayout(basic)
        save_row = QHBoxLayout()
        self._save_root = QLineEdit()
        browse = QPushButton("参照…")
        browse.clicked.connect(self._browse_save_root)
        save_row.addWidget(self._save_root)
        save_row.addWidget(browse)
        basic_form.addRow("保存先フォルダ", save_row)
        self._theme = QComboBox()
        self._theme.addItems(["light", "dark"])
        basic_form.addRow("テーマ", self._theme)
        right_layout.addWidget(basic)

        schedule = QGroupBox("起動時チェック")
        schedule_form = QFormLayout(schedule)
        self._auto_check = QCheckBox("起動時に自動チェックする")
        schedule_form.addRow(self._auto_check)
        self._interval_hours = QSpinBox()
        self._interval_hours.setRange(1, 720)
        schedule_form.addRow("再チェック間隔（時間）", self._interval_hours)
        self._last_check_label = QLabel("—")
        schedule_form.addRow("最終チェック", self._last_check_label)
        right_layout.addWidget(schedule)

        download = QGroupBox("ダウンロード")
        download_form = QFormLayout(download)
        self._concurrency = QSpinBox()
        self._concurrency.setRange(1, 10)
        download_form.addRow("同時ダウンロード数", self._concurrency)
        self._retry = QSpinBox()
        self._retry.setRange(0, 10)
        download_form.addRow("リトライ回数", self._retry)
        self._timeout = QSpinBox()
        self._timeout.setRange(10, 600)
        self._timeout.setSuffix(" 秒")
        download_form.addRow("タイムアウト", self._timeout)
        right_layout.addWidget(download)

        notify = QGroupBox("通知")
        notify_layout = QVBoxLayout(notify)
        self._notify_new = QCheckBox("新規公開検知時")
        self._notify_complete = QCheckBox("ダウンロード完了時")
        self._notify_error = QCheckBox("エラー時")
        notify_layout.addWidget(self._notify_new)
        notify_layout.addWidget(self._notify_complete)
        notify_layout.addWidget(self._notify_error)
        right_layout.addWidget(notify)

        log_group = QGroupBox("ログ")
        log_form = QFormLayout(log_group)
        self._log_level = QComboBox()
        self._log_level.addItems(["DEBUG", "INFO", "WARN", "ERROR"])
        log_form.addRow("ログレベル", self._log_level)
        self._log_retention = QComboBox()
        self._log_retention.addItems(["30d", "90d", "infinite"])
        log_form.addRow("ログ保持", self._log_retention)
        right_layout.addWidget(log_group)

        tray_group = QGroupBox("トレイ・スタートアップ")
        tray_layout = QVBoxLayout(tray_group)
        self._enable_tray = QCheckBox("システムトレイを有効にする")
        self._minimize_tray = QCheckBox("閉じるときトレイに格納する")
        self._start_with_windows = QCheckBox("Windows 起動時に自動起動")
        tray_layout.addWidget(self._enable_tray)
        tray_layout.addWidget(self._minimize_tray)
        tray_layout.addWidget(self._start_with_windows)
        right_layout.addWidget(tray_group)

        github_group = QGroupBox("Git 連携（任意）")
        github_form = QFormLayout(github_group)
        self._github_enabled = QCheckBox("Git 同期を有効にする")
        github_form.addRow(self._github_enabled)
        self._github_repo = QLineEdit()
        github_form.addRow("リポジトリパス", self._github_repo)
        self._github_auto_commit = QCheckBox("ダウンロード後に自動 commit")
        github_form.addRow(self._github_auto_commit)
        right_layout.addWidget(github_group)

        actions = QHBoxLayout()
        save_btn = QPushButton("設定を保存")
        save_btn.clicked.connect(self.save_to_store)
        check_btn = QPushButton("今すぐ更新確認")
        check_btn.clicked.connect(lambda: self.check_requested.emit(True))
        scrape_btn = QPushButton("サイト再スキャン")
        scrape_btn.clicked.connect(self.scrape_requested.emit)
        actions.addWidget(save_btn)
        actions.addWidget(check_btn)
        actions.addWidget(scrape_btn)
        actions.addStretch()
        right_layout.addLayout(actions)
        right_layout.addStretch()

        right_scroll.setWidget(right_body)
        root.addWidget(right_scroll, stretch=1)

    def _browse_save_root(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "保存先フォルダを選択")
        if path:
            self._save_root.setText(path)

    def _update_region_summary(self) -> None:
        self._region_summary.setText(self._region_selector.selection_summary())

    def load_from_config(self) -> None:
        """Populate widgets from ``self._config``."""
        cfg = self._config
        self._save_root.setText(str(cfg.download.save_root) if cfg.download.save_root else "")
        self._theme.setCurrentText(cfg.ui.theme)
        self._region_selector.set_selected_codes(cfg.targets.selected_codes)
        self._update_region_summary()
        self._auto_check.setChecked(cfg.schedule.auto_check_on_startup)
        self._interval_hours.setValue(cfg.schedule.recheck_interval_hours)
        self._last_check_label.setText(cfg.schedule.last_check_at or "未実行")
        self._concurrency.setValue(cfg.download.concurrency)
        self._retry.setValue(cfg.download.retry)
        self._timeout.setValue(cfg.download.timeout_sec)
        self._notify_new.setChecked(cfg.notification.on_new_publish)
        self._notify_complete.setChecked(cfg.notification.on_complete)
        self._notify_error.setChecked(cfg.notification.on_error)
        self._log_level.setCurrentText(cfg.log.level)
        self._log_retention.setCurrentText(cfg.log.retention)
        self._enable_tray.setChecked(cfg.tray.enable_tray)
        self._minimize_tray.setChecked(cfg.tray.minimize_to_tray)
        self._start_with_windows.setChecked(cfg.tray.start_with_windows)
        self._github_enabled.setChecked(cfg.github.enabled)
        self._github_repo.setText(str(cfg.github.repo_path) if cfg.github.repo_path else "")
        self._github_auto_commit.setChecked(cfg.github.auto_commit)

    def apply_to_config(self) -> AppConfig:
        """Copy widget state into ``self._config``."""
        path_text = self._save_root.text().strip()
        self._config.download.save_root = Path(path_text) if path_text else None
        self._config.ui.theme = cast(Literal["light", "dark"], self._theme.currentText())
        selected = self._region_selector.selected_codes()
        total = len(all_codes())
        self._config.targets.selected_codes = set() if len(selected) >= total else selected
        self._config.schedule.auto_check_on_startup = self._auto_check.isChecked()
        self._config.schedule.recheck_interval_hours = self._interval_hours.value()
        self._config.download.concurrency = self._concurrency.value()
        self._config.download.retry = self._retry.value()
        self._config.download.timeout_sec = self._timeout.value()
        self._config.notification.on_new_publish = self._notify_new.isChecked()
        self._config.notification.on_complete = self._notify_complete.isChecked()
        self._config.notification.on_error = self._notify_error.isChecked()
        self._config.log.level = cast(
            Literal["DEBUG", "INFO", "WARN", "ERROR"],
            self._log_level.currentText(),
        )
        self._config.log.retention = cast(
            Literal["30d", "90d", "infinite"],
            self._log_retention.currentText(),
        )
        self._config.tray.enable_tray = self._enable_tray.isChecked()
        self._config.tray.minimize_to_tray = self._minimize_tray.isChecked()
        self._config.tray.start_with_windows = self._start_with_windows.isChecked()
        self._config.github.enabled = self._github_enabled.isChecked()
        repo_text = self._github_repo.text().strip()
        self._config.github.repo_path = Path(repo_text) if repo_text else None
        self._config.github.auto_commit = self._github_auto_commit.isChecked()
        return self._config

    def save_to_store(self) -> None:
        """Validate, save config, and emit ``config_saved``."""
        self.apply_to_config()
        if self._config.download.save_root is None:
            QMessageBox.warning(self, "設定", "保存先フォルダを指定してください。")
            return
        try:
            self._store.save(self._config)
        except OSError as exc:
            QMessageBox.critical(self, "設定", f"保存に失敗しました:\n{exc}")
            return
        self._last_check_label.setText(self._config.schedule.last_check_at or "未実行")
        self.config_saved.emit(self._config)
        QMessageBox.information(self, "設定", "設定を保存しました。")

    @property
    def config(self) -> AppConfig:
        return self._config
