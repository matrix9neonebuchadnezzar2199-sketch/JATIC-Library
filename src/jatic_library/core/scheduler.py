"""Startup check and download orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from loguru import logger

from jatic_library.constants import DB_PATH, LOG_DIR, TZ_JST
from jatic_library.core.downloader import (
    Downloader,
    DownloadResult,
    ProgressCallback,
    resolve_targets,
)
from jatic_library.core.git_sync import sync_publication_folder
from jatic_library.core.logger import setup_logging
from jatic_library.core.models import CheckResult
from jatic_library.core.notifier import DownloadSummary, Notifier
from jatic_library.core.repository import Repository
from jatic_library.core.url_builder import compute_publish_info
from jatic_library.settings.config import AppConfig
from jatic_library.settings.store import ConfigStore


@dataclass(frozen=True)
class CheckDecision:
    """Whether an automatic check should run."""

    should_run: bool
    reason: str


@dataclass
class CheckOutcome:
    """Result of a check run."""

    publish_ym: str
    new_downloads: int
    skipped: int
    errors: int
    download_result: DownloadResult | None = None


class StartupScheduler:
    """Decide and run publication checks."""

    def __init__(self, config: AppConfig, repo: Repository) -> None:
        self._config = config
        self._repo = repo

    def should_check_now(self, *, force: bool = False) -> CheckDecision:
        """Return whether a check should execute now."""
        if force:
            return CheckDecision(True, "manual or forced check")
        if not self._config.schedule.auto_check_on_startup:
            return CheckDecision(False, "auto_check_on_startup is disabled")
        if self._config.download.save_root is None:
            return CheckDecision(False, "save_root not configured")

        last = self._config.schedule.last_check_at
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=ZoneInfo(TZ_JST))
                interval = timedelta(hours=self._config.schedule.recheck_interval_hours)
                if datetime.now(ZoneInfo(TZ_JST)) - last_dt < interval:
                    return CheckDecision(False, "within recheck interval")
            except ValueError:
                logger.warning("Invalid last_check_at: {}", last)

        info = compute_publish_info(date.today())
        if self._repo.is_publication_complete(info.folder_name):
            return CheckDecision(False, f"publication {info.folder_name} already complete")

        return CheckDecision(True, f"publication {info.folder_name} incomplete or missing")

    async def run_check(
        self,
        *,
        force: bool = False,
        progress_cb: ProgressCallback | None = None,
    ) -> CheckOutcome:
        """Run check and download missing targets when appropriate."""
        decision = self.should_check_now(force=force)
        info = compute_publish_info(date.today())
        notifier = Notifier(self._config.notification)

        if not decision.should_run:
            self._repo.add_check_history("skipped", decision.reason)
            self._touch_last_check()
            return CheckOutcome(
                publish_ym=info.folder_name,
                new_downloads=0,
                skipped=0,
                errors=0,
            )

        notifier.notify_new_publish(info.folder_name)
        targets = resolve_targets(self._config.targets.selected_codes)
        downloader = Downloader(self._config.download, self._repo)
        try:
            result = await downloader.download_publication(
                info,
                targets,
                progress_cb=progress_cb,
            )
        except Exception as exc:
            logger.exception("Check run failed")
            self._repo.add_check_history("error", str(exc))
            notifier.notify_error(str(exc))
            self._touch_last_check()
            return CheckOutcome(
                publish_ym=info.folder_name,
                new_downloads=0,
                skipped=0,
                errors=1,
            )

        notifier.notify_complete(
            DownloadSummary(
                publish_ym=result.publish_ym,
                succeeded=len(result.succeeded),
                skipped=len(result.skipped),
                failed=len(result.failed),
            )
        )
        if result.failed:
            notifier.notify_error(f"{len(result.failed)} region(s) failed")

        if self._config.download.save_root is not None and (
            result.succeeded or result.skipped
        ):
            sync_publication_folder(
                self._config.github,
                self._config.download.save_root,
                result.publish_ym,
            )

        result_label: CheckResult = "new_found" if result.succeeded else "no_update"
        if result.failed:
            result_label = "error"
        self._repo.add_check_history(result_label, decision.reason)
        self._touch_last_check(persist=True)

        return CheckOutcome(
            publish_ym=result.publish_ym,
            new_downloads=len(result.succeeded),
            skipped=len(result.skipped),
            errors=len(result.failed),
            download_result=result,
        )

    def _touch_last_check(self, *, persist: bool = False) -> None:
        now = datetime.now(ZoneInfo(TZ_JST)).isoformat(timespec="seconds")
        self._config.schedule.last_check_at = now
        if persist:
            ConfigStore().save(self._config)


async def run_cli_check(*, force: bool = False) -> CheckOutcome:
    """Load config, init logging/repo, and run scheduler."""
    store = ConfigStore()
    config = store.load()
    setup_logging(LOG_DIR, config.log)
    if config.download.save_root is None:
        raise SystemExit("save_root is not set. Edit %LOCALAPPDATA%\\JATIC-Library\\config.json")

    with Repository(DB_PATH) as repo:
        scheduler = StartupScheduler(config, repo)
        return await scheduler.run_check(force=force)
