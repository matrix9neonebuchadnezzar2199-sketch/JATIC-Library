"""Download Chromium into ``build/browser_cache`` for PyInstaller bundling."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "browser_cache"


def _chromium_present(root: Path) -> bool:
    patterns = (
        "chromium-*/chrome-win/chrome.exe",
        "chromium-*/chrome-win64/chrome.exe",
    )
    return any(root.glob(pat) for pat in patterns)


def main() -> int:
    """Install Playwright Chromium into the build-only cache directory."""
    if CACHE.is_dir():
        shutil.rmtree(CACHE)
    CACHE.mkdir(parents=True)

    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(CACHE)
    cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
    print(f"Running: {' '.join(cmd)}")
    print(f"Target: {CACHE}")
    code = subprocess.call(cmd, env=env)  # noqa: S603
    if code != 0:
        print(f"[ERROR] playwright install failed (exit={code})", file=sys.stderr)
        return code
    if not _chromium_present(CACHE):
        print("[ERROR] chromium-*/chrome.exe not found under browser_cache", file=sys.stderr)
        return 1
    total = sum(f.stat().st_size for f in CACHE.rglob("*") if f.is_file())
    print(f"Bundle ready: {total / (1024 * 1024):.1f} MB under {CACHE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
