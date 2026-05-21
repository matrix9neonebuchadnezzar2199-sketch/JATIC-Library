"""QApplication bootstrap and GUI entry."""

from __future__ import annotations

import contextlib
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from jatic_library.constants import APP_DATA_DIR, DB_PATH, LOG_DIR
from jatic_library.paths import default_save_root, normalize_save_root
from jatic_library.core.logger import setup_logging
from jatic_library.core.repository import Repository
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.main_window import MainWindow
from jatic_library.ui.theme import apply_theme


def run_app(*, run_startup_check: bool = True) -> int:
    """Start the PySide6 GUI."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("JATIC-Library")
    app.setOrganizationName("matrix9neonebuchadnezzar2199-sketch")

    store = ConfigStore()
    config = store.load()
    if config.download.save_root and any("pytest-of" in part for part in config.download.save_root.parts):
        config.download.save_root = default_save_root()
        with contextlib.suppress(OSError):
            store.save(config)
    save_root = normalize_save_root(config.download.save_root)
    config.download.save_root = save_root
    save_root.mkdir(parents=True, exist_ok=True)
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    setup_logging(LOG_DIR, config.log)
    apply_theme(app, config.ui.theme)

    try:
        with Repository(DB_PATH) as repo:
            window = MainWindow(
                config,
                store,
                repo,
                run_startup_check=run_startup_check,
            )
            window.show()
            return app.exec()
    except OSError as exc:
        box = QMessageBox()
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("データベース")
        box.setText(f"履歴データベースを開けませんでした:\n{exc}")
        box.exec()
        return 1
