"""Background computation of library file row counts and sizes."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from shiboken6 import isValid

from jatic_library.core.library_scan_cache import set_cached_stats
from jatic_library.core.library_scanner import compute_file_stats


class LibraryStatsBridge(QObject):
    """Relay stats from worker threads to the UI thread."""

    stats_ready = Signal(int, str, int, int)
    """generation, path_str, row_count (or -1 if None), display_size"""


class FileStatsRunnable(QRunnable):
    """Compute stats for one file path off the UI thread."""

    def __init__(
        self,
        bridge: LibraryStatsBridge,
        generation: int,
        path: Path,
    ) -> None:
        super().__init__()
        self._bridge = bridge
        self._generation = generation
        self._path = path

    def run(self) -> None:
        row_count, display_size = compute_file_stats(self._path)
        if self._path.suffix.lower() == ".zip":
            set_cached_stats(
                self._path,
                row_count=row_count,
                uncompressed_csv_size=display_size,
            )
        else:
            try:
                plain_size = self._path.stat().st_size
            except OSError:
                plain_size = display_size
            set_cached_stats(
                self._path,
                row_count=row_count,
                uncompressed_csv_size=plain_size,
            )
        if not isValid(self._bridge):
            return
        row_signal = -1 if row_count is None else row_count
        self._bridge.stats_ready.emit(self._generation, str(self._path), row_signal, display_size)


def enqueue_file_stats(
    bridge: LibraryStatsBridge,
    generation: int,
    paths: list[Path],
) -> None:
    """Schedule background stats jobs on the global thread pool."""
    pool = QThreadPool.globalInstance()
    for path in paths:
        pool.start(FileStatsRunnable(bridge, generation, path))
