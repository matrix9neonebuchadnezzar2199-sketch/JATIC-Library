"""Tests for SQLite repository."""

import sqlite3
from pathlib import Path

import pytest

from jatic_library.core.models import FileRow
from jatic_library.core.repository import Repository


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    r = Repository(tmp_path / "test.db")
    r.connect()
    yield r
    r.close()


def test_connect_and_foreign_keys(repo: Repository) -> None:
    row = repo._conn_required().execute("PRAGMA foreign_keys").fetchone()
    assert row is not None and int(row[0]) == 1


def test_context_manager(tmp_path: Path) -> None:
    with Repository(tmp_path / "ctx.db") as repo:
        repo.upsert_publication("2026_3", "2026-05-01", "pending")
    again = Repository(tmp_path / "ctx.db")
    again.connect()
    assert again.get_publication("2026_3") is not None
    again.close()


def test_migration_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "mig.db"
    first = Repository(path)
    first.connect()
    first.close()
    second = Repository(path)
    second.connect()
    second.close()


def test_publication_upsert_and_complete(repo: Repository) -> None:
    repo.upsert_publication("2026_3", "2026-05-01", "pending")
    first = repo.get_publication("2026_3")
    assert first is not None
    detected = first.detected_at
    repo.upsert_publication("2026_3", "2026-05-01", "complete")
    second = repo.get_publication("2026_3")
    assert second is not None
    assert second.status == "complete"
    assert second.detected_at == detected
    assert repo.is_publication_complete("2026_3") is True
    assert repo.is_publication_complete("2026_9") is False


def test_list_publications_order(repo: Repository) -> None:
    repo.upsert_publication("2026_1", "2026-03-01", "complete")
    repo.upsert_publication("2026_3", "2026-05-01", "complete")
    desc = [p.publish_ym for p in repo.list_publications("DESC")]
    assert desc == ["2026_3", "2026_1"]
    asc = [p.publish_ym for p in repo.list_publications("ASC")]
    assert asc == ["2026_1", "2026_3"]


def _sample_file(publish_ym: str = "2026_3", target: str = "tokyo") -> FileRow:
    return FileRow(
        id=None,
        publish_ym=publish_ym,
        target_code=target,
        display_name="東京都",
        file_path=f"F:/data/{publish_ym}/{target}.zip",
        file_size=100,
        sha256="abc",
        source_url="https://example.test/file.zip",
        downloaded_at="2026-05-01T10:00:00+09:00",
        status="ok",
    )


def test_file_upsert_and_delete(repo: Repository) -> None:
    repo.upsert_publication("2026_3", "2026-05-01", "pending")
    fid = repo.upsert_file(_sample_file())
    got = repo.get_file("2026_3", "tokyo")
    assert got is not None and got.id == fid
    repo.upsert_file(_sample_file())
    fid2 = repo.get_file("2026_3", "tokyo")
    assert fid2 is not None and fid2.id == fid
    assert len(repo.list_files_by_publication("2026_3")) == 1
    repo.delete_file(fid)
    assert repo.get_file("2026_3", "tokyo") is None


def test_list_files_by_target(repo: Repository) -> None:
    repo.upsert_publication("2026_3", "2026-05-01", "complete")
    repo.upsert_publication("2026_2", "2026-04-01", "complete")
    repo.upsert_file(_sample_file("2026_3"))
    repo.upsert_file(_sample_file("2026_2"))
    rows = repo.list_files_by_target("tokyo")
    assert len(rows) == 2


def test_check_history(repo: Repository) -> None:
    repo.add_check_history("no_update", "ok")
    repo.add_check_history("new_found")
    repo.add_check_history("error", None)
    last = repo.get_last_check()
    assert last is not None and last.result == "error"
    recent = repo.list_check_history(limit=2)
    assert len(recent) == 2
    assert recent[0].result == "error"


def test_tags_cascade(repo: Repository) -> None:
    tag_id = repo.create_tag("important", "#ff0000")
    repo.assign_tag(tag_id, "publication", "2026_3")
    tags = repo.list_tags_for("publication", "2026_3")
    assert len(tags) == 1
    assert repo.list_targets_with_tag(tag_id, "publication") == ["2026_3"]
    repo.unassign_tag(tag_id, "publication", "2026_3")
    assert repo.list_tags_for("publication", "2026_3") == []
    repo.delete_tag(tag_id)
    assert repo.list_tags() == []


def test_create_tag_duplicate(repo: Repository) -> None:
    repo.create_tag("dup")
    with pytest.raises(sqlite3.IntegrityError):
        repo.create_tag("dup")


def test_event_logs(repo: Repository) -> None:
    repo.add_event_log("DEBUG", "test", "d1")
    repo.add_event_log("INFO", "test", "i1")
    repo.add_event_log("WARN", "other", "w1")
    repo.add_event_log("ERROR", "test", "e1")
    assert len(repo.list_event_logs(level="INFO")) == 1
    assert len(repo.list_event_logs(category="test")) == 3
    removed = repo.purge_old_logs("9999-12-31T00:00:00+09:00")
    assert removed == 4


def test_list_missing_publications(repo: Repository) -> None:
    repo.upsert_publication("2026_1", "2026-03-01", "complete")
    repo.upsert_publication("2026_3", "2026-05-01", "complete")
    repo.upsert_publication("2026_4", "2026-06-01", "partial")
    missing = repo.list_missing_publications((2026, 1), (2026, 4))
    assert "2026_2" in missing
    assert "2026_4" in missing
    assert "2026_1" not in missing
    assert "2026_3" not in missing


def test_transaction_rollback(repo: Repository) -> None:
    repo.upsert_publication("2026_3", "2026-05-01", "pending")
    with pytest.raises(RuntimeError):
        with repo.transaction():
            repo.upsert_publication("2026_4", "2026-06-01", "pending")
            raise RuntimeError("fail")
    assert repo.get_publication("2026_4") is None


def test_transaction_commit(repo: Repository) -> None:
    with repo.transaction():
        repo.upsert_publication("2026_5", "2026-07-01", "pending")
    assert repo.get_publication("2026_5") is not None
