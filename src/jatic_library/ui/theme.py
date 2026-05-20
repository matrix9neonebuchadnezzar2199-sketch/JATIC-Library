"""Load and apply Qt style sheets."""

from __future__ import annotations

from importlib import resources
from typing import Literal

from PySide6.QtWidgets import QApplication

ThemeName = Literal["light", "dark"]


def theme_stylesheet(name: ThemeName) -> str:
    """Return QSS text for *name*."""
    package = "jatic_library.ui.themes"
    filename = f"{name}.qss"
    with resources.files(package).joinpath(filename).open(encoding="utf-8") as handle:
        return handle.read()


def apply_theme(app: QApplication, name: ThemeName) -> None:
    """Apply *name* theme to *app*."""
    app.setStyleSheet(theme_stylesheet(name))
