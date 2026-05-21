"""Tests for download progress dialog."""

from PySide6.QtWidgets import QApplication

from jatic_library.core.downloader import DownloadProgress
from jatic_library.core.publication_postprocess import (
    POSTPROCESS_EXTRACT_CODE,
    POSTPROCESS_MERGE_CODE,
)
from jatic_library.ui.widgets.download_progress_dialog import DownloadProgressDialog


def test_progress_dialog_updates_bar(qapp: QApplication) -> None:
    dialog = DownloadProgressDialog()
    dialog.report(
        DownloadProgress(
            target_code="tokyo",
            bytes_done=50,
            bytes_total=100,
            speed_bps=0.0,
            status="running",
        )
    )
    assert "tokyo" in dialog._bars


def test_progress_dialog_postprocess_bars(qapp: QApplication) -> None:
    dialog = DownloadProgressDialog()
    dialog.report(
        DownloadProgress(
            target_code=POSTPROCESS_EXTRACT_CODE,
            bytes_done=2,
            bytes_total=5,
            speed_bps=0.0,
            status="解凍中: 東京都",
        )
    )
    dialog.report(
        DownloadProgress(
            target_code=POSTPROCESS_MERGE_CODE,
            bytes_done=1,
            bytes_total=1,
            speed_bps=0.0,
            status="CSV結合完了",
        )
    )
    assert POSTPROCESS_EXTRACT_CODE in dialog._bars
    assert POSTPROCESS_MERGE_CODE in dialog._bars
    assert dialog._bars[POSTPROCESS_MERGE_CODE].value() == 100
