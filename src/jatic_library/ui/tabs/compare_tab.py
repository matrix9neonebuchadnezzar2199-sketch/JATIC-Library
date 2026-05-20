"""Compare tab placeholder (#16)."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CompareTab(QWidget):
    """Side-by-side month comparison (implemented in a later instruction)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(
            "比較タブ（#16 で実装予定）\n"
            "同一地域の2か月分を並べて比較します。"
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
