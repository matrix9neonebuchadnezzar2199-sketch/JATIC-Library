"""Entry point: python -m jatic_library."""

from jatic_library import __app_name__, __version__


def main() -> int:
    """Temporary CLI entry until instruction #09 wires PySide6."""
    print(f"Hello from {__app_name__} v{__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
