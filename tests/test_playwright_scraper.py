"""Tests for Playwright scraper (mocked)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jatic_library.core.playwright_scraper import JarticScraper, merge_scraped_keys


@pytest.mark.asyncio
async def test_fetch_typeb_links_mocked() -> None:
    mock_page = AsyncMock()
    mock_page.eval_on_selector_all.return_value = [
        {
            "href": "https://www.jartic.or.jp/d/opendata/202605010000/typeB_tokyo.zip",
            "text": "東京都",
        }
    ]
    mock_browser = AsyncMock()
    mock_browser.new_page.return_value = mock_page
    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("playwright.async_api.async_playwright") as mock_pw:
        mock_pw.return_value.__aenter__.return_value = mock_playwright
        scraper = JarticScraper()
        links = await scraper.fetch_typeb_links()

    assert len(links) == 1
    assert links[0].filename_key == "tokyo"


def test_merge_scraped_keys() -> None:
    from jatic_library.core.playwright_scraper import ScrapedLink

    links = [
        ScrapedLink(
            "東京都",
            "https://www.jartic.or.jp/d/opendata/202605010000/typeB_tokyo.zip",
            "tokyo",
        )
    ]
    merged = merge_scraped_keys(links)
    tokyo = next(t for t in merged if t.code == "tokyo")
    assert tokyo.filename_key == "tokyo"
