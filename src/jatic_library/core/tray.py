"""System tray integration."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from jatic_library.settings.config import TraySettings


class TrayController:
    """Optional system tray icon with quick actions."""

    def __init__(
        self,
        settings: TraySettings,
        *,
        on_check_now: Callable[[], None],
        on_show_window: Callable[[], None],
        on_quit: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        self._settings = settings
        self._on_check_now = on_check_now
        self._on_show_window = on_show_window
        self._on_quit = on_quit
        self._tray: QSystemTrayIcon | None = None
        self._parent = parent

    def setup(self) -> bool:
        """Create tray icon when enabled and platform supports it."""
        if not self._settings.enable_tray:
            return False
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return False

        self._tray = QSystemTrayIcon(self._parent)
        self._tray.setToolTip("JATIC-Library")
        style = QApplication.style()
        pixmap = style.StandardPixmap.SP_ComputerIcon
        icon = style.standardIcon(pixmap)
        self._tray.setIcon(icon)

        menu = QMenu()
        show_action = QAction("ウィンドウを表示")
        show_action.triggered.connect(self._on_show_window)
        check_action = QAction("今すぐ更新確認")
        check_action.triggered.connect(self._on_check_now)
        quit_action = QAction("終了")
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(show_action)
        menu.addAction(check_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()
        return True

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_show_window()
