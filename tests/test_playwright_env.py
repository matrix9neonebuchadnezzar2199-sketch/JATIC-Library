"""Tests for Playwright environment helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from jatic_library.core.playwright_env import (
    INSTALL_HINT,
    _find_chromium_in_cache,
    chromium_is_ready,
    chromium_missing_message,
    failures_look_like_missing_browser,
    install_chromium,
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


def test_find_chromium_in_cache(tmp_path: Path) -> None:
    chrome_dir = tmp_path / "chromium-1234" / "chrome-win"
    chrome_dir.mkdir(parents=True)
    exe = chrome_dir / "chrome.exe"
    exe.write_bytes(b"x")
    assert _find_chromium_in_cache(tmp_path) == exe


def test_install_success_when_cache_has_chrome_after_exit_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chrome_dir = tmp_path / "chromium-9999" / "chrome-win"
    chrome_dir.mkdir(parents=True)
    exe = chrome_dir / "chrome.exe"
    exe.write_bytes(b"x")

    class FakeProcess:
        stdout = iter(["Downloading\n", "done\n"])

        def wait(self) -> int:
            return 0

    monkeypatch.setattr(
        "jatic_library.core.playwright_env._resolve_install_command",
        lambda: (["fake"], None),
    )
    monkeypatch.setattr(
        "jatic_library.core.playwright_env._browsers_cache_dir",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "jatic_library.core.playwright_env.subprocess.Popen",
        lambda *args, **kwargs: FakeProcess(),
    )
    monkeypatch.setattr(
        "jatic_library.core.playwright_env.chromium_executable_path",
        lambda: exe,
    )

    ok, message = install_chromium()
    assert ok is True
    assert "成功" in message


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
