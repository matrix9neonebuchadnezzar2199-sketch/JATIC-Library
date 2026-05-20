"""Repository must use per-thread connections (GUI worker pattern)."""

from __future__ import annotations

import threading
from queue import Queue

from jatic_library.core.repository import Repository


def test_separate_connections_from_worker_thread(tmp_path) -> None:
    """Background QThread pattern: open Repository inside the worker thread."""
    db_path = tmp_path / "thread.db"
    results: Queue[str | None] = Queue()

    def worker() -> None:
        with Repository(db_path) as repo:
            repo.upsert_publication("2026_3", "2026-05-01", "pending")
            pub = repo.get_publication("2026_3")
            results.put(pub.status if pub else None)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert results.get(timeout=1.0) == "pending"
