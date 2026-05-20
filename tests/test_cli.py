"""Tests for CLI."""

import pytest

from jatic_library.cli import build_parser, main


def test_build_parser_has_subcommands() -> None:
    parser = build_parser()
    assert parser.parse_args(["check"]).command == "check"


def test_main_version(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
