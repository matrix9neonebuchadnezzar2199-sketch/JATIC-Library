"""Command-line interface."""

from __future__ import annotations

import argparse
import asyncio
from datetime import date

from loguru import logger

from jatic_library import __app_name__, __version__
from jatic_library.constants import DB_PATH, LOG_DIR
from jatic_library.core.downloader import Downloader, resolve_targets
from jatic_library.core.logger import setup_logging
from jatic_library.core.notifier import DownloadSummary, Notifier
from jatic_library.core.playwright_scraper import scrape_and_save_targets
from jatic_library.core.repository import Repository
from jatic_library.core.scheduler import run_cli_check
from jatic_library.core.url_builder import compute_publish_info
from jatic_library.settings.store import ConfigStore


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="jatic-library", description=__app_name__)
    parser.add_argument("--version", action="version", version=f"{__app_name__} v{__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="Run startup-style update check")
    p_dl = sub.add_parser("download", help="Download current publication ZIPs")
    p_dl.add_argument("-r", "--region", action="append", dest="regions", help="Target code")
    p_dl.add_argument("--all", action="store_true", help="All 51 regions")
    p_dl.add_argument("--force", action="store_true", help="Download even if complete")

    sub.add_parser("scrape", help="Rescan JARTIC site and update targets.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        print(f"Hello from {__app_name__} v{__version__}")
        print("Commands: check, download, scrape  (use -h for help)")
        return 0

    if args.command == "check":
        outcome = asyncio.run(run_cli_check(force=False))
        print(
            f"check: {outcome.publish_ym} "
            f"new={outcome.new_downloads} skip={outcome.skipped} err={outcome.errors}"
        )
        return 1 if outcome.errors else 0

    if args.command == "scrape":
        count = asyncio.run(scrape_and_save_targets())
        print(f"scrape: saved {count} typeB links to targets cache")
        return 0

    if args.command == "download":
        return asyncio.run(_run_download(args))

    parser.error(f"unknown command: {args.command}")
    return 2


async def _run_download(args: argparse.Namespace) -> int:
    store = ConfigStore()
    config = store.load()
    setup_logging(LOG_DIR, config.log)
    if config.download.save_root is None:
        raise SystemExit("save_root is not set in config.json")

    if args.all:
        codes: set[str] = set()
    elif args.regions:
        codes = set(args.regions)
    else:
        raise SystemExit("Specify --all or -r <code> (e.g. -r tokyo)")

    config.targets.selected_codes = codes
    targets = resolve_targets(codes)
    info = compute_publish_info(date.today())

    with Repository(DB_PATH) as repo:
        if not args.force and repo.is_publication_complete(info.folder_name):
            print(f"publication {info.folder_name} already complete (use --force)")
            return 0
        notifier = Notifier(config.notification)
        notifier.notify_new_publish(info.folder_name)
        downloader = Downloader(config.download, repo)
        result = await downloader.download_publication(info, targets)
        notifier.notify_complete(
            DownloadSummary(
                publish_ym=result.publish_ym,
                succeeded=len(result.succeeded),
                skipped=len(result.skipped),
                failed=len(result.failed),
            )
        )
        if result.failed:
            for code, msg in result.failed:
                logger.error("{}: {}", code, msg)
            return 1
        print(
            f"download: ok={len(result.succeeded)} "
            f"skip={len(result.skipped)} fail={len(result.failed)}"
        )
        return 0
