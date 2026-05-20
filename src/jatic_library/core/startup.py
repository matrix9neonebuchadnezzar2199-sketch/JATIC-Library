"""Windows startup registration (Run key)."""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from typing import Any

APP_RUN_VALUE_NAME = "JATIC-Library"


def _run_key() -> Any:
    import winreg

    return winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
    )


def is_startup_enabled() -> bool:
    """Return True when the app is registered in the current-user Run key."""
    import winreg

    try:
        with _run_key() as key:
            winreg.QueryValueEx(key, APP_RUN_VALUE_NAME)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_startup_enabled(enabled: bool, *, executable: Path | None = None) -> None:
    """Register or remove startup entry for the current user."""
    import winreg

    exe = executable or Path(sys.executable)
    command = f'"{exe}"'

    with _run_key() as key:
        if enabled:
            winreg.SetValueEx(key, APP_RUN_VALUE_NAME, 0, winreg.REG_SZ, command)
        else:
            with contextlib.suppress(FileNotFoundError):
                winreg.DeleteValue(key, APP_RUN_VALUE_NAME)
