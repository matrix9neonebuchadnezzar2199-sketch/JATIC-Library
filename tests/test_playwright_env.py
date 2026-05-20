"""Tests for Playwright environment helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jatic_library.core.playwright_env import (
    INSTALL_HINT,
    chromium_is_ready,
    chromium_missing_message,
    failures_look_like_missing_browser,
)


def test_chromium_missing_message_when_not_ready() -> None:
    with patch(
        "jatic_library.core.playwright_env.chromium_executable_path",
        return_value=None,
    ):
        assert chromium_is_ready() is False
        assert chromium_missing_message() == INSTALL_HINT


def test_chromium_missing_message_when_ready(tmp_path: Path) -> None:
    exe = tmp_path / "chrome.exe"
    exe.write_bytes(b"")
    with patch(
        "jatic_library.core.playwright_env.chromium_executable_path",
        return_value=exe,
    ):
        assert chromium_missing_message() is None


def test_failures_look_like_missing_browser() -> None:
    failed = [
        (
            "tochigi",
            "BrowserType.launch: Executable doesn't exist at C:\\path\\chrome.exe",
        ),
    ]
    assert failures_look_like_missing_browser(failed) is True
    assert failures_look_like_missing_browser([("x", "HTTP 500")]) is False
    assert failures_look_like_missing_browser([]) is False
