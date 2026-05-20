"""Compare two publication months for one region."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from jatic_library.core.library_scanner import LibraryFileItem, scan_library
from jatic_library.settings.config import AppConfig
from jatic_library.ui.widgets.csv_preview import CsvPreviewWidget
from jatic_library.ui.widgets.traffic_chart import TrafficChartWidget


class CompareTab(QWidget):
    """Side-by-side CSV preview for two months of the same region."""

    def __init__(
        self,
        config: AppConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._files_by_month: dict[str, list[LibraryFileItem]] = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._region = QComboBox()
        self._region.currentIndexChanged.connect(self._reload_previews)
        form.addRow("地域", self._region)

        month_row = QHBoxLayout()
        self._month_a = QComboBox()
        self._month_b = QComboBox()
        self._month_a.currentIndexChanged.connect(self._reload_previews)
        self._month_b.currentIndexChanged.connect(self._reload_previews)
        month_row.addWidget(QLabel("月 A"))
        month_row.addWidget(self._month_a)
        month_row.addWidget(QLabel("月 B"))
        month_row.addWidget(self._month_b)
        form.addRow(month_row)
        layout.addLayout(form)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("月 A"))
        self._preview_a = CsvPreviewWidget()
        self._chart_a = TrafficChartWidget()
        left_layout.addWidget(self._preview_a)
        left_layout.addWidget(self._chart_a)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("月 B"))
        self._preview_b = CsvPreviewWidget()
        self._chart_b = TrafficChartWidget()
        right_layout.addWidget(self._preview_b)
        right_layout.addWidget(self._chart_b)
        splitter.addWidget(right)
        layout.addWidget(splitter)

    def update_config(self, config: AppConfig) -> None:
        """Replace config and refresh month list."""
        self._config = config
        self.refresh()

    def refresh(self) -> None:
        """Rebuild month and region selectors from disk."""
        self._files_by_month.clear()
        save_root = self._config.download.save_root
        if save_root is None:
            self._month_a.clear()
            self._month_b.clear()
            self._region.clear()
            return

        tree = scan_library(save_root, sort="date_desc")
        months: list[str] = []
        regions: dict[str, str] = {}
        for year_item in tree:
            for month_item in year_item.months:
                months.append(month_item.folder_name)
                self._files_by_month[month_item.folder_name] = list(month_item.files)
                for file_item in month_item.files:
                    key = file_item.target_code or file_item.display_name
                    regions[key] = file_item.display_name

        self._month_a.blockSignals(True)
        self._month_b.blockSignals(True)
        self._month_a.clear()
        self._month_b.clear()
        for folder in months:
            self._month_a.addItem(folder, folder)
            self._month_b.addItem(folder, folder)
        if len(months) >= 2:
            self._month_b.setCurrentIndex(1)
        self._month_a.blockSignals(False)
        self._month_b.blockSignals(False)

        self._region.blockSignals(True)
        self._region.clear()
        for code, label in sorted(regions.items(), key=lambda item: item[1]):
            self._region.addItem(label, code)
        self._region.blockSignals(False)
        self._reload_previews()

    def _find_zip(self, publish_ym: str, target_code: str) -> Path | None:
        for file_item in self._files_by_month.get(publish_ym, []):
            if file_item.target_code == target_code:
                return file_item.file_path
        return None

    def _reload_previews(self) -> None:
        """Load CSV previews for the selected months and region."""
        code = self._region.currentData()
        if not isinstance(code, str):
            self._preview_a.clear()
            self._preview_b.clear()
            self._chart_a.clear()
            self._chart_b.clear()
            return
        month_a = self._month_a.currentData()
        month_b = self._month_b.currentData()
        if not isinstance(month_a, str) or not isinstance(month_b, str):
            return
        path_a = self._find_zip(month_a, code)
        path_b = self._find_zip(month_b, code)
        if path_a is not None:
            self._preview_a.load_zip(path_a)
            self._chart_a.load_zip(path_a)
        else:
            self._preview_a.clear()
            self._chart_a.clear()
        if path_b is not None:
            self._preview_b.load_zip(path_b)
            self._chart_b.load_zip(path_b)
        else:
            self._preview_b.clear()
            self._chart_b.clear()
