"""Calendar tab with publication markers and missing months."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QFormLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from jatic_library.core.repository import Repository
from jatic_library.core.url_builder import compute_publish_info, parse_folder_name
from jatic_library.settings.config import AppConfig


class CalendarTab(QWidget):
    """Show next publish date and highlight missing publication months."""

    def __init__(
        self,
        config: AppConfig,
        repo: Repository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._repo = repo
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        info_box = QFormLayout()
        self._next_publish = QLabel("—")
        self._data_folder = QLabel("—")
        info_box.addRow("次回公開（予定）", self._next_publish)
        info_box.addRow("対象データ月フォルダ", self._data_folder)
        layout.addLayout(info_box)

        self._calendar = QCalendarWidget()
        self._calendar.setGridVisible(True)
        layout.addWidget(self._calendar)

        self._missing_label = QLabel("欠損・未完了の公開月")
        layout.addWidget(self._missing_label)
        self._missing_list = QListWidget()
        layout.addWidget(self._missing_list)

    def update_config(self, config: AppConfig) -> None:
        """Replace config and refresh."""
        self._config = config
        self.refresh()

    def refresh(self) -> None:
        """Rebuild calendar markers and missing-month list."""
        today = date.today()
        info = compute_publish_info(today)
        self._next_publish.setText(f"{info.publish_year}年{info.publish_month}月")
        self._data_folder.setText(info.folder_name)

        missing_format = QTextCharFormat()
        missing_format.setBackground(QColor(255, 220, 220))
        missing_format.setForeground(QColor(120, 0, 0))

        complete_format = QTextCharFormat()
        complete_format.setBackground(QColor(220, 255, 220))

        self._calendar.setDateTextFormat(QDate(), QTextCharFormat())

        end_year, end_month = today.year, today.month
        start_year, start_month = end_year - 2, end_month
        missing = self._repo.list_missing_publications(
            (start_year, start_month),
            (end_year, end_month),
        )
        missing_set = set(missing)
        self._missing_list.clear()
        for folder in missing:
            self._missing_list.addItem(folder)
            try:
                year, month = parse_folder_name(folder)
            except ValueError:
                continue
            qdate = QDate(year, month, 1)
            self._calendar.setDateTextFormat(qdate, missing_format)

        save_root = self._config.download.save_root
        if save_root is not None and save_root.is_dir():
            for pub_dir in save_root.iterdir():
                if not pub_dir.is_dir():
                    continue
                try:
                    year, month = parse_folder_name(pub_dir.name)
                except ValueError:
                    continue
                if pub_dir.name not in missing_set and self._repo.is_publication_complete(
                    pub_dir.name
                ):
                    qdate = QDate(year, month, 1)
                    self._calendar.setDateTextFormat(qdate, complete_format)
