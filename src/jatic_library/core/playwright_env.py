"""Playwright browser availability checks."""

from __future__ import annotations

from pathlib import Path

INSTALL_COMMAND = "uv run playwright install chromium"

INSTALL_HINT = (
    "Playwright の Chromium が未インストールです。\n\n"
    "プロジェクト直下で次を実行してください:\n"
    f"  {INSTALL_COMMAND}\n\n"
    "完了後、アプリを再起動して更新チェックをやり直してください。"
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
