"""Library tab placeholder (#11)."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LibraryTab(QWidget):
    """Three-pane library browser (implemented in a later instruction)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(
            "保管庫タブ（#11 で実装予定）\n"
            "年 → 月 → 地域のツリー、詳細ペイン、CSV プレビューをここに配置します。"
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
