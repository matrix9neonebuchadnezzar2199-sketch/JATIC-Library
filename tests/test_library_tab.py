"""Tests for library tab UI."""

import zipfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from jatic_library.core.manifest import Manifest, ManifestFileEntry
from jatic_library.core.repository import Repository
from jatic_library.settings.config import AppConfig
from jatic_library.ui.tabs.library_tab import LibraryTab


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _seed_library(save_root: Path) -> None:
    folder = save_root / "2026_3"
    folder.mkdir(parents=True)
    zip_path = folder / "東京都.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("traffic.csv", b"hour,volume\n8,100\n")
    Manifest(
        publish_ym="2026_3",
        publish_date="2026-05-01",
        downloaded_at="2026-05-01T10:00:00+09:00",
        source_dir_url="https://example.test/",
        files=[
            ManifestFileEntry(
                target_code="tokyo",
                display_name="東京都",
                filename="東京都.zip",
                source_url="https://example.test/t.zip",
                size=10,
                sha256="deadbeef",
                downloaded_at="2026-05-01T10:00:00+09:00",
            )
        ],
    ).save(folder)


def test_library_tab_builds_tree(qapp: QApplication, tmp_path: Path) -> None:
    save_root = tmp_path / "data"
    _seed_library(save_root)
    config = AppConfig.default()
    config.download.save_root = save_root
    db = tmp_path / "lib.db"
    with Repository(db) as repo:
        tab = LibraryTab(config, repo)
        assert tab._tree.topLevelItemCount() == 1
        year = tab._tree.topLevelItem(0)
        assert year is not None
        assert year.childCount() == 1
        month = year.child(0)
        assert month is not None
        assert month.childCount() == 1
