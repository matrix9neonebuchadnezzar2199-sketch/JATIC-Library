"""Tests for MainWindow._on_delete_file ordering and idempotency."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from jatic_library.core.library_scanner import LibraryFileItem
from jatic_library.core.models import FileRow
from jatic_library.core.repository import Repository
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore
from jatic_library.ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _sample_item(
    tmp_path: Path,
    *,
    target_code: str | None = "tokyo",
) -> LibraryFileItem:
    folder = tmp_path / "2026_3"
    folder.mkdir(parents=True, exist_ok=True)
    file_path = folder / ("merged.csv" if target_code is None else "tokyo.zip")
    file_path.write_bytes(b"data")
    return LibraryFileItem(
        publish_ym="2026_3",
        file_name=file_path.name,
        file_path=file_path,
        display_name="東京都" if target_code else "統合.csv",
        target_code=target_code,
        file_size=4,
        sha256=None,
        source_url=None,
        downloaded_at=None,
    )


def _sample_row(item: LibraryFileItem) -> FileRow:
    return FileRow(
        id=1,
        publish_ym=item.publish_ym,
        target_code=item.target_code or "tokyo",
        display_name=item.display_name,
        file_path=str(item.file_path),
        file_size=item.file_size,
        sha256="abc",
        source_url="https://example.test/t.zip",
        downloaded_at="2026-05-01T10:00:00+09:00",
        status="ok",
    )


@pytest.fixture
def main_window(qapp: QApplication, tmp_path: Path) -> MainWindow:
    db = tmp_path / "test.db"
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    store = ConfigStore(tmp_path / "cfg.json")
    repo = Repository(db)
    repo.connect()
    window = MainWindow(config, store, repo, run_startup_check=False)
    yield window
    repo.close()


def test_delete_calls_db_before_manifest_before_file(
    main_window: MainWindow,
    tmp_path: Path,
) -> None:
    item = _sample_item(tmp_path)
    call_order: list[str] = []
    row = _sample_row(item)

    with (
        patch.object(main_window._repo, "get_file", return_value=row) as mock_get,
        patch.object(
            main_window._repo,
            "delete_file",
            side_effect=lambda _fid: call_order.append("db"),
        ) as mock_delete,
        patch.object(main_window._repo, "delete_tag_assignments") as mock_tags,
        patch("jatic_library.ui.main_window.Manifest.load") as mock_load,
        patch.object(Path, "unlink", side_effect=lambda **_kw: call_order.append("file")),
    ):
        manifest = MagicMock()
        mock_load.return_value = manifest
        manifest.remove_file.side_effect = lambda _code: call_order.append("manifest")
        manifest.save.side_effect = lambda _folder: call_order.append("manifest_save")

        main_window._on_delete_file(item)

    mock_get.assert_called_once()
    mock_delete.assert_called_once_with(1)
    mock_tags.assert_called_once_with("file", "2026_3/tokyo")
    assert call_order.index("db") < call_order.index("manifest")
    assert call_order.index("manifest") < call_order.index("file")


def test_delete_missing_file_is_idempotent(main_window: MainWindow, tmp_path: Path) -> None:
    item = _sample_item(tmp_path)
    row = _sample_row(item)

    with (
        patch.object(main_window._repo, "get_file", return_value=row),
        patch.object(main_window._repo, "delete_file"),
        patch("jatic_library.ui.main_window.Manifest.load", return_value=None),
        patch.object(Path, "unlink"),
        patch.object(main_window, "_refresh_data_tabs") as mock_refresh,
    ):
        main_window._on_delete_file(item)
        main_window._on_delete_file(item)

    assert mock_refresh.call_count == 2


def test_delete_skips_db_when_target_code_is_none(
    main_window: MainWindow,
    tmp_path: Path,
) -> None:
    item = _sample_item(tmp_path, target_code=None)
    call_order: list[str] = []

    with (
        patch.object(main_window._repo, "get_file") as mock_get,
        patch.object(
            main_window._repo,
            "delete_file",
            side_effect=lambda _fid: call_order.append("db"),
        ) as mock_delete,
        patch("jatic_library.ui.main_window.Manifest.load") as mock_load,
        patch.object(Path, "unlink", side_effect=lambda **_kw: call_order.append("file")),
    ):
        main_window._on_delete_file(item)

    mock_get.assert_not_called()
    mock_delete.assert_not_called()
    mock_load.assert_not_called()
    assert call_order == ["file"]


def test_delete_partial_failure_continues(main_window: MainWindow, tmp_path: Path) -> None:
    item = _sample_item(tmp_path)
    call_order: list[str] = []
    row = _sample_row(item)

    with (
        patch.object(main_window._repo, "get_file", return_value=row),
        patch.object(
            main_window._repo,
            "delete_file",
            side_effect=sqlite3.OperationalError("db fail"),
        ),
        patch("jatic_library.ui.main_window.Manifest.load") as mock_load,
        patch.object(Path, "unlink", side_effect=lambda **_kw: call_order.append("file")),
    ):
        manifest = MagicMock()
        mock_load.return_value = manifest
        manifest.remove_file.side_effect = lambda _code: call_order.append("manifest")
        manifest.save.side_effect = lambda _folder: call_order.append("manifest_save")

        main_window._on_delete_file(item)

    assert "manifest" in call_order
    assert "file" in call_order


def test_delete_merged_csv_removes_tag_assignments(
    main_window: MainWindow,
    tmp_path: Path,
) -> None:
    folder = tmp_path / "2026_3"
    folder.mkdir(parents=True, exist_ok=True)
    merged_path = folder / "統合.csv"
    merged_path.write_bytes(b"col\n1\n")
    item = LibraryFileItem(
        publish_ym="2026_3",
        file_name=merged_path.name,
        file_path=merged_path,
        display_name="統合CSV",
        target_code="merged",
        file_size=8,
        sha256=None,
        source_url=None,
        downloaded_at=None,
    )
    tag_id = main_window._repo.create_tag("merged-tag")
    main_window._repo.assign_tag(tag_id, "file", "2026_3/merged")

    with (
        patch.object(main_window._repo, "get_file", return_value=None),
        patch.object(main_window._repo, "delete_file") as mock_delete,
        patch("jatic_library.ui.main_window.Manifest.load", return_value=None),
        patch.object(Path, "unlink"),
    ):
        main_window._on_delete_file(item)

    mock_delete.assert_not_called()
    assert main_window._repo.list_tags_for("file", "2026_3/merged") == []
