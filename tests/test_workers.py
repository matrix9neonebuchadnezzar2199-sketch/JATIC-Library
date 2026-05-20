"""Tests for background asyncio workers."""

import time

import pytest
from PySide6.QtWidgets import QApplication

from jatic_library.ui.workers import AsyncTaskWorker


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _wait_for_worker(
    worker: AsyncTaskWorker,
    qapp: QApplication,
    *,
    timeout_sec: float = 5.0,
) -> None:
    deadline = time.monotonic() + timeout_sec
    while worker.isRunning() and time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()


def test_worker_emits_result(qapp: QApplication) -> None:
    async def coro() -> str:
        return "ok"

    worker = AsyncTaskWorker(coro)
    results: list[object] = []
    worker.finished_ok.connect(results.append)
    worker.start()
    _wait_for_worker(worker, qapp)
    assert results == ["ok"]


def test_worker_emits_failure(qapp: QApplication) -> None:
    async def coro() -> None:
        raise RuntimeError("boom")

    worker = AsyncTaskWorker(coro)
    errors: list[str] = []
    worker.failed.connect(errors.append)
    worker.start()
    _wait_for_worker(worker, qapp)
    assert errors and "boom" in errors[0]
