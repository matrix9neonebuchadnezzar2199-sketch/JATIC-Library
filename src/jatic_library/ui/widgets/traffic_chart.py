"""Simple traffic bar chart from a ZIP CSV."""

from __future__ import annotations

import zipfile
from pathlib import Path

import polars as pl
import pyqtgraph as pg
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from jatic_library.core.csv_loader import CsvPreviewError, find_first_csv_name


class TrafficChartWidget(QWidget):
    """Plot the first numeric column found in a region ZIP."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._hint = QLabel("ZIP を選択してグラフを表示します。")
        self._hint.setWordWrap(True)
        layout.addWidget(self._hint)
        self._plot = pg.PlotWidget()
        self._plot.setBackground("w")
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self._plot)

    def clear(self) -> None:
        """Reset chart state."""
        self._plot.clear()
        self._hint.setText("ZIP を選択してグラフを表示します。")

    def load_zip(self, zip_path: Path, *, max_points: int = 200) -> None:
        """Load *zip_path* and plot the first numeric column."""
        self._plot.clear()
        if not zip_path.is_file():
            self._hint.setText("ファイルが見つかりません。")
            return
        try:
            csv_name = find_first_csv_name(zip_path)
        except CsvPreviewError as exc:
            self._hint.setText(str(exc))
            return

        with zipfile.ZipFile(zip_path) as archive:
            raw = archive.read(csv_name)
        frame: pl.DataFrame | None = None
        for encoding in ("utf-8", "cp932"):
            try:
                frame = pl.read_csv(
                    raw,
                    encoding=encoding,
                    infer_schema_length=50,
                    ignore_errors=True,
                )
                break
            except Exception:  # noqa: S112 — try next encoding
                continue
        if frame is None or frame.is_empty():
            self._hint.setText("CSV を読み込めませんでした。")
            return

        numeric_col = None
        for name in frame.columns:
            series = frame[name]
            if series.dtype in (pl.Int64, pl.Float64, pl.Int32, pl.Float32):
                numeric_col = name
                break
        if numeric_col is None:
            self._hint.setText("数値列が見つかりませんでした。")
            return

        values = frame[numeric_col].drop_nulls().head(max_points).to_list()
        if not values:
            self._hint.setText("プロットするデータがありません。")
            return

        y = [float(v) for v in values]
        self._plot.plot(list(range(len(y))), y, pen=pg.mkPen(color=(30, 120, 200), width=2))
        self._hint.setText(f"{zip_path.name} — 列: {numeric_col} ({len(y)} 点)")
