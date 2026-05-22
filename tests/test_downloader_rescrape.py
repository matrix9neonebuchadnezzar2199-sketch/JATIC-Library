"""Tests for 404 rescrape helper."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from jatic_library.core.downloader import Downloader
from jatic_library.core.repository import Repository
from jatic_library.settings.config import DownloadSettings


@pytest.mark.asyncio
async def test_maybe_rescrape_runs_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """404 should trigger scrape only once per publication download."""
    db_path = tmp_path / "test.db"
    with Repository(db_path) as repo:
        downloader = Downloader(
            DownloadSettings(save_root=tmp_path / "data"),
            repo,
        )
    calls: list[int] = []

    async def fake_scrape() -> int:
        calls.append(1)
        return 51

    monkeypatch.setattr(
        "jatic_library.core.playwright_scraper.scrape_and_save_targets",
        fake_scrape,
    )

    request = httpx.Request("GET", "https://example.invalid/missing.zip")
    response = httpx.Response(404, request=request)
    exc = httpx.HTTPStatusError("404", request=request, response=response)
    state: dict[str, bool] = {"done": False}

    assert await downloader._maybe_rescrape_on_404(exc, state) is True
    assert await downloader._maybe_rescrape_on_404(exc, state) is False
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_maybe_rescrape_ignores_non_404(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    with Repository(db_path) as repo:
        downloader = Downloader(
            DownloadSettings(save_root=tmp_path / "data"),
            repo,
        )
    request = httpx.Request("GET", "https://example.invalid/server.zip")
    response = httpx.Response(500, request=request)
    exc = httpx.HTTPStatusError("500", request=request, response=response)
    state: dict[str, bool] = {"done": False}
    assert await downloader._maybe_rescrape_on_404(exc, state) is False


@pytest.mark.asyncio
async def test_rescrape_on_404_concurrency_protection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "test.db"
    with Repository(db_path) as repo:
        downloader = Downloader(
            DownloadSettings(save_root=tmp_path / "data"),
            repo,
        )
    mock_scrape = AsyncMock(return_value=51)
    monkeypatch.setattr(
        "jatic_library.core.playwright_scraper.scrape_and_save_targets",
        mock_scrape,
    )
    request = httpx.Request("GET", "https://example.invalid/missing.zip")
    response = httpx.Response(404, request=request)
    exc = httpx.HTTPStatusError("404", request=request, response=response)
    state: dict[str, bool] = {"done": False}

    results = await asyncio.gather(
        *[downloader._maybe_rescrape_on_404(exc, state) for _ in range(5)]
    )

    assert sum(1 for value in results if value) == 1
    assert mock_scrape.await_count == 1


@pytest.mark.asyncio
async def test_rescrape_skipped_for_non_404_without_lock(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    with Repository(db_path) as repo:
        downloader = Downloader(
            DownloadSettings(save_root=tmp_path / "data"),
            repo,
        )
    with patch.object(
        downloader._rescrape_lock,
        "__aenter__",
        new_callable=AsyncMock,
    ) as mock_enter:
        request = httpx.Request("GET", "https://example.invalid/server.zip")
        response = httpx.Response(500, request=request)
        exc = httpx.HTTPStatusError("500", request=request, response=response)
        state: dict[str, bool] = {"done": False}
        assert await downloader._maybe_rescrape_on_404(exc, state) is False
        mock_enter.assert_not_called()
