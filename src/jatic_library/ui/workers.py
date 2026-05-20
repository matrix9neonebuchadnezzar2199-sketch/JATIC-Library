"""Background workers for asyncio tasks."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from PySide6.QtCore import QObject, QThread, Signal

T = TypeVar("T")


class AsyncTaskWorker(QThread):
    """Run an asyncio coroutine factory on a background thread."""

    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        coro_factory: Callable[[], Coroutine[Any, Any, T]],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._coro_factory = coro_factory

    def run(self) -> None:
        try:
            result = asyncio.run(self._coro_factory())
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished_ok.emit(result)
