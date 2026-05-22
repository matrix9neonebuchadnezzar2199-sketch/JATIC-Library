# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for JATIC-Library (onedir)."""

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

hiddenimports = [
    "pyqtgraph",
    # Playwright internal driver (INST_27 frozen install path)
    "playwright._impl._driver",
    "playwright.sync_api",
    "playwright.async_api",
    # Pydantic v2
    "pydantic",
    "pydantic.deprecated.decorator",
    "pydantic_core",
    # Loguru
    "loguru",
    "loguru._defaults",
    # Windows toast
    "win11toast",
    "zoneinfo",
]

datas = [
    (str(root / "src" / "jatic_library" / "resources"), "jatic_library/resources"),
    (str(root / "src" / "jatic_library" / "ui" / "themes"), "jatic_library/ui/themes"),
    (str(playwright_driver), "playwright/driver"),
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

# APP_VERSION is read by build.bat via `from jatic_library import __version__`
_ = APP_VERSION
