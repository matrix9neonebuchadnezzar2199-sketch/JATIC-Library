"""Modal download progress display."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from jatic_library.core.downloader import DownloadProgress


class DownloadProgressDialog(QDialog):
    """Show per-target download progress (thread-safe via signals)."""

    progress_reported = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ダウンロード進捗")
        self.setMinimumWidth(480)
        self._bars: dict[str, QProgressBar] = {}
        self._labels: dict[str, QLabel] = {}

        layout = QVBoxLayout(self)
        self._summary = QLabel("準備中…")
        layout.addWidget(self._summary)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        scroll.setWidget(self._container)
        layout.addWidget(scroll)

        self.progress_reported.connect(self._on_progress)

    def report(self, progress: DownloadProgress) -> None:
        """Emit progress from any thread (queued to GUI)."""
        self.progress_reported.emit(progress)

    def _on_progress(self, progress: object) -> None:
        if not isinstance(progress, DownloadProgress):
            return
        code = progress.target_code
        if code not in self._bars:
            label = QLabel(code)
            bar = QProgressBar()
            bar.setRange(0, 100)
            self._labels[code] = label
            self._bars[code] = bar
            self._container_layout.addWidget(label)
            self._container_layout.addWidget(bar)

        bar = self._bars[code]
        label = self._labels[code]
        total = progress.bytes_total or 1
        pct = min(100, int(progress.bytes_done * 100 / total))
        bar.setValue(pct)
        label.setText(f"{code} — {progress.status}")
        self._summary.setText(f"処理中: {code} ({progress.status})")
