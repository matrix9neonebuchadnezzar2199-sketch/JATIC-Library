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
    "開発環境では次を実行してください:\n"
    f"  {INSTALL_COMMAND}\n\n"
    "配布版 exe では Chromium が同梱されている必要があります。"
)

PROXY_HINT = (
    "プロキシ環境下の場合は、コマンドプロンプトで次を設定してから再試行してください:\n"
    "  set HTTPS_PROXY=http://your-proxy:port"
)

_CHROMIUM_GLOB_PATTERNS = (
    "chromium-*/chrome-win/chrome.exe",
    "chromium-*/chrome-win64/chrome.exe",
    "chromium_headless_shell-*/chrome-win/chrome.exe",
    "chromium_headless_shell-*/chrome-win64/chrome.exe",
)


def _user_browsers_cache_dir() -> Path:
    """Per-user Playwright browser download location (development / fallback)."""
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "ms-playwright"
    return Path.home() / "AppData" / "Local" / "ms-playwright"


def _bundled_browsers_dir() -> Path | None:
    """Return ``_internal/ms-playwright`` when the frozen build ships Chromium."""
    if not getattr(sys, "frozen", False):
        return None
    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return None
    root = Path(meipass) / "ms-playwright"
    if _find_chromium_in_cache(root) is None:
        return None
    return root


def configure_playwright_runtime() -> Path:
    """Set ``PLAYWRIGHT_BROWSERS_PATH`` before any Playwright import (call at startup)."""
    bundled = _bundled_browsers_dir()
    if bundled is not None:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(bundled)
        return bundled
    cache = _user_browsers_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(cache)
    return cache


def chromium_is_bundled() -> bool:
    """True when running a frozen build that includes Chromium under ``_internal``."""
    return _bundled_browsers_dir() is not None


def _active_browsers_dir() -> Path:
    """Currently configured browser cache (bundled or per-user)."""
    bundled = _bundled_browsers_dir()
    if bundled is not None:
        return bundled
    return _user_browsers_cache_dir()


def _find_chromium_in_cache(cache: Path | None = None) -> Path | None:
    """Locate Chromium under a ``ms-playwright``-style directory tree."""
    root = cache if cache is not None else _active_browsers_dir()
    if not root.is_dir():
        return None
    candidates: list[Path] = []
    for pattern in _CHROMIUM_GLOB_PATTERNS:
        candidates.extend(root.glob(pattern))
    existing = [path for path in candidates if path.is_file()]
    if not existing:
        return None
    return max(existing, key=lambda path: path.stat().st_mtime)


def chromium_executable_path() -> Path | None:
    """Return Chromium executable path if Playwright can resolve it."""
    configure_playwright_runtime()
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
    if chromium_is_bundled():
        cache = _bundled_browsers_dir()
        assert cache is not None
    else:
        cache = configure_playwright_runtime()
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
    """Run Playwright Chromium installer (development / repair only when not bundled).

    Args:
        on_line: Optional callback for each stdout line from the installer.

    Returns:
        ``(success, message)`` for UI display.
    """
    if chromium_is_bundled():
        exe = _find_chromium_in_cache()
        detail = f"\n\n同梱: {exe}" if exe else ""
        return True, f"Chromium は配布物に同梱されています。{detail}"

    cache = configure_playwright_runtime()
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

    configure_playwright_runtime()
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
