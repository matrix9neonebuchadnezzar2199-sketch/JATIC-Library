"""Playwright-based JARTIC open-data scraper."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from loguru import logger

from jatic_library.constants import JARTIC_OPENDATA_PAGE, TARGETS_CACHE_PATH, TZ_JST
from jatic_library.core.targets import (
    TARGETS,
    Target,
    cache_is_fresh_for_folder,
    load_cache_meta,
    save_overrides,
    write_cache_meta,
)

_TYPEB_RE = re.compile(r"typeB_([A-Za-z0-9_]+)\.zip", re.IGNORECASE)
_OPENDATA_DIR_RE = re.compile(r"/d/opendata/(\d+)/", re.IGNORECASE)


@dataclass(frozen=True)
class ScrapedLink:
    """One discovered typeB ZIP link."""

    display_name: str
    url: str
    filename_key: str


class JarticScraper:
    """Scrape rendered open-data page for typeB links."""

    async def fetch_typeb_links(self) -> list[ScrapedLink]:
        """Load the page and extract typeB ZIP anchors."""
        from playwright.async_api import async_playwright

        links: list[ScrapedLink] = []
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(JARTIC_OPENDATA_PAGE, wait_until="networkidle", timeout=120_000)
                raw: list[dict[str, str]] = await page.eval_on_selector_all(
                    "a[href*='typeB_']",
                    """els => els.map(e => ({
                        href: e.href,
                        text: (e.innerText || e.textContent || '').trim()
                    }))""",
                )
                seen: set[str] = set()
                for item in raw:
                    href = item.get("href", "")
                    match = _TYPEB_RE.search(href)
                    if not match:
                        continue
                    key = match.group(1).lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    text = item.get("text") or key
                    links.append(
                        ScrapedLink(
                            display_name=text,
                            url=href,
                            filename_key=key,
                        )
                    )
            finally:
                await browser.close()
        logger.info("Scraped {} typeB links", len(links))
        return links

    async def fetch_publish_label(self) -> str:
        """Return visible publication month label if found."""
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(
                    JARTIC_OPENDATA_PAGE, wait_until="domcontentloaded", timeout=120_000
                )
                text = await page.inner_text("body")
                return text[:500]
            finally:
                await browser.close()


def extract_publish_ym_compact(links: list[ScrapedLink]) -> str:
    """Return the JARTIC open-data directory timestamp from scraped URLs."""
    for link in links:
        match = _OPENDATA_DIR_RE.search(link.url)
        if match:
            return match.group(1)
    raise RuntimeError("Could not determine publish_ym_compact from scraped links")


def merge_scraped_keys(links: list[ScrapedLink]) -> list[Target]:
    """Apply scraped filename_key values onto the built-in master."""
    key_map = {link.filename_key: link for link in links}
    merged: list[Target] = []
    for target in TARGETS:
        scraped = key_map.get(target.filename_key)
        if scraped is None:
            for link in links:
                if (
                    target.display_name in link.display_name
                    or link.display_name in target.display_name
                ):
                    scraped = link
                    break
        if scraped is not None:
            merged.append(
                Target(
                    target.code,
                    target.display_name,
                    target.folder_label,
                    target.region,
                    scraped.filename_key,
                    target.order,
                )
            )
        else:
            merged.append(target)
    return merged


async def scrape_and_save_targets(
    cache_path: Path = TARGETS_CACHE_PATH,
    *,
    scraped_for_folder: str | None = None,
) -> int:
    """Scrape site and persist filename_key overrides. Returns link count."""
    scraper = JarticScraper()
    links = await scraper.fetch_typeb_links()
    if not links:
        raise RuntimeError("No typeB links found on JARTIC open-data page")
    publish_ym_compact = extract_publish_ym_compact(links)
    merged = merge_scraped_keys(links)
    save_overrides(merged, cache_path)
    scraped_at = datetime.now(ZoneInfo(TZ_JST)).isoformat(timespec="seconds")
    write_cache_meta(
        cache_path,
        publish_ym_compact=publish_ym_compact,
        scraped_for_folder=scraped_for_folder,
        scraped_at=scraped_at,
    )
    return len(links)


async def ensure_targets_cache_fresh(
    folder_name: str,
    cache_path: Path = TARGETS_CACHE_PATH,
) -> bool:
    """Scrape when *cache_path* lacks metadata for *folder_name*. Returns True if scraped."""
    meta = load_cache_meta(cache_path)
    if cache_is_fresh_for_folder(meta, folder_name):
        return False
    await scrape_and_save_targets(cache_path, scraped_for_folder=folder_name)
    return True
