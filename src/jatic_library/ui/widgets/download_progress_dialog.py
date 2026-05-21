"""Modal download progress display."""

from __future__ import annotations

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from jatic_library.core.downloader import DownloadProgress
from jatic_library.core.publication_postprocess import (
    POSTPROCESS_EXTRACT_CODE,
    POSTPROCESS_MERGE_CODE,
)

_PROGRESS_LABELS: dict[str, str] = {
    POSTPROCESS_EXTRACT_CODE: "ZIP解凍",
    POSTPROCESS_MERGE_CODE: "CSV結合",
}


class DownloadProgressDialog(QDialog):
    """Show per-target download progress (thread-safe via signals)."""

    progress_reported = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ダウンロード進捗")
        self.setMinimumWidth(520)
        self.setMinimumHeight(560)
        self.resize(QSize(520, 640))
        self._bars: dict[str, QProgressBar] = {}
        self._labels: dict[str, QLabel] = {}

        layout = QVBoxLayout(self)
        self._summary = QLabel("準備中…")
        self._summary.setWordWrap(True)
        layout.addWidget(self._summary)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(420)
        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.addStretch()
        scroll.setWidget(self._container)
        layout.addWidget(scroll, stretch=1)

        self.progress_reported.connect(self._on_progress)

    def report(self, progress: DownloadProgress) -> None:
        """Emit progress from any thread (queued to GUI)."""
        self.progress_reported.emit(progress)

    def _display_name(self, code: str) -> str:
        return _PROGRESS_LABELS.get(code, code)

    def _on_progress(self, progress: object) -> None:
        if not isinstance(progress, DownloadProgress):
            return
        code = progress.target_code
        if code not in self._bars:
            label = QLabel(self._display_name(code))
            bar = QProgressBar()
            bar.setRange(0, 100)
            self._labels[code] = label
            self._bars[code] = bar
            insert_at = max(0, self._container_layout.count() - 1)
            self._container_layout.insertWidget(insert_at, label)
            self._container_layout.insertWidget(insert_at + 1, bar)

        bar = self._bars[code]
        label = self._labels[code]
        total = progress.bytes_total or 1
        pct = min(100, int(progress.bytes_done * 100 / total))
        bar.setValue(pct)
        name = self._display_name(code)
        label.setText(f"{name} — {progress.status}")
        self._summary.setText(f"処理中: {name} ({progress.status})")
