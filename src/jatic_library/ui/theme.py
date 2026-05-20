"""Load and apply Qt style sheets."""

from __future__ import annotations

from importlib import resources
from typing import Literal

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QStyleFactory

ThemeName = Literal["light", "dark"]

_UI_FONTS = ["Segoe UI", "Yu Gothic UI", "Meiryo UI", "sans-serif"]


def theme_stylesheet(name: ThemeName) -> str:
    """Return QSS text for *name*."""
    package = "jatic_library.ui.themes"
    filename = f"{name}.qss"
    with resources.files(package).joinpath(filename).open(encoding="utf-8") as handle:
        return handle.read()


def apply_theme(app: QApplication, name: ThemeName) -> None:
    """Apply Fusion base style, UI font, and *name* palette."""
    fusion = QStyleFactory.create("Fusion")
    if fusion is not None:
        app.setStyle(fusion)

    font = QFont()
    font.setFamilies(_UI_FONTS)
    font.setPointSize(10)
    app.setFont(font)
    app.setStyleSheet(theme_stylesheet(name))
