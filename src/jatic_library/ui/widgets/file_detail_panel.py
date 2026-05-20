"""Metadata panel for a selected library file."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from jatic_library.core.library_scanner import LibraryFileItem


def _format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.2f} GB"


class FileDetailPanel(QWidget):
    """Show file metadata for the library tree selection."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._form = QFormLayout(self)
        self._labels: dict[str, QLabel] = {}
        for key in (
            "表示名",
            "公開月",
            "コード",
            "パス",
            "サイズ",
            "SHA256",
            "ダウンロード日時",
            "元 URL",
            "DB ステータス",
        ):
            value = QLabel("—")
            value.setWordWrap(True)
            value.setTextInteractionFlags(
                value.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._labels[key] = value
            self._form.addRow(key, value)

    def clear(self) -> None:
        """Reset all fields."""
        for label in self._labels.values():
            label.setText("—")

    def show_file(self, item: LibraryFileItem) -> None:
        """Populate fields from *item*."""
        self._labels["表示名"].setText(item.display_name)
        self._labels["公開月"].setText(item.publish_ym)
        self._labels["コード"].setText(item.target_code or "—")
        self._labels["パス"].setText(str(item.file_path))
        self._labels["サイズ"].setText(_format_bytes(item.file_size))
        self._labels["SHA256"].setText(item.sha256 or "—")
        self._labels["ダウンロード日時"].setText(item.downloaded_at or "—")
        self._labels["元 URL"].setText(item.source_url or "—")
        self._labels["DB ステータス"].setText(item.status or "—")
