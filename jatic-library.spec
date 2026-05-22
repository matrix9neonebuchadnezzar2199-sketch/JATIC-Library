# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for JATIC-Library (onedir, Chromium bundled)."""

from __future__ import annotations

import sys
from pathlib import Path

import playwright

block_cipher = None
root = Path(SPECPATH)

sys.path.insert(0, str(root / "src"))
from jatic_library import __version__ as APP_VERSION  # noqa: E402

sys.path.pop(0)

playwright_root = Path(playwright.__file__).parent
playwright_driver = playwright_root / "driver"
browser_cache = root / "build" / "browser_cache"

_CHROMIUM_GLOBS = (
    "chromium-*/chrome-win/chrome.exe",
    "chromium-*/chrome-win64/chrome.exe",
)


def _browser_bundle_ready(cache: Path) -> bool:
    if not cache.is_dir():
        return False
    return any(cache.glob(pat) for pat in _CHROMIUM_GLOBS)


if not _browser_bundle_ready(browser_cache):
    raise SystemExit(
        "Chromium bundle missing. Run: uv run python scripts/prepare_browser_bundle.py\n"
        "Or use build.bat which runs this step automatically."
    )

hiddenimports = [
    "pyqtgraph",
    "playwright._impl._driver",
    "playwright.sync_api",
    "playwright.async_api",
    "pydantic",
    "pydantic.deprecated.decorator",
    "pydantic_core",
    "loguru",
    "loguru._defaults",
    "win11toast",
    "zoneinfo",
]

datas = [
    (str(root / "src" / "jatic_library" / "resources"), "jatic_library/resources"),
    (str(root / "src" / "jatic_library" / "ui" / "themes"), "jatic_library/ui/themes"),
    (str(playwright_driver), "playwright/driver"),
    (str(browser_cache), "ms-playwright"),
]

a = Analysis(
    [str(root / "src" / "jatic_library" / "__main__.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JATIC-Library",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="JATIC-Library",
)

_ = APP_VERSION
