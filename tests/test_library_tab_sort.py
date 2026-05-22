"""Tests for LibraryTab sort debounce and persistence."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from jatic_library.core.repository import Repository
from jatic_library.settings.config import AppConfig
from jatic_library.ui.tabs.library_tab import LibraryTab


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def library_tab(qapp: QApplication, tmp_path: Path) -> LibraryTab:
    save_root = tmp_path / "data"
    save_root.mkdir(parents=True, exist_ok=True)
    config = AppConfig.default()
    config.download.save_root = save_root
    db = tmp_path / "sort.db"
    repo = Repository(db)
    repo.connect()
    tab = LibraryTab(config, repo)
    yield tab
    repo.close()


def _index_for_key(tab: LibraryTab, sort_key: str) -> int:
    for index in range(tab._sort.count()):
        if tab._sort.itemData(index) == sort_key:
            return index
    raise AssertionError(f"sort key not found: {sort_key}")


def test_sort_changed_same_value_no_emit(library_tab: LibraryTab) -> None:
    library_tab._config.ui.library_default_sort = "date_desc"
    spy = QSignalSpy(library_tab.sort_changed)

    library_tab._sort.setCurrentIndex(_index_for_key(library_tab, "date_desc"))
    QTest.qWait(400)

    assert spy.count() == 0


def test_sort_changed_debounce_collapses_to_one_emit(library_tab: LibraryTab) -> None:
    spy = QSignalSpy(library_tab.sort_changed)

    library_tab._sort.setCurrentIndex(_index_for_key(library_tab, "date_asc"))
    library_tab._sort.setCurrentIndex(_index_for_key(library_tab, "name"))
    library_tab._sort.setCurrentIndex(_index_for_key(library_tab, "date_desc"))
    QTest.qWait(400)

    assert spy.count() == 1
    assert spy.at(0)[0] == "date_desc"


def test_sort_changed_flush_on_quit(library_tab: LibraryTab) -> None:
    spy = QSignalSpy(library_tab.sort_changed)

    library_tab._sort.setCurrentIndex(_index_for_key(library_tab, "name"))
    assert library_tab._sort_persist_timer.isActive()

    library_tab.flush_pending_sort()

    assert spy.count() == 1
    assert spy.at(0)[0] == "name"
    assert not library_tab._sort_persist_timer.isActive()


def test_refresh_does_not_trigger_debounce(library_tab: LibraryTab) -> None:
    library_tab._sort.setCurrentIndex(_index_for_key(library_tab, "name"))
    QTest.qWait(400)
    assert not library_tab._sort_persist_timer.isActive()

    library_tab.refresh()
    assert not library_tab._sort_persist_timer.isActive()
