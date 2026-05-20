"""Integration-style tests for scheduler download flow."""

from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from jatic_library.core.downloader import DownloadResult
from jatic_library.core.repository import Repository
from jatic_library.core.scheduler import StartupScheduler
from jatic_library.core.url_builder import compute_publish_info
from jatic_library.settings.config import AppConfig


@pytest.mark.asyncio
async def test_run_check_skips_download_when_not_needed(tmp_path: Path) -> None:
    config = AppConfig.default()
    config.download.save_root = tmp_path / "data"
    config.schedule.auto_check_on_startup = False
    db = tmp_path / "skip.db"
    with Repository(db) as repo:
        scheduler = StartupScheduler(config, repo)
        with patch.object(
            scheduler,
            "should_check_now",
            return_value=type("D", (), {"should_run": False, "reason": "disabled"})(),
        ):
            outcome = await scheduler.run_check(force=False)
    assert outcome.new_downloads == 0
    assert outcome.errors == 0


@pytest.mark.asyncio
async def test_run_check_downloads_and_syncs_git(tmp_path: Path) -> None:
    config = AppConfig.default()
    save_root = tmp_path / "data"
    config.download.save_root = save_root
    config.github.enabled = True
    config.github.auto_commit = True
    config.github.repo_path = save_root
    info = compute_publish_info(date(2026, 5, 15))
    fake_result = DownloadResult(
        publish_ym=info.folder_name,
        succeeded=["tokyo"],
    )
    db = tmp_path / "flow.db"
    with Repository(db) as repo:
        scheduler = StartupScheduler(config, repo)
        with (
            patch.object(
                scheduler,
                "should_check_now",
                return_value=type("D", (), {"should_run": True, "reason": "test"})(),
            ),
            patch(
                "jatic_library.core.scheduler.Downloader.download_publication",
                new_callable=AsyncMock,
                return_value=fake_result,
            ) as mock_dl,
            patch("jatic_library.core.scheduler.sync_publication_folder") as mock_git,
            patch("jatic_library.core.scheduler.Notifier"),
        ):
            outcome = await scheduler.run_check(force=True)
    mock_dl.assert_awaited_once()
    mock_git.assert_called_once()
    assert outcome.new_downloads == 1
    assert outcome.publish_ym == info.folder_name
