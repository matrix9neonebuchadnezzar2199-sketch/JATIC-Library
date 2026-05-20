"""Calendar tab placeholder (#14)."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CalendarTab(QWidget):
    """Publication calendar (implemented in a later instruction)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(
            "カレンダータブ（#14 で実装予定）\n"
            "公開済み月のマーカーと次回公開予定日を表示します。"
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        layout.addStretch()
