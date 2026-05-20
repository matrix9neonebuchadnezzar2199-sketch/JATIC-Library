"""Calendar tab with publication markers and missing months."""

from __future__ import annotations

from datetime import date
from typing import Literal

from PySide6.QtCore import QDate
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QFormLayout,
    QGroupBox,
    QLabel,
    QListWidget,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from jatic_library.core.repository import Repository
from jatic_library.core.url_builder import compute_publish_info, parse_folder_name
from jatic_library.settings.config import AppConfig

ThemeName = Literal["light", "dark"]

_MISSING_COLORS: dict[ThemeName, tuple[str, str]] = {
    "light": ("#fef3c7", "#92400e"),
    "dark": ("#422006", "#fcd34d"),
}
_COMPLETE_COLORS: dict[ThemeName, tuple[str, str]] = {
    "light": ("#d1fae5", "#065f46"),
    "dark": ("#064e3b", "#6ee7b7"),
}


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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        schedule = QGroupBox("公開スケジュール")
        schedule_form = QFormLayout(schedule)
        schedule_form.setSpacing(10)
        self._next_publish = QLabel("—")
        self._next_publish.setObjectName("heroValue")
        self._data_folder = QLabel("—")
        self._data_folder.setObjectName("heroValue")
        schedule_form.addRow("次回公開（予定）", self._next_publish)
        schedule_form.addRow("対象データ月フォルダ", self._data_folder)
        layout.addWidget(schedule)

        calendar_box = QGroupBox("月間カレンダー")
        calendar_layout = QVBoxLayout(calendar_box)
        hint = QLabel("欠損月は琥珀色、取得完了月は緑色で表示します。")
        hint.setObjectName("sectionHint")
        calendar_layout.addWidget(hint)
        self._calendar = QCalendarWidget()
        self._calendar.setObjectName("publicationCalendar")
        self._calendar.setGridVisible(True)
        self._calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.ISOWeekNumbers
        )
        self._calendar.setMinimumHeight(300)
        self._calendar.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        calendar_layout.addWidget(self._calendar)
        layout.addWidget(calendar_box, stretch=2)

        missing_box = QGroupBox("欠損・未完了の公開月")
        missing_layout = QVBoxLayout(missing_box)
        self._missing_list = QListWidget()
        self._missing_list.setObjectName("missingMonthList")
        self._missing_list.setAlternatingRowColors(True)
        missing_layout.addWidget(self._missing_list)
        layout.addWidget(missing_box, stretch=1)

    def update_config(self, config: AppConfig) -> None:
        """Replace config and refresh."""
        self._config = config
        self.refresh()

    def _marker_formats(self) -> tuple[QTextCharFormat, QTextCharFormat]:
        theme: ThemeName = self._config.ui.theme
        missing_bg, missing_fg = _MISSING_COLORS[theme]
        complete_bg, complete_fg = _COMPLETE_COLORS[theme]

        missing_format = QTextCharFormat()
        missing_format.setBackground(QColor(missing_bg))
        missing_format.setForeground(QColor(missing_fg))

        complete_format = QTextCharFormat()
        complete_format.setBackground(QColor(complete_bg))
        complete_format.setForeground(QColor(complete_fg))
        return missing_format, complete_format

    def refresh(self) -> None:
        """Rebuild calendar markers and missing-month list."""
        today = date.today()
        info = compute_publish_info(today)
        self._next_publish.setText(f"{info.publish_year}年{info.publish_month}月")
        self._data_folder.setText(info.folder_name)

        missing_format, complete_format = self._marker_formats()

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
