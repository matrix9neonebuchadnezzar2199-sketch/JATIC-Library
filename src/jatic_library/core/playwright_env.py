"""Playwright browser availability checks."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ProgressLine = Callable[[str], None]

INSTALL_COMMAND = "uv run playwright install chromium"

INSTALL_HINT = (
    "Playwright の Chromium が未インストールです。\n\n"
    "プロジェクト直下で次を実行してください:\n"
    f"  {INSTALL_COMMAND}\n\n"
    "完了後、アプリを再起動して更新チェックをやり直してください。"
)

PROXY_HINT = (
    "プロキシ環境下の場合は、コマンドプロンプトで次を設定してから再試行してください:\n"
    "  set HTTPS_PROXY=http://your-proxy:port"
)

_CHROME_EXE_NAMES = ("chrome.exe", "chromium.exe")


def _browsers_cache_dir() -> Path:
    """Default Playwright browser download location on Windows."""
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "ms-playwright"
    return Path.home() / "AppData" / "Local" / "ms-playwright"


def _apply_browsers_env() -> Path:
    """Pin browser cache path for install subprocess and runtime checks."""
    cache = _browsers_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(cache)
    return cache


def _find_chromium_in_cache(cache: Path | None = None) -> Path | None:
    """Locate Chromium under ``ms-playwright`` when Playwright API resolution fails."""
    root = cache or _browsers_cache_dir()
    if not root.is_dir():
        return None
    candidates: list[Path] = []
    for pattern in (
        "chromium-*/chrome-win/chrome.exe",
        "chromium-*/chrome-win64/chrome.exe",
        "chromium_headless_shell-*/chrome-win/chrome.exe",
        "chromium_headless_shell-*/chrome-win64/chrome.exe",
    ):
        candidates.extend(root.glob(pattern))
    existing = [path for path in candidates if path.is_file()]
    if not existing:
        return None
    return max(existing, key=lambda path: path.stat().st_mtime)


def chromium_executable_path() -> Path | None:
    """Return Chromium executable path if Playwright can resolve it."""
    _apply_browsers_env()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _find_chromium_in_cache()

    try:
        with sync_playwright() as playwright:
            raw = playwright.chromium.executable_path
    except Exception:
        return _find_chromium_in_cache()
    if not raw:
        return _find_chromium_in_cache()
    path = Path(raw)
    if path.is_file():
        return path
    return _find_chromium_in_cache()


def chromium_is_ready() -> bool:
    """True when Chromium browser binaries are installed for Playwright."""
    return chromium_executable_path() is not None


def chromium_missing_message() -> str | None:
    """Return a user-facing hint when Chromium is missing, else None."""
    if chromium_is_ready():
        return None
    return INSTALL_HINT


def _subprocess_env(base: dict[str, str] | None) -> dict[str, str]:
    """Build environment for ``playwright install`` with a stable browser cache."""
    cache = _apply_browsers_env()
    env = dict(os.environ)
    if base is not None:
        env.update(base)
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(cache)
    return env


def _popen_kwargs() -> dict[str, object]:
    """Hide console window on Windows when launching the Node installer."""
    if sys.platform != "win32":
        return {}
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if not flags:
        return {}
    return {"creationflags": flags}


def _resolve_install_command() -> tuple[list[str] | None, dict[str, str] | None]:
    """Return (cmd, env) for ``playwright install chromium``.

    Frozen (PyInstaller): bundled node + cli.js via Playwright internal driver.
    Development: ``python -m playwright``.
    """
    if getattr(sys, "frozen", False):
        try:
            from playwright._impl._driver import (
                compute_driver_executable,
                get_driver_env,
            )
        except ImportError:
            return None, None
        try:
            node, cli = compute_driver_executable()
            env = get_driver_env()
        except Exception:
            return None, None
        return [node, cli, "install", "chromium"], env

    return [sys.executable, "-m", "playwright", "install", "chromium"], None


def install_chromium(on_line: ProgressLine | None = None) -> tuple[bool, str]:
    """Run Playwright Chromium installer.

    Args:
        on_line: Optional callback for each stdout line from the installer.

    Returns:
        ``(success, message)`` for UI display.
    """
    cache = _apply_browsers_env()
    cmd, env = _resolve_install_command()
    if cmd is None:
        return False, (
            "Playwright のインストーラを解決できませんでした。\n"
            "Playwright モジュールが正しく同梱されていない可能性があります。"
        )

    if on_line is not None:
        on_line(f"実行: {' '.join(cmd)}")
        on_line(f"保存先: {cache}")

    merged_env = _subprocess_env(env)

    try:
        process = subprocess.Popen(  # noqa: S603 — cmd from _resolve_install_command only
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=merged_env,
            **_popen_kwargs(),
        )
    except OSError as exc:
        return False, f"インストーラ起動失敗: {exc}\n\n{PROXY_HINT}"

    assert process.stdout is not None
    for line in process.stdout:
        if on_line is not None:
            on_line(line.rstrip())

    code = process.wait()
    if on_line is not None:
        on_line(f"終了コード: {code}")

    if code != 0:
        return False, f"インストール失敗 (exit={code})\n\n{PROXY_HINT}"

    _apply_browsers_env()
    cached = _find_chromium_in_cache()
    if chromium_is_ready():
        detail = ""
        if cached is not None:
            detail = f"\n\n検出: {cached}"
        return True, f"Chromium のインストールに成功しました。{detail}"

    return False, (
        "インストール処理は終了しましたが、Chromium を検出できませんでした。\n"
        f"ブラウザキャッシュ: {cache}\n\n"
        "アプリを一度終了して再起動し、再度「はい」でインストールを試してください。\n"
        "それでも失敗する場合は USER_MANUAL の手動手順を参照してください。"
    )


def failures_look_like_missing_browser(
    failed: list[tuple[str, str]],
) -> bool:
    """True when all failure messages indicate missing Playwright browser."""
    if not failed:
        return False
    markers = (
        "Executable doesn't exist",
        "playwright install",
        "BrowserType.launch",
    )
    return all(any(marker in message for marker in markers) for _, message in failed)
