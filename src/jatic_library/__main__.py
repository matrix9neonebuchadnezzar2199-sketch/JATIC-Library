"""Entry point: python -m jatic_library."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    """Launch GUI when no args; otherwise delegate to CLI."""
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        from jatic_library.app import run_app

        return run_app()
    from jatic_library.cli import main as cli_main

    return cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
