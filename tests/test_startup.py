"""Tests for Windows startup registration."""

import sys
from unittest.mock import MagicMock, patch

from jatic_library.core import startup as startup_mod


def test_startup_command_includes_module_when_not_frozen() -> None:
    mock_key = MagicMock()
    mock_key.__enter__ = MagicMock(return_value=mock_key)
    mock_key.__exit__ = MagicMock(return_value=False)
    with (
        patch.object(sys, "frozen", False, create=True),
        patch.object(sys, "executable", "C:\\Python\\python.exe"),
        patch.object(startup_mod, "_run_key", return_value=mock_key),
        patch("winreg.SetValueEx") as set_value,
        patch("winreg.REG_SZ", 1),
    ):
        startup_mod.set_startup_enabled(True)
    command = set_value.call_args[0][4]
    assert "-m jatic_library" in command


def test_is_startup_enabled_false_when_missing() -> None:
    mock_key = MagicMock()
    with (
        patch.object(startup_mod, "_run_key", return_value=mock_key),
        patch("winreg.QueryValueEx", side_effect=FileNotFoundError),
    ):
        assert startup_mod.is_startup_enabled() is False
