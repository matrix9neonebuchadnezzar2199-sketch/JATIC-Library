"""Lightweight HTML scraper (no JavaScript execution).

The JARTIC open-data list is rendered client-side; this module is a stub
for future static fallbacks. Use ``playwright_scraper`` for production scans.
"""

from loguru import logger

from jatic_library.constants import JARTIC_OPENDATA_PAGE


def fetch_static_html() -> str:
    """Fetch the open-data page HTML without executing JavaScript."""
    import httpx

    response = httpx.get(JARTIC_OPENDATA_PAGE, timeout=60.0, follow_redirects=True)
    response.raise_for_status()
    logger.debug("Fetched {} bytes of static HTML", len(response.text))
    return response.text
