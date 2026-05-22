"""Playwright browser availability checks."""

from __future__ import annotations

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


def chromium_executable_path() -> Path | None:
    """Return Chromium executable path if Playwright can resolve it."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    try:
        with sync_playwright() as playwright:
            raw = playwright.chromium.executable_path
    except Exception:
        return None
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_file() else None


def chromium_is_ready() -> bool:
    """True when Chromium browser binaries are installed for Playwright."""
    return chromium_executable_path() is not None


def chromium_missing_message() -> str | None:
    """Return a user-facing hint when Chromium is missing, else None."""
    if chromium_is_ready():
        return None
    return INSTALL_HINT


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
    cmd, env = _resolve_install_command()
    if cmd is None:
        return False, (
            "Playwright のインストーラを解決できませんでした。\n"
            "Playwright モジュールが正しく同梱されていない可能性があります。"
        )

    try:
        process = subprocess.Popen(  # noqa: S603 — cmd from _resolve_install_command only
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
    except OSError as exc:
        return False, f"インストーラ起動失敗: {exc}\n\n{PROXY_HINT}"

    assert process.stdout is not None
    for line in process.stdout:
        if on_line is not None:
            on_line(line.rstrip())

    code = process.wait()
    if code != 0:
        return False, f"インストール失敗 (exit={code})\n\n{PROXY_HINT}"
    if not chromium_is_ready():
        return False, "インストール完了報告は出ましたが Chromium が検出できません。"
    return True, "Chromium のインストールに成功しました。"


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
