"""Initial Chromium setup wizard."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from jatic_library.core.playwright_env import install_chromium


class _InstallWorker(QObject):
    """Run ``install_chromium`` off the GUI thread."""

    line_received = Signal(str)
    finished = Signal(bool, str)

    def run(self) -> None:
        ok, message = install_chromium(on_line=self.line_received.emit)
        self.finished.emit(ok, message)


class PlaywrightSetupDialog(QDialog):
    """Ask user to install Chromium, then run it in a background thread."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Playwright Chromium のセットアップ")
        self.resize(560, 360)
        self._result_ok = False

        layout = QVBoxLayout(self)
        self._label = QLabel(
            "サイト再スキャンや 404 自動再取得には Chromium が必要です。\n"
            "今すぐインストールしますか？（約 200MB をダウンロード）"
        )
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setVisible(False)
        layout.addWidget(self._log)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No
        )
        self._buttons.accepted.connect(self._start_install)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        self._thread: QThread | None = None
        self._worker: _InstallWorker | None = None

    def install_succeeded(self) -> bool:
        """True if Chromium became available during this dialog session."""
        return self._result_ok

    def _start_install(self) -> None:
        self._buttons.setEnabled(False)
        self._label.setText("Chromium をインストールしています…（数分かかることがあります）")
        self._log.clear()
        self._log.setVisible(True)

        self._thread = QThread(self)
        self._worker = _InstallWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.line_received.connect(self._log.appendPlainText)
        self._worker.finished.connect(self._on_finished)
        self._thread.start()

    def _on_finished(self, ok: bool, message: str) -> None:
        self._result_ok = ok
        status = "完了" if ok else "失敗"
        self._label.setText(f"【{status}】\n{message}")
        self._log.appendPlainText("")
        self._log.appendPlainText(f"--- {status} ---")
        self._log.appendPlainText(message)

        if ok:
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.clicked.connect(self.accept)
        else:
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Retry | QDialogButtonBox.StandardButton.Close
            )
            buttons.button(QDialogButtonBox.StandardButton.Retry).clicked.connect(
                self._retry_install
            )
            buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.reject)

        layout = self.layout()
        assert isinstance(layout, QVBoxLayout)
        layout.replaceWidget(self._buttons, buttons)
        self._buttons.deleteLater()
        self._buttons = buttons

        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        self._worker = None

    def _retry_install(self) -> None:
        """Re-run installer after a failed attempt."""
        self._start_install()
