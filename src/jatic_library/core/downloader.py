"""Async parallel downloader with manifest and SQLite persistence."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import httpx
from loguru import logger

from jatic_library.constants import APP_VERSION, TARGETS_CACHE_PATH
from jatic_library.core.http_client import JarticHttpClient
from jatic_library.core.manifest import Manifest, ManifestFileEntry
from jatic_library.core.models import FileRow, PublicationStatus
from jatic_library.core.publication_postprocess import (
    PostprocessError,
    postprocess_publication_folder,
)
from jatic_library.core.repository import Repository, now_jst_iso
from jatic_library.core.targets import Target, load_overrides
from jatic_library.core.url_builder import PublishInfo, build_zip_url
from jatic_library.settings.config import DownloadSettings


@dataclass
class DownloadProgress:
    """Per-target download progress."""

    target_code: str
    bytes_done: int
    bytes_total: int
    speed_bps: float
    status: str


@dataclass
class DownloadResult:
    """Aggregated download outcome."""

    publish_ym: str
    succeeded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


ProgressCallback = Callable[[DownloadProgress], None]


def publication_status_for_result(
    result: DownloadResult,
    *,
    target_count: int,
) -> PublicationStatus:
    """Derive publication status from a download run.

    ``complete`` only when every requested target succeeded or was skipped.
    """
    if target_count <= 0:
        return "pending"
    if result.failed:
        return "partial"
    finished = len(result.succeeded) + len(result.skipped)
    if finished >= target_count:
        return "complete"
    if finished > 0:
        return "partial"
    return "pending"


class Downloader:
    """Download typeB ZIP files for a publication month."""

    def __init__(
        self,
        settings: DownloadSettings,
        repo: Repository,
    ) -> None:
        self._settings = settings
        self._repo = repo
        self._rescrape_lock = asyncio.Lock()

    async def download_publication(
        self,
        info: PublishInfo,
        targets: list[Target],
        progress_cb: ProgressCallback | None = None,
        *,
        publish_date: str | None = None,
        merge_targets: list[Target] | None = None,
    ) -> DownloadResult:
        """Download all *targets* for *info* into save_root."""
        if self._settings.save_root is None:
            raise ValueError("download.save_root is not configured")
        if not targets:
            raise ValueError("targets list is empty")

        save_root = Path(self._settings.save_root)
        folder = save_root / info.folder_name
        folder.mkdir(parents=True, exist_ok=True)

        pub_date = publish_date or date(info.publish_year, info.publish_month, 1).isoformat()
        self._repo.upsert_publication(info.folder_name, pub_date, "pending")

        manifest = Manifest.load(folder) or Manifest(
            publish_ym=info.folder_name,
            publish_date=pub_date,
            downloaded_at=now_jst_iso(),
            source_dir_url=info.dir_url,
            app_version=APP_VERSION,
        )

        semaphore = asyncio.Semaphore(self._settings.concurrency)
        result = DownloadResult(publish_ym=info.folder_name)
        rescrape_state = {"done": False}

        async with JarticHttpClient(timeout_sec=float(self._settings.timeout_sec)) as http:

            async def run_one(target: Target) -> None:
                async with semaphore:
                    try:
                        status = await self._download_one(
                            http,
                            info,
                            target,
                            folder,
                            manifest,
                            progress_cb,
                            rescrape_state,
                        )
                        if status == "skipped":
                            result.skipped.append(target.code)
                        else:
                            result.succeeded.append(target.code)
                    except Exception as exc:
                        logger.error("Download failed for {}: {}", target.code, exc)
                        result.failed.append((target.code, str(exc)))

            await asyncio.gather(*(run_one(t) for t in targets))

        manifest.downloaded_at = now_jst_iso()
        manifest.save(folder)

        if result.succeeded or result.skipped:
            merge_list = merge_targets if merge_targets is not None else targets

            def _postprocess_progress(code: str, done: int, total: int, status: str) -> None:
                if progress_cb is None:
                    return
                progress_cb(
                    DownloadProgress(
                        target_code=code,
                        bytes_done=done,
                        bytes_total=max(total, 1),
                        speed_bps=0.0,
                        status=status,
                    )
                )

            try:
                postprocess_publication_folder(folder, merge_list, _postprocess_progress)
            except PostprocessError as exc:
                logger.warning("Post-download merge/extract failed: {}", exc)

        pub_status = publication_status_for_result(result, target_count=len(targets))
        if result.succeeded or result.skipped or result.failed:
            self._repo.upsert_publication(info.folder_name, pub_date, pub_status)
        return result

    async def _download_one(
        self,
        http: JarticHttpClient,
        info: PublishInfo,
        target: Target,
        folder: Path,
        manifest: Manifest,
        progress_cb: ProgressCallback | None,
        rescrape_state: dict[str, bool],
    ) -> str:
        """Download a single target. Returns 'skipped' or 'done'."""
        url = build_zip_url(info, target.filename_key)
        dest = folder / f"{target.folder_label}.zip"
        existing = manifest.file_entry(target.code)

        if dest.is_file() and existing and existing.sha256:
            current_hash = _sha256_file(dest)
            if current_hash == existing.sha256:
                if progress_cb:
                    progress_cb(
                        DownloadProgress(
                            target_code=target.code,
                            bytes_done=dest.stat().st_size,
                            bytes_total=dest.stat().st_size,
                            speed_bps=0.0,
                            status="done",
                        )
                    )
                return "skipped"

        last_error: Exception | None = None
        for attempt in range(self._settings.retry + 1):
            try:
                await http.head(url)
                digest, size = await self._stream_to_file(http, url, dest, target, progress_cb)
                entry = ManifestFileEntry(
                    target_code=target.code,
                    display_name=target.display_name,
                    filename=dest.name,
                    source_url=url,
                    size=size,
                    sha256=digest,
                    downloaded_at=now_jst_iso(),
                )
                manifest.upsert_file(entry)
                self._repo.upsert_file(
                    FileRow(
                        id=None,
                        publish_ym=info.folder_name,
                        target_code=target.code,
                        display_name=target.display_name,
                        file_path=str(dest.resolve()),
                        file_size=size,
                        sha256=digest,
                        source_url=url,
                        downloaded_at=entry.downloaded_at,
                        status="ok",
                    )
                )
                return "done"
            except Exception as exc:
                last_error = exc
                if dest.exists():
                    dest.unlink(missing_ok=True)
                if await self._maybe_rescrape_on_404(exc, rescrape_state):
                    target = self._refresh_target(target)
                    url = build_zip_url(info, target.filename_key)
                    continue
                if attempt < self._settings.retry:
                    await asyncio.sleep(2**attempt)
        assert last_error is not None
        raise last_error

    async def _maybe_rescrape_on_404(self, exc: Exception, rescrape_state: dict[str, bool]) -> bool:
        status_code = None
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code
        if status_code != httpx.codes.NOT_FOUND:
            return False
        async with self._rescrape_lock:
            if rescrape_state.get("done"):
                return False
            logger.warning("404 for ZIP URL, running one-time Playwright rescrape")
            from jatic_library.core.playwright_scraper import scrape_and_save_targets

            await scrape_and_save_targets()
            rescrape_state["done"] = True
            return True

    def _refresh_target(self, target: Target) -> Target:
        master = load_overrides(TARGETS_CACHE_PATH)
        for item in master:
            if item.code == target.code:
                return item
        return target

    async def _stream_to_file(
        self,
        http: JarticHttpClient,
        url: str,
        dest: Path,
        target: Target,
        progress_cb: ProgressCallback | None,
    ) -> tuple[str, int]:
        """Stream URL to *dest* and return sha256 and size."""
        tmp = dest.with_suffix(dest.suffix + ".part")
        hasher = hashlib.sha256()
        total = 0
        response = await http.get_stream(url)
        try:
            content_length = int(response.headers.get("content-length", 0))
            with tmp.open("wb") as handle:
                async for chunk in response.aiter_bytes(chunk_size=1024 * 256):
                    if self._settings.rate_limit_bps:
                        await asyncio.sleep(len(chunk) / self._settings.rate_limit_bps)
                    handle.write(chunk)
                    hasher.update(chunk)
                    total += len(chunk)
                    if progress_cb:
                        progress_cb(
                            DownloadProgress(
                                target_code=target.code,
                                bytes_done=total,
                                bytes_total=content_length or total,
                                speed_bps=0.0,
                                status="running",
                            )
                        )
        finally:
            await response.aclose()
        tmp.replace(dest)
        return hasher.hexdigest(), total


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_targets(selected_codes: set[str]) -> list[Target]:
    """Return target list from selection; empty means all regions."""
    master = load_overrides(TARGETS_CACHE_PATH)
    if not selected_codes:
        return list(master)
    return [t for t in master if t.code in selected_codes]
