"""Tests for download progress dialog."""

from PySide6.QtWidgets import QApplication

from jatic_library.core.downloader import DownloadProgress
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
