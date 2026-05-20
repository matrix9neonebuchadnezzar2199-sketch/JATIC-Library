"""SQLite row models."""

from dataclasses import dataclass
from typing import Literal

PublicationStatus = Literal["pending", "partial", "complete", "failed"]
FileStatus = Literal["ok", "failed"]
CheckResult = Literal["no_update", "new_found", "error", "skipped"]
TagScope = Literal["publication", "file"]


@dataclass
class PublicationRow:
    """Publication month record."""

    publish_ym: str
    publish_date: str
    detected_at: str
    status: PublicationStatus


@dataclass
class FileRow:
    """Downloaded file record."""

    id: int | None
    publish_ym: str
    target_code: str
    display_name: str
    file_path: str
    file_size: int
    sha256: str
    source_url: str
    downloaded_at: str
    status: FileStatus


@dataclass
class CheckHistoryRow:
    """Startup check history row."""

    id: int | None
    checked_at: str
    result: CheckResult
    detail: str | None


@dataclass
class TagRow:
    """Tag definition."""

    id: int | None
    name: str
    color: str | None


@dataclass
class TagAssignmentRow:
    """Tag assignment."""

    tag_id: int
    scope: TagScope
    scope_key: str


@dataclass
class EventLogRow:
    """Persistent event log row."""

    id: int | None
    ts: str
    level: str
    category: str
    message: str
