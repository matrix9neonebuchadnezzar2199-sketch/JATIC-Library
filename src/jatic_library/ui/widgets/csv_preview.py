"""ZIP CSV preview table."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from jatic_library.core.csv_loader import CsvPreviewError, preview_csv_from_zip


class CsvPreviewWidget(QWidget):
    """Preview the first CSV inside a ZIP (up to 1000 rows)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._status = QLabel("ZIP を選択すると CSV プレビューを表示します。")
        self._status.setWordWrap(True)
        self._table = QTableWidget()
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._status)
        layout.addWidget(self._table)

    def clear(self) -> None:
        """Clear the preview table."""
        self._status.setText("ZIP を選択すると CSV プレビューを表示します。")
        self._table.clear()
        self._table.setRowCount(0)
        self._table.setColumnCount(0)

    def load_zip(self, zip_path: Path) -> None:
        """Load CSV preview from *zip_path*."""
        try:
            headers, rows = preview_csv_from_zip(zip_path)
        except CsvPreviewError as exc:
            self._status.setText(str(exc))
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            return

        self._status.setText(f"{zip_path.name} — {len(rows)} 行表示（最大1000行）")
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                cell = QTableWidgetItem(value)
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_index, col_index, cell)
        self._table.resizeColumnsToContents()
