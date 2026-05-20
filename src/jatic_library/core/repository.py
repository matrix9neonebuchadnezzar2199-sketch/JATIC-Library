"""SQLite persistence for downloads and tags."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal, cast
from zoneinfo import ZoneInfo

from jatic_library.constants import DB_PATH, TZ_JST
from jatic_library.core.models import (
    CheckHistoryRow,
    CheckResult,
    EventLogRow,
    FileRow,
    FileStatus,
    PublicationRow,
    PublicationStatus,
    TagRow,
    TagScope,
)
from jatic_library.core.url_builder import parse_folder_name

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publications (
  publish_ym       TEXT PRIMARY KEY,
  publish_date     TEXT NOT NULL,
  detected_at      TEXT NOT NULL,
  status           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  publish_ym       TEXT NOT NULL,
  target_code      TEXT NOT NULL,
  display_name     TEXT NOT NULL,
  file_path        TEXT NOT NULL,
  file_size        INTEGER NOT NULL,
  sha256           TEXT NOT NULL,
  source_url       TEXT NOT NULL,
  downloaded_at    TEXT NOT NULL,
  status           TEXT NOT NULL,
  UNIQUE(publish_ym, target_code),
  FOREIGN KEY(publish_ym) REFERENCES publications(publish_ym)
);

CREATE INDEX IF NOT EXISTS idx_files_publish_ym ON files(publish_ym);
CREATE INDEX IF NOT EXISTS idx_files_target_code ON files(target_code);

CREATE TABLE IF NOT EXISTS check_history (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  checked_at       TEXT NOT NULL,
  result           TEXT NOT NULL,
  detail           TEXT
);

CREATE INDEX IF NOT EXISTS idx_check_history_checked_at ON check_history(checked_at DESC);

CREATE TABLE IF NOT EXISTS tags (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  name             TEXT UNIQUE NOT NULL,
  color            TEXT
);

CREATE TABLE IF NOT EXISTS tag_assignments (
  tag_id           INTEGER NOT NULL,
  scope            TEXT NOT NULL,
  scope_key        TEXT NOT NULL,
  PRIMARY KEY(tag_id, scope, scope_key),
  FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_logs (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  ts               TEXT NOT NULL,
  level            TEXT NOT NULL,
  category         TEXT NOT NULL,
  message          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_event_logs_ts ON event_logs(ts DESC);
"""


def now_jst_iso() -> str:
    """Return current time in JST as ISO8601 seconds precision."""
    return datetime.now(ZoneInfo(TZ_JST)).isoformat(timespec="seconds")


class Repository:
    """SQLite access layer."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Open connection and apply schema migrations."""
        # GUI の QThread ワーカーは別スレッドで接続を開く。共有接続時の保険として無効化。
        self._conn = sqlite3.connect(
            str(self.db_path),
            isolation_level=None,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "Repository":
        self.connect()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run statements in an explicit transaction."""
        if self._conn is None:
            raise RuntimeError("Repository not connected")
        self._conn.execute("BEGIN")
        try:
            yield self._conn
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def _conn_required(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Repository not connected")
        return self._conn

    def _migrate(self) -> None:
        conn = self._conn_required()
        conn.executescript(SCHEMA_SQL)
        row = conn.execute("SELECT value FROM schema_meta WHERE key='version'").fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO schema_meta(key, value) VALUES('version', ?)",
                (str(SCHEMA_VERSION),),
            )

    def upsert_publication(
        self,
        publish_ym: str,
        publish_date: str,
        status: PublicationStatus,
    ) -> None:
        """Insert or update a publication row."""
        conn = self._conn_required()
        now = now_jst_iso()
        conn.execute(
            """
            INSERT INTO publications(publish_ym, publish_date, detected_at, status)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(publish_ym) DO UPDATE SET
              publish_date=excluded.publish_date,
              status=excluded.status
            """,
            (publish_ym, publish_date, now, status),
        )

    def get_publication(self, publish_ym: str) -> PublicationRow | None:
        """Fetch one publication row."""
        conn = self._conn_required()
        row = conn.execute(
            "SELECT * FROM publications WHERE publish_ym = ?",
            (publish_ym,),
        ).fetchone()
        if row is None:
            return None
        return PublicationRow(
            publish_ym=str(row["publish_ym"]),
            publish_date=str(row["publish_date"]),
            detected_at=str(row["detected_at"]),
            status=cast(PublicationStatus, row["status"]),
        )

    def list_publications(self, order: Literal["ASC", "DESC"] = "DESC") -> list[PublicationRow]:
        """List publications ordered by publish_ym."""
        conn = self._conn_required()
        direction = "DESC" if order.upper() == "DESC" else "ASC"
        rows = conn.execute(
            f"SELECT * FROM publications ORDER BY publish_ym {direction}"
        ).fetchall()
        return [
            PublicationRow(
                publish_ym=str(r["publish_ym"]),
                publish_date=str(r["publish_date"]),
                detected_at=str(r["detected_at"]),
                status=cast(PublicationStatus, r["status"]),
            )
            for r in rows
        ]

    def is_publication_complete(self, publish_ym: str) -> bool:
        """Return True when publication status is complete."""
        pub = self.get_publication(publish_ym)
        return pub is not None and pub.status == "complete"

    def upsert_file(self, row: FileRow) -> int:
        """Insert or update a file row and return its id."""
        conn = self._conn_required()
        conn.execute(
            """
            INSERT INTO files(
              publish_ym, target_code, display_name, file_path, file_size,
              sha256, source_url, downloaded_at, status
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(publish_ym, target_code) DO UPDATE SET
              display_name=excluded.display_name,
              file_path=excluded.file_path,
              file_size=excluded.file_size,
              sha256=excluded.sha256,
              source_url=excluded.source_url,
              downloaded_at=excluded.downloaded_at,
              status=excluded.status
            """,
            (
                row.publish_ym,
                row.target_code,
                row.display_name,
                row.file_path,
                row.file_size,
                row.sha256,
                row.source_url,
                row.downloaded_at,
                row.status,
            ),
        )
        file_id = conn.execute(
            "SELECT id FROM files WHERE publish_ym = ? AND target_code = ?",
            (row.publish_ym, row.target_code),
        ).fetchone()
        assert file_id is not None
        return int(file_id["id"])

    def get_file(self, publish_ym: str, target_code: str) -> FileRow | None:
        """Fetch one file row."""
        conn = self._conn_required()
        row = conn.execute(
            "SELECT * FROM files WHERE publish_ym = ? AND target_code = ?",
            (publish_ym, target_code),
        ).fetchone()
        return self._row_to_file(row) if row else None

    def list_files_by_publication(self, publish_ym: str) -> list[FileRow]:
        """List files for a publication month."""
        conn = self._conn_required()
        rows = conn.execute(
            "SELECT * FROM files WHERE publish_ym = ? ORDER BY target_code",
            (publish_ym,),
        ).fetchall()
        return [self._row_to_file(r) for r in rows]

    def list_files_by_target(self, target_code: str) -> list[FileRow]:
        """List files for a target across months."""
        conn = self._conn_required()
        rows = conn.execute(
            "SELECT * FROM files WHERE target_code = ? ORDER BY publish_ym DESC",
            (target_code,),
        ).fetchall()
        return [self._row_to_file(r) for r in rows]

    def delete_file(self, file_id: int) -> None:
        """Delete a file row by id."""
        self._conn_required().execute("DELETE FROM files WHERE id = ?", (file_id,))

    def add_check_history(self, result: CheckResult, detail: str | None = None) -> int:
        """Append a check history row."""
        conn = self._conn_required()
        cur = conn.execute(
            "INSERT INTO check_history(checked_at, result, detail) VALUES(?, ?, ?)",
            (now_jst_iso(), result, detail),
        )
        last_id = cur.lastrowid
        assert last_id is not None
        return int(last_id)

    def get_last_check(self) -> CheckHistoryRow | None:
        """Return the most recent check history row."""
        conn = self._conn_required()
        row = conn.execute(
            "SELECT * FROM check_history ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return CheckHistoryRow(
            id=int(row["id"]),
            checked_at=str(row["checked_at"]),
            result=cast(CheckResult, row["result"]),
            detail=row["detail"],
        )

    def list_check_history(self, limit: int = 100) -> list[CheckHistoryRow]:
        """List recent check history rows."""
        conn = self._conn_required()
        rows = conn.execute(
            "SELECT * FROM check_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            CheckHistoryRow(
                id=int(r["id"]),
                checked_at=str(r["checked_at"]),
                result=cast(CheckResult, r["result"]),
                detail=r["detail"],
            )
            for r in rows
        ]

    def create_tag(self, name: str, color: str | None = None) -> int:
        """Create a tag and return its id."""
        cur = self._conn_required().execute(
            "INSERT INTO tags(name, color) VALUES(?, ?)",
            (name, color),
        )
        tag_id = cur.lastrowid
        assert tag_id is not None
        return int(tag_id)

    def list_tags(self) -> list[TagRow]:
        """List all tags."""
        rows = self._conn_required().execute(
            "SELECT * FROM tags ORDER BY name"
        ).fetchall()
        return [
            TagRow(id=int(r["id"]), name=str(r["name"]), color=r["color"]) for r in rows
        ]

    def delete_tag(self, tag_id: int) -> None:
        """Delete a tag (assignments cascade)."""
        self._conn_required().execute("DELETE FROM tags WHERE id = ?", (tag_id,))

    def assign_tag(self, tag_id: int, scope: TagScope, scope_key: str) -> None:
        """Assign a tag to a scope."""
        self._conn_required().execute(
            "INSERT OR IGNORE INTO tag_assignments(tag_id, scope, scope_key) VALUES(?, ?, ?)",
            (tag_id, scope, scope_key),
        )

    def unassign_tag(self, tag_id: int, scope: TagScope, scope_key: str) -> None:
        """Remove a tag assignment."""
        self._conn_required().execute(
            "DELETE FROM tag_assignments WHERE tag_id=? AND scope=? AND scope_key=?",
            (tag_id, scope, scope_key),
        )

    def list_tags_for(self, scope: TagScope, scope_key: str) -> list[TagRow]:
        """List tags assigned to a scope key."""
        rows = self._conn_required().execute(
            """
            SELECT t.* FROM tags t
            JOIN tag_assignments a ON t.id = a.tag_id
            WHERE a.scope = ? AND a.scope_key = ?
            ORDER BY t.name
            """,
            (scope, scope_key),
        ).fetchall()
        return [
            TagRow(id=int(r["id"]), name=str(r["name"]), color=r["color"]) for r in rows
        ]

    def list_targets_with_tag(self, tag_id: int, scope: TagScope) -> list[str]:
        """List scope keys that have the given tag."""
        rows = self._conn_required().execute(
            "SELECT scope_key FROM tag_assignments WHERE tag_id = ? AND scope = ?",
            (tag_id, scope),
        ).fetchall()
        return [str(r["scope_key"]) for r in rows]

    def add_event_log(self, level: str, category: str, message: str) -> int:
        """Append an event log row."""
        cur = self._conn_required().execute(
            "INSERT INTO event_logs(ts, level, category, message) VALUES(?, ?, ?, ?)",
            (now_jst_iso(), level, category, message),
        )
        log_id = cur.lastrowid
        assert log_id is not None
        return int(log_id)

    def list_event_logs(
        self,
        level: str | None = None,
        category: str | None = None,
        limit: int = 1000,
    ) -> list[EventLogRow]:
        """List event logs with optional filters."""
        query = "SELECT * FROM event_logs WHERE 1=1"
        params: list[object] = []
        if level is not None:
            query += " AND level = ?"
            params.append(level)
        if category is not None:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        rows = self._conn_required().execute(query, params).fetchall()
        return [
            EventLogRow(
                id=int(r["id"]),
                ts=str(r["ts"]),
                level=str(r["level"]),
                category=str(r["category"]),
                message=str(r["message"]),
            )
            for r in rows
        ]

    def purge_old_logs(self, before_iso: str) -> int:
        """Delete logs older than *before_iso* and return the count removed."""
        cur = self._conn_required().execute(
            "DELETE FROM event_logs WHERE ts < ?",
            (before_iso,),
        )
        return int(cur.rowcount)

    def list_missing_publications(
        self,
        start_ym: tuple[int, int],
        end_ym: tuple[int, int],
    ) -> list[str]:
        """Return publish_ym values missing or not complete in range."""
        missing: list[str] = []
        year, month = start_ym
        end_year, end_month = end_ym
        while (year, month) <= (end_year, end_month):
            folder = f"{year}_{month}"
            if not self.is_publication_complete(folder):
                missing.append(folder)
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
        return sorted(missing, key=lambda name: parse_folder_name(name))

    @staticmethod
    def _row_to_file(row: sqlite3.Row) -> FileRow:
        return FileRow(
            id=int(row["id"]),
            publish_ym=str(row["publish_ym"]),
            target_code=str(row["target_code"]),
            display_name=str(row["display_name"]),
            file_path=str(row["file_path"]),
            file_size=int(row["file_size"]),
            sha256=str(row["sha256"]),
            source_url=str(row["source_url"]),
            downloaded_at=str(row["downloaded_at"]),
            status=cast(FileStatus, row["status"]),
        )
