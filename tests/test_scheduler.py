"""Tests for startup scheduler."""

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jatic_library.constants import TZ_JST
from jatic_library.core.repository import Repository
from jatic_library.core.scheduler import StartupScheduler
from jatic_library.core.url_builder import compute_publish_info
from jatic_library.settings.config import AppConfig


def test_should_check_when_save_root_missing(tmp_path: Path) -> None:
    config = AppConfig.default()
    db = tmp_path / "sched.db"
    with Repository(db) as repo:
        decision = StartupScheduler(config, repo).should_check_now()
    assert decision.should_run is False
    assert "save_root" in decision.reason


def test_should_check_when_interval_not_elapsed(tmp_path: Path) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.schedule.last_check_at = datetime.now(ZoneInfo(TZ_JST)).isoformat(timespec="seconds")
    config.schedule.recheck_interval_hours = 24
    db = tmp_path / "sched2.db"
    with Repository(db) as repo:
        decision = StartupScheduler(config, repo).should_check_now()
    assert decision.should_run is False
    assert "interval" in decision.reason


def test_should_check_when_publication_incomplete(tmp_path: Path) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.schedule.last_check_at = None
    db = tmp_path / "sched3.db"
    with Repository(db) as repo:
        decision = StartupScheduler(config, repo).should_check_now()
    info = compute_publish_info(date(2026, 5, 15))
    assert decision.should_run is True
    assert info.folder_name in decision.reason


def test_force_check_overrides_complete(tmp_path: Path) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.schedule.last_check_at = datetime.now(ZoneInfo(TZ_JST)).isoformat(timespec="seconds")
    info = compute_publish_info(date.today())
    db = tmp_path / "sched4.db"
    with Repository(db) as repo:
        repo.upsert_publication(info.folder_name, "2026-05-01", "complete")
        decision = StartupScheduler(config, repo).should_check_now(force=True)
    assert decision.should_run is True
