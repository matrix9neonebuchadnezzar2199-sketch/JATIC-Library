"""Tests for CLI."""

import pytest

from jatic_library.cli import main


def test_main_no_command_prints_hello(capsys) -> None:
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "Hello from JATIC-Library" in captured.out


def test_main_version(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
